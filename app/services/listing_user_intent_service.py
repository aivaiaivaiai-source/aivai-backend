"""Listing user intent service — storage + revision only (no resolver)."""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.constants import MAX_USER_INTENT_TEXT_LENGTH
from app.core.exceptions import AppException, EntityNotFoundError, OwnershipError
from app.models.enums import ListingStatus
from app.models.listing import Listing
from app.models.listing_user_intent_enums import ListingUserIntentStatus
from app.repositories.listing_repository import ListingRepository
from app.repositories.listing_user_intent_repository import ListingUserIntentRepository
from app.schemas.listing_user_intent import ListingUserIntentRead, ListingUserIntentUpsertRequest
from app.user_intent.fingerprint import intent_fingerprint, normalize_intent_text

logger = logging.getLogger(__name__)


class ListingUserIntentService:
    def __init__(
        self,
        session: AsyncSession,
        listing_repository: ListingRepository,
        intent_repository: ListingUserIntentRepository,
        settings: Settings | None = None,
    ) -> None:
        self._session = session
        self._listings = listing_repository
        self._intents = intent_repository
        self._settings = settings or get_settings()

    @property
    def feature_enabled(self) -> bool:
        return bool(self._settings.MEDIA_USER_INTENT_ENABLED)

    @staticmethod
    def _ensure_owner(listing: Listing, actor_user_id: int) -> None:
        if listing.owner_id is None or listing.owner_id != actor_user_id:
            raise OwnershipError("You cannot modify another user's listing.")

    @staticmethod
    def _ensure_draft(listing: Listing) -> None:
        if listing.status != ListingStatus.draft:
            raise AppException(
                "User intent can only be updated on draft listings.",
                status_code=400,
            )

    def _to_read(
        self,
        listing_id: int,
        row: object | None,
    ) -> ListingUserIntentRead:
        if row is None:
            return ListingUserIntentRead(
                listing_id=listing_id,
                raw_intent_text=None,
                intent_status=ListingUserIntentStatus.missing.value,
                intent_fingerprint="",
                intent_version=0,
                feature_enabled=self.feature_enabled,
                updated_at=None,
            )
        return ListingUserIntentRead(
            listing_id=listing_id,
            raw_intent_text=getattr(row, "raw_intent_text", None),
            intent_status=getattr(row, "intent_status").value,
            intent_fingerprint=getattr(row, "intent_fingerprint", "") or "",
            intent_version=int(getattr(row, "intent_version", 0) or 0),
            feature_enabled=self.feature_enabled,
            updated_at=getattr(row, "updated_at", None),
        )

    async def get_intent(
        self,
        listing_id: int,
        *,
        actor_user_id: int,
    ) -> ListingUserIntentRead:
        listing = await self._listings.get_by_id(listing_id)
        if listing is None:
            raise EntityNotFoundError("Listing", entity_id=listing_id)
        self._ensure_owner(listing, actor_user_id)
        row = await self._intents.get_by_listing_id(listing_id)
        return self._to_read(listing_id, row)

    async def upsert_intent(
        self,
        listing_id: int,
        *,
        actor_user_id: int,
        payload: ListingUserIntentUpsertRequest,
    ) -> ListingUserIntentRead:
        if not self.feature_enabled:
            raise AppException("User intent feature is disabled.", status_code=404)

        listing = await self._listings.get_by_id(listing_id)
        if listing is None:
            raise EntityNotFoundError("Listing", entity_id=listing_id)
        self._ensure_owner(listing, actor_user_id)
        self._ensure_draft(listing)

        text = normalize_intent_text(payload.raw_intent_text)
        if not text:
            raise AppException("Intent text cannot be empty.", status_code=400)
        if len(text) > MAX_USER_INTENT_TEXT_LENGTH:
            raise AppException(
                f"Intent text exceeds {MAX_USER_INTENT_TEXT_LENGTH} characters.",
                status_code=400,
            )

        fp = intent_fingerprint(text)
        existing = await self._intents.get_by_listing_id(listing_id)

        if existing is None:
            row = await self._intents.create(
                listing_id=listing_id,
                raw_intent_text=text,
                intent_status=ListingUserIntentStatus.provided,
                intent_fingerprint=fp,
                intent_version=1,
            )
            logger.info(
                "listing_user_intent_created listing_id=%s version=1 fp_prefix=%s",
                listing_id,
                fp[:8],
            )
        elif existing.intent_fingerprint == fp:
            return self._to_read(listing_id, existing)
        else:
            existing.raw_intent_text = text
            existing.intent_status = ListingUserIntentStatus.provided
            existing.intent_fingerprint = fp
            existing.intent_version = int(existing.intent_version or 0) + 1
            existing.updated_at = datetime.now(UTC)
            row = await self._intents.save(existing)
            logger.info(
                "listing_user_intent_updated listing_id=%s version=%s fp_prefix=%s",
                listing_id,
                row.intent_version,
                fp[:8],
            )

        await self._session.commit()
        return self._to_read(listing_id, row)

    async def clear_intent(
        self,
        listing_id: int,
        *,
        actor_user_id: int,
    ) -> ListingUserIntentRead:
        if not self.feature_enabled:
            raise AppException("User intent feature is disabled.", status_code=404)

        listing = await self._listings.get_by_id(listing_id)
        if listing is None:
            raise EntityNotFoundError("Listing", entity_id=listing_id)
        self._ensure_owner(listing, actor_user_id)
        self._ensure_draft(listing)

        await self._intents.delete_by_listing_id(listing_id)
        await self._session.commit()
        logger.info("listing_user_intent_cleared listing_id=%s", listing_id)
        return self._to_read(listing_id, None)
