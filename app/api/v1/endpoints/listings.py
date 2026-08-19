from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, get_listing_service, get_promotion_service
from app.core.constants import MAX_LIMIT
from app.core.rate_limit import LISTING_CREATE_LIMITER
from app.models.enums import Currency, ListingStatus
from app.repositories.category_repository import CategoryRepository
from app.schemas.listing import (
    ListingCreate,
    ListingFeedPage,
    ListingRead,
    ListingStatusUpdate,
    ListingUpdate,
    PromotionActivate,
    PromotionStopRead,
)
from app.schemas.user import UserRead
from app.services.listing_service import ListingService
from app.services.promotion_service import PromotionService

router = APIRouter()

# Mobile «Продажа авто» + legacy intelligence slug.
_CAR_SALE_SLUGS = ("transport-car-sale", "transport-cars")


async def _enforce_listing_create_rate_limit(
    user: UserRead = Depends(get_current_user),
) -> None:
    await LISTING_CREATE_LIMITER.hit(f"listing_create:{user.id}")


async def _resolve_category_ids(
    *,
    category_id: int | None,
    category_slug: str | None,
    session: AsyncSession,
) -> list[int] | None:
    if category_id is not None:
        return [category_id]
    if not category_slug:
        return None
    categories = CategoryRepository(session)
    slug = category_slug.strip()
    slugs = list(_CAR_SALE_SLUGS) if slug in _CAR_SALE_SLUGS else [slug]
    ids: list[int] = []
    for s in slugs:
        row = await categories.get_by_slug(s)
        if row is not None:
            ids.append(row.id)
    return ids or None


@router.get("", response_model=ListingFeedPage)
async def get_feed(
    service: ListingService = Depends(get_listing_service),
    session: AsyncSession = Depends(get_db),
    q: str | None = Query(default=None),
    category_id: int | None = Query(default=None),
    category_slug: str | None = Query(default=None),
    city: str | None = Query(default=None),
    brand: str | None = Query(default=None),
    model: str | None = Query(default=None),
    year_min: int | None = Query(default=None, ge=1900, le=2100),
    year_max: int | None = Query(default=None, ge=1900, le=2100),
    steering: str | None = Query(default=None),
    engine_volume: str | None = Query(default=None),
    fuel: str | None = Query(default=None),
    transmission: str | None = Query(default=None),
    min_price: Decimal | None = Query(default=None, ge=0),
    max_price: Decimal | None = Query(default=None, ge=0),
    currency: Currency | None = Query(default=None),
    status: ListingStatus | None = Query(
        default=None,
        description=(
            "Public home/search feed. Omitted = active only. "
            "draft is never listed."
        ),
    ),
    limit: int = Query(default=20, ge=1, le=MAX_LIMIT),
    offset: int = Query(default=0, ge=0),
) -> ListingFeedPage:
    category_ids = await _resolve_category_ids(
        category_id=category_id,
        category_slug=category_slug,
        session=session,
    )
    return await service.get_feed(
        q=q,
        category_id=None if category_ids else category_id,
        category_ids=category_ids,
        city=city,
        brand=brand,
        model=model,
        year_min=year_min,
        year_max=year_max,
        steering=steering,
        engine_volume=engine_volume,
        fuel=fuel,
        transmission=transmission,
        min_price=min_price,
        max_price=max_price,
        currency=currency,
        status=status,
        limit=limit,
        offset=offset,
    )


@router.post("", response_model=ListingRead, status_code=201)
async def create_listing(
    body: ListingCreate,
    service: ListingService = Depends(get_listing_service),
    user: UserRead = Depends(get_current_user),
    _: None = Depends(_enforce_listing_create_rate_limit),
) -> ListingRead:
    # Public create is always a draft. Activation (and later moderation)
    # goes through PATCH /listings/{id}/status after photos are uploaded.
    draft = body.model_copy(update={"status": ListingStatus.draft})
    return await service.create_listing(
        draft,
        owner_id=user.id,
        known_fields=draft.fields or None,
    )


@router.get("/mine", response_model=ListingFeedPage)
async def get_my_listings(
    service: ListingService = Depends(get_listing_service),
    user: UserRead = Depends(get_current_user),
    status: ListingStatus | None = Query(
        default=None,
        description="Optional filter. Omitted = active + draft + sold.",
    ),
    limit: int = Query(default=40, ge=1, le=MAX_LIMIT),
    offset: int = Query(default=0, ge=0),
) -> ListingFeedPage:
    return await service.get_mine(
        owner_id=user.id,
        status=status,
        limit=limit,
        offset=offset,
    )


@router.get("/{listing_id}", response_model=ListingRead)
async def read_listing(
    listing_id: int,
    service: ListingService = Depends(get_listing_service),
) -> ListingRead:
    return await service.get_listing(listing_id)


@router.patch("/{listing_id}", response_model=ListingRead)
async def patch_listing(
    listing_id: int,
    body: ListingUpdate,
    service: ListingService = Depends(get_listing_service),
    user: UserRead = Depends(get_current_user),
) -> ListingRead:
    return await service.update_listing(listing_id, actor_user_id=user.id, data=body)


@router.delete("/{listing_id}", status_code=204)
async def delete_listing(
    listing_id: int,
    service: ListingService = Depends(get_listing_service),
    user: UserRead = Depends(get_current_user),
) -> None:
    await service.delete_listing(listing_id, actor_user_id=user.id)


@router.patch("/{listing_id}/status", response_model=ListingRead)
async def patch_listing_status(
    listing_id: int,
    body: ListingStatusUpdate,
    service: ListingService = Depends(get_listing_service),
    user: UserRead = Depends(get_current_user),
) -> ListingRead:
    return await service.change_status(
        listing_id,
        actor_user_id=user.id,
        payload=body,
    )


@router.post("/{listing_id}/promotion", response_model=ListingRead)
async def activate_promotion(
    listing_id: int,
    body: PromotionActivate,
    service: PromotionService = Depends(get_promotion_service),
    user: UserRead = Depends(get_current_user),
) -> ListingRead:
    return await service.activate(
        listing_id,
        actor_user_id=user.id,
        daily_rate=body.daily_rate,
        days=body.days,
    )


@router.post("/{listing_id}/promotion/stop", response_model=PromotionStopRead)
async def stop_promotion(
    listing_id: int,
    service: PromotionService = Depends(get_promotion_service),
    user: UserRead = Depends(get_current_user),
) -> PromotionStopRead:
    return await service.stop(listing_id, actor_user_id=user.id)
