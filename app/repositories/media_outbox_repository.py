from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.media_outbox import MediaOutbox, outbox_dedupe_key
from app.models.media_job_enums import MediaOutboxStatus
from app.repositories.base import BaseRepository


class MediaOutboxRepository(BaseRepository[MediaOutbox]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, MediaOutbox)

    async def has_pending_for_job(self, job_id: int) -> bool:
        stmt = (
            select(MediaOutbox.id)
            .where(
                MediaOutbox.job_id == job_id,
                MediaOutbox.status == MediaOutboxStatus.pending,
            )
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def dedupe_key_exists(self, dedupe_key: str) -> bool:
        stmt = (
            select(MediaOutbox.id)
            .where(MediaOutbox.dedupe_key == dedupe_key)
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def create_enqueue_event(
        self,
        job_id: int,
        *,
        suffix: str = "enqueue",
    ) -> MediaOutbox:
        row = MediaOutbox(
            job_id=job_id,
            event_type="media_job_enqueue",
            dedupe_key=outbox_dedupe_key(job_id, suffix=suffix),
            status=MediaOutboxStatus.pending,
        )
        return await self.create(row)

    async def list_pending(self, *, limit: int) -> list[MediaOutbox]:
        stmt = (
            select(MediaOutbox)
            .where(MediaOutbox.status == MediaOutboxStatus.pending)
            .order_by(MediaOutbox.id)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def mark_dispatched(self, outbox_id: int, *, now: datetime | None = None) -> bool:
        ts = now or datetime.now(UTC)
        stmt = (
            update(MediaOutbox)
            .where(
                MediaOutbox.id == outbox_id,
                MediaOutbox.status == MediaOutboxStatus.pending,
            )
            .values(status=MediaOutboxStatus.dispatched, dispatched_at=ts)
        )
        result = await self._session.execute(stmt)
        return (result.rowcount or 0) > 0
