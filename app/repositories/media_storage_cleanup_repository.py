from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.media_storage_cleanup import MediaStorageCleanup, MediaStorageCleanupStatus
from app.repositories.base import BaseRepository


class MediaStorageCleanupRepository(BaseRepository[MediaStorageCleanup]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, MediaStorageCleanup)

    async def enqueue(
        self,
        *,
        storage_key: str,
        media_id: int | None,
        reason: str,
    ) -> MediaStorageCleanup:
        existing = await self._find_pending(storage_key)
        if existing is not None:
            return existing
        row = MediaStorageCleanup(
            storage_key=storage_key,
            media_id=media_id,
            reason=reason,
            status=MediaStorageCleanupStatus.pending,
        )
        return await self.create(row)

    async def _find_pending(self, storage_key: str) -> MediaStorageCleanup | None:
        stmt = (
            select(MediaStorageCleanup)
            .where(
                MediaStorageCleanup.storage_key == storage_key,
                MediaStorageCleanup.status == MediaStorageCleanupStatus.pending,
            )
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_pending(self, *, limit: int) -> list[MediaStorageCleanup]:
        stmt = (
            select(MediaStorageCleanup)
            .where(MediaStorageCleanup.status == MediaStorageCleanupStatus.pending)
            .order_by(MediaStorageCleanup.id)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def mark_done(self, cleanup_id: int) -> None:
        stmt = (
            update(MediaStorageCleanup)
            .where(MediaStorageCleanup.id == cleanup_id)
            .values(status=MediaStorageCleanupStatus.done, last_error=None)
        )
        await self._session.execute(stmt)

    async def mark_failed(self, cleanup_id: int, *, error: str, max_attempts: int) -> None:
        row = await self.get_by_id(cleanup_id)
        if row is None:
            return
        attempts = row.attempt_count + 1
        status = (
            MediaStorageCleanupStatus.dead
            if attempts >= max_attempts
            else MediaStorageCleanupStatus.pending
        )
        stmt = (
            update(MediaStorageCleanup)
            .where(MediaStorageCleanup.id == cleanup_id)
            .values(
                attempt_count=attempts,
                last_error=error[:512],
                status=status,
            )
        )
        await self._session.execute(stmt)
