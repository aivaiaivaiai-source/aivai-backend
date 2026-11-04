"""Listing description mode preference (Substage 3C-2)."""

from __future__ import annotations

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.exceptions import AppException, EntityNotFoundError
from app.models.listing_description_mode_enums import ListingDescriptionMode
from app.repositories.listing_repository import ListingRepository
from app.schemas.listing_description_mode import (
    ListingDescriptionModeRead,
    ListingDescriptionModeUpsertRequest,
)

logger = logging.getLogger(__name__)


class ListingDescriptionModeService:
    def __init__(self, session: AsyncSession, settings: Settings | None = None) -> None:
        self._session = session
        self._settings = settings or get_settings()
        self._listings = ListingRepository(session)

    @property
    def feature_enabled(self) -> bool:
        return bool(self._settings.MEDIA_DESCRIPTION_MODE_ENABLED)

    async def get_mode(
        self,
        listing_id: int,
        *,
        actor_user_id: int,
    ) -> ListingDescriptionModeRead:
        listing = await self._listings.get_by_id(listing_id)
        if listing is None:
            raise EntityNotFoundError("Listing", entity_id=listing_id)
        if listing.owner_id != actor_user_id:
            raise AppException("Not allowed.", status_code=403)
        mode = listing.description_mode
        return ListingDescriptionModeRead(
            listing_id=listing_id,
            description_mode=mode.value if mode is not None else None,
            feature_enabled=self.feature_enabled,
        )

    async def upsert_mode(
        self,
        listing_id: int,
        *,
        actor_user_id: int,
        payload: ListingDescriptionModeUpsertRequest,
    ) -> ListingDescriptionModeRead:
        if not self.feature_enabled:
            raise AppException("Description mode is disabled.", status_code=404)

        listing = await self._listings.get_by_id(listing_id)
        if listing is None:
            raise EntityNotFoundError("Listing", entity_id=listing_id)
        if listing.owner_id != actor_user_id:
            raise AppException("Not allowed.", status_code=403)

        raw = payload.description_mode.strip().lower()
        try:
            mode = ListingDescriptionMode(raw)
        except ValueError as exc:
            raise AppException(
                "Invalid description_mode; allowed: ai_assisted, manual.",
                status_code=400,
            ) from exc

        listing.description_mode = mode
        await self._session.flush()
        logger.info(
            "listing_description_mode_set listing_id=%s mode=%s",
            listing_id,
            mode.value,
        )
        return ListingDescriptionModeRead(
            listing_id=listing_id,
            description_mode=mode.value,
            feature_enabled=True,
        )

    async def clear_mode(
        self,
        listing_id: int,
        *,
        actor_user_id: int,
    ) -> ListingDescriptionModeRead:
        if not self.feature_enabled:
            raise AppException("Description mode is disabled.", status_code=404)

        listing = await self._listings.get_by_id(listing_id)
        if listing is None:
            raise EntityNotFoundError("Listing", entity_id=listing_id)
        if listing.owner_id != actor_user_id:
            raise AppException("Not allowed.", status_code=403)

        listing.description_mode = None
        await self._session.flush()
        logger.info("listing_description_mode_cleared listing_id=%s", listing_id)
        return ListingDescriptionModeRead(
            listing_id=listing_id,
            description_mode=None,
            feature_enabled=True,
        )
