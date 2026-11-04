"""Listing description mode endpoints (Substage 3C-2)."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, get_listing_description_mode_service
from app.schemas.listing_description_mode import (
    ListingDescriptionModeRead,
    ListingDescriptionModeUpsertRequest,
)
from app.schemas.user import UserRead
from app.services.listing_description_mode_service import ListingDescriptionModeService

router = APIRouter()


@router.get(
    "/{listing_id}/description-mode",
    response_model=ListingDescriptionModeRead,
)
async def get_description_mode(
    listing_id: int,
    user: UserRead = Depends(get_current_user),
    service: ListingDescriptionModeService = Depends(get_listing_description_mode_service),
) -> ListingDescriptionModeRead:
    return await service.get_mode(listing_id, actor_user_id=user.id)


@router.put(
    "/{listing_id}/description-mode",
    response_model=ListingDescriptionModeRead,
)
async def upsert_description_mode(
    listing_id: int,
    body: ListingDescriptionModeUpsertRequest,
    user: UserRead = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    service: ListingDescriptionModeService = Depends(get_listing_description_mode_service),
) -> ListingDescriptionModeRead:
    result = await service.upsert_mode(
        listing_id,
        actor_user_id=user.id,
        payload=body,
    )
    await session.commit()
    return result


@router.delete(
    "/{listing_id}/description-mode",
    response_model=ListingDescriptionModeRead,
)
async def clear_description_mode(
    listing_id: int,
    user: UserRead = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    service: ListingDescriptionModeService = Depends(get_listing_description_mode_service),
) -> ListingDescriptionModeRead:
    """Revert description mode to unset (draft rollback)."""
    result = await service.clear_mode(listing_id, actor_user_id=user.id)
    await session.commit()
    return result
