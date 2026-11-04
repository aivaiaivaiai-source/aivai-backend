"""Category Resolver endpoints (Substage 3C-3 shadow + 3C-4 draft enrichment)."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_category_resolver_service, get_current_user
from app.schemas.category_resolver import CategoryResolverRead, CategoryResolverResolveResponse
from app.schemas.user import UserRead
from app.services.category_resolver_service import CategoryResolverService

router = APIRouter()


@router.get(
    "/{listing_id}/category-resolver",
    response_model=CategoryResolverRead,
)
async def get_category_resolver_result(
    listing_id: int,
    user: UserRead = Depends(get_current_user),
    service: CategoryResolverService = Depends(get_category_resolver_service),
) -> CategoryResolverRead:
    """Latest resolver result; includes draft enrichment state when enabled."""
    return await service.get_result(listing_id, actor_user_id=user.id)


@router.post(
    "/{listing_id}/category-resolver/resolve",
    response_model=CategoryResolverResolveResponse,
)
async def resolve_category_suggestion(
    listing_id: int,
    user: UserRead = Depends(get_current_user),
    service: CategoryResolverService = Depends(get_category_resolver_service),
) -> CategoryResolverResolveResponse:
    """Run hybrid resolver; applies draft enrichment when flag enabled."""
    return await service.resolve_for_listing(listing_id, actor_user_id=user.id)


@router.post(
    "/{listing_id}/category-resolver/enrich-draft",
    response_model=CategoryResolverRead,
)
async def enrich_draft_category(
    listing_id: int,
    user: UserRead = Depends(get_current_user),
    service: CategoryResolverService = Depends(get_category_resolver_service),
) -> CategoryResolverRead:
    """Resolve (if needed) and apply draft-safe category enrichment."""
    return await service.enrich_draft_from_latest(listing_id, actor_user_id=user.id)
