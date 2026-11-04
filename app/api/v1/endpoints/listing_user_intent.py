"""Listing user intent endpoints (Substage 3C-1)."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, get_listing_user_intent_service
from app.schemas.listing_user_intent import (
    ListingUserIntentRead,
    ListingUserIntentUpsertRequest,
)
from app.schemas.user import UserRead
from app.services.listing_user_intent_service import ListingUserIntentService

router = APIRouter()


@router.get(
    "/{listing_id}/user-intent",
    response_model=ListingUserIntentRead,
)
async def get_listing_user_intent(
    listing_id: int,
    user: UserRead = Depends(get_current_user),
    service: ListingUserIntentService = Depends(get_listing_user_intent_service),
) -> ListingUserIntentRead:
    return await service.get_intent(listing_id, actor_user_id=user.id)


@router.put(
    "/{listing_id}/user-intent",
    response_model=ListingUserIntentRead,
)
async def upsert_listing_user_intent(
    listing_id: int,
    body: ListingUserIntentUpsertRequest,
    user: UserRead = Depends(get_current_user),
    service: ListingUserIntentService = Depends(get_listing_user_intent_service),
) -> ListingUserIntentRead:
    """Confirm raw user intent text — does not assign category or call external AI."""
    return await service.upsert_intent(
        listing_id,
        actor_user_id=user.id,
        payload=body,
    )


@router.delete(
    "/{listing_id}/user-intent",
    response_model=ListingUserIntentRead,
)
async def clear_listing_user_intent(
    listing_id: int,
    user: UserRead = Depends(get_current_user),
    service: ListingUserIntentService = Depends(get_listing_user_intent_service),
) -> ListingUserIntentRead:
    """Revert user intent to unset (draft rollback)."""
    return await service.clear_intent(listing_id, actor_user_id=user.id)
