from decimal import Decimal

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_user, get_listing_service
from app.core.constants import MAX_LIMIT
from app.models.enums import Currency, ListingStatus
from app.schemas.listing import (
    ListingCreate,
    ListingRead,
    ListingStatusUpdate,
    ListingUpdate,
)
from app.schemas.user import UserRead
from app.services.listing_service import ListingService

router = APIRouter()


@router.get("", response_model=list[ListingRead])
async def get_feed(
    service: ListingService = Depends(get_listing_service),
    q: str | None = Query(default=None),
    category_id: int | None = Query(default=None),
    min_price: Decimal | None = Query(default=None, ge=0),
    max_price: Decimal | None = Query(default=None, ge=0),
    currency: Currency | None = Query(default=None),
    status: ListingStatus | None = Query(
        default=None,
        description=(
            "When omitted, only active listings are returned. Pass a status to filter."
        ),
    ),
    limit: int = Query(default=20, ge=1, le=MAX_LIMIT),
    offset: int = Query(default=0, ge=0),
) -> list[ListingRead]:
    return await service.get_feed(
        q=q,
        category_id=category_id,
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
) -> ListingRead:
    return await service.create_listing(body, owner_id=user.id)


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
