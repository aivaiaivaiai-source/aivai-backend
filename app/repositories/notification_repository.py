from __future__ import annotations

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.notifications import NOTIFICATION_TYPE_SAVED_SEARCH_MATCH
from app.models.notification import Notification
from app.repositories.base import BaseRepository


class NotificationRepository(BaseRepository[Notification]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Notification)

    async def exists_saved_search_match_for(
        self,
        *,
        user_id: int,
        listing_id: int,
        saved_search_id: int,
    ) -> bool:
        stmt = (
            select(Notification.id)
            .where(
                Notification.user_id == user_id,
                Notification.type == NOTIFICATION_TYPE_SAVED_SEARCH_MATCH,
                Notification.payload["listing_id"].astext == str(listing_id),
                Notification.payload["saved_search_id"].astext == str(saved_search_id),
            )
            .limit(1)
        )
        row = await self._session.execute(stmt)
        return row.scalar_one_or_none() is not None

    async def list_for_user(
        self,
        user_id: int,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Notification]:
        stmt = (
            select(Notification)
            .where(Notification.user_id == user_id)
            .order_by(Notification.id.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def mark_read_for_user(self, notification_id: int, user_id: int) -> Notification | None:
        obj = await self._find_owned(notification_id, user_id)
        if obj is None:
            return None
        obj.is_read = True
        await self._session.flush()
        await self._session.refresh(obj)
        return obj

    async def mark_all_read_for_user(self, user_id: int) -> int:
        stmt = (
            update(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.is_read.is_(False),
            )
            .values(is_read=True)
        )
        result = await self._session.execute(stmt)
        return int(result.rowcount or 0)

    async def _find_owned(self, notification_id: int, user_id: int) -> Notification | None:
        stmt = select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == user_id,
        )
        row = await self._session.execute(stmt)
        return row.scalar_one_or_none()
