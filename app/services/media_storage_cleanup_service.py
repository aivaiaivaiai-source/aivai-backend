"""Abandoned uploads + orphan blob reconciliation (Stage 5)."""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.models.media import Media
from app.models.media_enums import MediaLifecycleStatus
from app.repositories.media_storage_cleanup_repository import MediaStorageCleanupRepository
from app.services.storage_service import StorageService

logger = logging.getLogger(__name__)


class MediaStorageCleanupService:
    def __init__(
        self,
        session: AsyncSession,
        storage: StorageService,
        settings: Settings,
    ) -> None:
        self._session = session
        self._storage = storage
        self._settings = settings
        self._repo = MediaStorageCleanupRepository(session)

    async def enqueue_keys(
        self,
        keys: list[str],
        *,
        media_id: int | None,
        reason: str,
    ) -> None:
        for key in keys:
            if key:
                await self._repo.enqueue(storage_key=key, media_id=media_id, reason=reason)

    async def process_pending(self, *, batch_size: int | None = None) -> int:
        from app.media_upload import metrics

        limit = batch_size or self._settings.MEDIA_STORAGE_CLEANUP_BATCH
        max_attempts = self._settings.MEDIA_STORAGE_CLEANUP_MAX_ATTEMPTS
        pending = await self._repo.list_pending(limit=limit)
        done = 0
        for row in pending:
            try:
                self._storage.delete_key(row.storage_key)
                await self._repo.mark_done(row.id)
                done += 1
                metrics.incr("cleanup_success_total")
            except Exception as exc:
                logger.warning(
                    "storage_cleanup_failed key=%s attempt=%s",
                    row.storage_key,
                    row.attempt_count + 1,
                )
                await self._repo.mark_failed(
                    row.id,
                    error=str(exc),
                    max_attempts=max_attempts,
                )
                metrics.incr("cleanup_failure_total")
        if done:
            await self._session.commit()
        return done

    async def expire_abandoned_uploads(self, *, batch_size: int | None = None) -> int:
        from app.media_upload import metrics

        limit = batch_size or self._settings.MEDIA_UPLOAD_CLEANUP_BATCH
        now = datetime.now(UTC)
        stmt = (
            select(Media)
            .where(
                Media.lifecycle_status == MediaLifecycleStatus.uploading,
                Media.upload_expires_at.is_not(None),
                Media.upload_expires_at < now,
                Media.chat_id.is_(None),
            )
            .order_by(Media.id)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        rows = list(result.scalars().all())
        expired = 0
        for media in rows:
            if media.original_storage_key and self._storage.exists_key(
                media.original_storage_key,
            ):
                await self._repo.enqueue(
                    storage_key=media.original_storage_key,
                    media_id=media.id,
                    reason="abandoned_upload",
                )
            await self._session.execute(delete(Media).where(Media.id == media.id))
            expired += 1
            metrics.incr("upload_expired_total")
        if expired:
            await self._session.commit()
        return expired
