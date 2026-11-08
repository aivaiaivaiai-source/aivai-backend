from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.media_job import MediaJob, build_media_job_idempotency_key
from app.models.media_job_enums import MediaJobStatus
from app.repositories.base import BaseRepository


class MediaJobRepository(BaseRepository[MediaJob]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, MediaJob)

    async def get_by_idempotency_key(self, key: str) -> MediaJob | None:
        stmt = select(MediaJob).where(MediaJob.idempotency_key == key)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_for_media(self, media_id: int) -> list[MediaJob]:
        stmt = (
            select(MediaJob)
            .where(MediaJob.media_id == media_id)
            .order_by(MediaJob.id)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def supersede_actionable_except(
        self,
        media_id: int,
        *,
        keep_idempotency_key: str | None,
        error_code: str = "SUPERSEDED",
        message: str = "Superseded by newer category context",
    ) -> int:
        """Mark other queued/failed jobs for this media as dead (non-actionable).

        Leased jobs are left alone (in-flight); worker ACK path handles dead.
        Succeeded jobs are retained for A→B→A restore.
        """
        now = datetime.now(UTC)
        jobs = await self.list_for_media(media_id)
        superseded = 0
        for job in jobs:
            if keep_idempotency_key and job.idempotency_key == keep_idempotency_key:
                continue
            if job.status not in (MediaJobStatus.queued, MediaJobStatus.failed):
                continue
            job.status = MediaJobStatus.dead
            job.completed_at = now
            job.lease_owner = None
            job.lease_until = None
            job.last_error_code = error_code
            job.last_error_message = message[:512]
            superseded += 1
        return superseded

    async def get_by_id_for_update(self, job_id: int) -> MediaJob | None:
        stmt = (
            select(MediaJob)
            .where(MediaJob.id == job_id)
            .with_for_update()
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def claim_job(
        self,
        job_id: int,
        *,
        worker_id: str,
        lease_until: datetime,
        now: datetime,
    ) -> MediaJob | None:
        """Atomic claim — only one worker wins."""
        stmt = (
            update(MediaJob)
            .where(
                MediaJob.id == job_id,
                MediaJob.status.in_(
                    (MediaJobStatus.queued, MediaJobStatus.failed, MediaJobStatus.leased),
                ),
                MediaJob.available_at <= now,
                (
                    (MediaJob.lease_until.is_(None))
                    | (MediaJob.lease_until < now)
                    | (MediaJob.lease_owner == worker_id)
                ),
            )
            .values(
                status=MediaJobStatus.leased,
                lease_owner=worker_id,
                lease_until=lease_until,
                attempt_count=MediaJob.attempt_count + 1,
            )
            .returning(MediaJob)
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        if row is not None:
            await self._session.refresh(row)
        return row

    async def list_redispatchable(
        self,
        *,
        now: datetime,
        limit: int,
    ) -> list[MediaJob]:
        stmt = (
            select(MediaJob)
            .where(
                MediaJob.status.in_((MediaJobStatus.queued, MediaJobStatus.failed)),
                MediaJob.available_at <= now,
            )
            .order_by(MediaJob.available_at, MediaJob.id)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    def make_idempotency_key(media_id: int, pipeline_version: str) -> str:
        return build_media_job_idempotency_key(media_id, pipeline_version)
