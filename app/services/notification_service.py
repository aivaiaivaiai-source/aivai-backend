from __future__ import annotations

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import EntityNotFoundError, TransactionFailedError
from app.core.notifications import NOTIFICATION_TYPE_SAVED_SEARCH_MATCH
from app.core.pagination import clamp_limit
from app.models.enums import ListingStatus
from app.models.listing import Listing
from app.models.notification import Notification as NotificationRow
from app.repositories.notification_repository import NotificationRepository
from app.repositories.saved_search_repository import SavedSearchRepository
from app.schemas.notification import NotificationRead


class NotificationService:
    def __init__(
        self,
        session: AsyncSession,
        notifications: NotificationRepository,
        saved_searches: SavedSearchRepository | None = None,
    ) -> None:
        self._session = session
        self._notifications = notifications
        self._saved_searches = saved_searches

    async def list_for_user(
        self,
        user_id: int,
        limit: int = 100,
        offset: int = 0,
    ) -> list[NotificationRead]:
        limit = clamp_limit(limit)
        rows = await self._notifications.list_for_user(
            user_id,
            limit=limit,
            offset=offset,
        )
        return [NotificationRead.model_validate(r) for r in rows]

    async def mark_read(self, notification_id: int, user_id: int) -> NotificationRead:
        row = await self._notifications.mark_read_for_user(notification_id, user_id)
        if row is None:
            raise EntityNotFoundError("Notification", entity_id=notification_id)
        try:
            await self._session.commit()
        except Exception as exc:
            await self._session.rollback()
            raise TransactionFailedError(
                "Failed to mark notification read; transaction rolled back.",
            ) from exc
        return NotificationRead.model_validate(row)

    async def mark_read_many(self, user_id: int, ids: list[int]) -> int:
        updated = 0
        try:
            for nid in ids:
                row = await self._notifications.mark_read_for_user(nid, user_id)
                if row is not None:
                    updated += 1
            await self._session.commit()
        except Exception as exc:
            await self._session.rollback()
            raise TransactionFailedError(
                "Failed to mark notifications read; transaction rolled back.",
            ) from exc
        return updated

    async def mark_all_read(self, user_id: int) -> int:
        try:
            n = await self._notifications.mark_all_read_for_user(user_id)
            await self._session.commit()
        except Exception as exc:
            await self._session.rollback()
            raise TransactionFailedError(
                "Failed to mark all notifications read; transaction rolled back.",
            ) from exc
        return n

    async def emit_saved_search_alerts_for_listing(self, listing: Listing) -> None:
        if self._saved_searches is None:
            return
        if listing.owner_id is None or listing.status != ListingStatus.active:
            return

        matches = await self._saved_searches.find_matching_for_listing(listing)

        payload_base = {
            "listing_id": str(listing.id),
        }
        for ss in matches:
            dup = await self._notifications.exists_saved_search_match_for(
                user_id=ss.user_id,
                listing_id=listing.id,
                saved_search_id=ss.id,
            )
            if dup:
                continue
            payload = dict(payload_base)
            payload["saved_search_id"] = str(ss.id)

            notification = NotificationRow(
                user_id=ss.user_id,
                title="New listing matching your saved search",
                body=listing.title,
                type=NOTIFICATION_TYPE_SAVED_SEARCH_MATCH,
                payload=payload,
                is_read=False,
            )

            try:
                async with self._session.begin_nested():
                    await self._notifications.create(notification)
            except IntegrityError:
                continue
