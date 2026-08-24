"""Durable media job orchestration — PostgreSQL source of truth."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.exceptions import AppException
from app.media_queue import metrics
from app.media_queue.errors import MediaJobError, PermanentMediaJobError, RetryableMediaJobError
from app.media_queue.outbox_dispatcher import dispatch_pending_outbox
from app.media_queue.processor import MediaProcessorOutcome, MediaProcessorResult, NoOpMediaProcessor
from app.media_queue.streams import xack_job
from app.models.media import Media
from app.models.media_enums import MediaLifecycleStatus
from app.models.media_job import MediaJob, build_media_job_idempotency_key
from app.models.media_job_enums import MediaJobStatus
from app.repositories.media_job_repository import MediaJobRepository
from app.repositories.media_outbox_repository import MediaOutboxRepository
from app.repositories.media_repository import MediaRepository
from app.services.media_lifecycle import validate_lifecycle_transition

logger = logging.getLogger(__name__)


def retry_backoff_seconds(settings: Settings, attempt: int) -> int:
    schedule = settings.media_job_retry_backoff_list()
    if not schedule:
        return 60
    idx = min(max(attempt - 1, 0), len(schedule) - 1)
    return schedule[idx]


class MediaJobService:
    def __init__(
        self,
        session: AsyncSession,
        settings: Settings,
        *,
        processor: NoOpMediaProcessor | None = None,
    ) -> None:
        self._session = session
        self._settings = settings
        self._jobs = MediaJobRepository(session)
        self._outbox = MediaOutboxRepository(session)
        self._media = MediaRepository(session)
        self._processor = processor or NoOpMediaProcessor()

    async def enqueue_for_media(
        self,
        media_id: int,
        *,
        pipeline_version: str,
    ) -> MediaJob:
        """Create job + outbox in current transaction (caller commits)."""
        key = build_media_job_idempotency_key(media_id, pipeline_version)
        existing = await self._jobs.get_by_idempotency_key(key)
        if existing is not None:
            return existing

        now = datetime.now(UTC)
        job = MediaJob(
            media_id=media_id,
            idempotency_key=key,
            pipeline_version=pipeline_version,
            status=MediaJobStatus.queued,
            available_at=now,
        )
        created = await self._jobs.create(job)
        try:
            await self._outbox.create_enqueue_event(created.id, suffix="enqueue")
        except Exception as exc:
            raise AppException(
                "Failed to create media outbox event.",
                status_code=500,
            ) from exc
        metrics.incr("jobs_created_total")
        return created

    async def reconcile_undispatched_jobs(self) -> int:
        """Ensure queued/failed DB jobs have a pending outbox row (Redis recovery)."""
        now = datetime.now(UTC)
        jobs = await self._jobs.list_redispatchable(
            now=now,
            limit=self._settings.MEDIA_JOB_RECONCILE_BATCH,
        )
        created = 0
        for job in jobs:
            if job.status == MediaJobStatus.dead:
                continue
            if await self._outbox.has_pending_for_job(job.id):
                continue
            suffix = f"reconcile-a{job.attempt_count}"
            from app.models.media_outbox import outbox_dedupe_key

            dedupe_key = outbox_dedupe_key(job.id, suffix=suffix)
            if await self._outbox.dedupe_key_exists(dedupe_key):
                continue
            try:
                await self._outbox.create_enqueue_event(job.id, suffix=suffix)
                created += 1
            except Exception:
                await self._session.rollback()
                logger.exception("reconcile_outbox_failed job_id=%s", job.id)
        return created

    async def process_stream_message(
        self,
        redis: Redis,
        *,
        job_id: int,
        message_id: str,
        worker_id: str,
    ) -> bool:
        """
        Process one Redis message. Returns True if ACK'd.
        At-least-once + idempotent claim/success handling.
        """
        now = datetime.now(UTC)
        job = await self._jobs.get_by_id_for_update(job_id)
        if job is None:
            logger.warning("media_job_missing job_id=%s — ACK orphan message", job_id)
            await xack_job(redis, self._settings, message_id=message_id)
            return True

        if job.status == MediaJobStatus.succeeded:
            metrics.incr("jobs_redelivery_noop_total")
            await xack_job(redis, self._settings, message_id=message_id)
            return True

        if job.status == MediaJobStatus.dead:
            await xack_job(redis, self._settings, message_id=message_id)
            return True

        if (
            job.status == MediaJobStatus.leased
            and job.lease_until
            and job.lease_until > now
            and job.lease_owner
            and job.lease_owner != worker_id
        ):
            metrics.incr("jobs_active_lease_skip_total")
            return False

        lease_until = now + timedelta(seconds=self._settings.MEDIA_JOB_LEASE_SECONDS)
        claimed = await self._jobs.claim_job(
            job_id,
            worker_id=worker_id,
            lease_until=lease_until,
            now=now,
        )
        if claimed is None:
            refreshed = await self._jobs.get_by_id(job_id)
            if refreshed and refreshed.status == MediaJobStatus.succeeded:
                await xack_job(redis, self._settings, message_id=message_id)
                return True
            return False

        job = claimed
        media = await self._media.get_by_id(job.media_id)
        if media is None:
            await self._mark_dead(job, error_code="MEDIA_MISSING", message="Media row missing")
            await self._session.commit()
            await xack_job(redis, self._settings, message_id=message_id)
            return True

        try:
            validate_lifecycle_transition(media.lifecycle_status, MediaLifecycleStatus.processing)
        except AppException:
            pass
        media.lifecycle_status = MediaLifecycleStatus.processing
        await self._session.flush()

        try:
            result = await self._processor.process(self._session, job=job, media=media)
            await self._finalize_job(job, media, result)
            await self._session.commit()
            await xack_job(redis, self._settings, message_id=message_id)
            metrics.incr("jobs_succeeded_total")
            return True
        except MediaJobError as exc:
            await self._handle_failure(job, media, exc)
            await self._session.commit()
            if job.status in (MediaJobStatus.queued, MediaJobStatus.failed):
                suffix = f"retry-a{job.attempt_count}"
                try:
                    await self._outbox.create_enqueue_event(job.id, suffix=suffix)
                except Exception:
                    logger.exception("retry_outbox_failed job_id=%s", job.id)
            await xack_job(redis, self._settings, message_id=message_id)
            return True
        except Exception as exc:
            wrapped = RetryableMediaJobError(str(exc)[:200])
            await self._handle_failure(job, media, wrapped)
            await self._session.commit()
            if job.status in (MediaJobStatus.queued, MediaJobStatus.failed):
                suffix = f"retry-a{job.attempt_count}"
                try:
                    await self._outbox.create_enqueue_event(job.id, suffix=suffix)
                except Exception:
                    logger.exception("retry_outbox_failed job_id=%s", job.id)
            await xack_job(redis, self._settings, message_id=message_id)
            metrics.incr("jobs_failed_total")
            return True

    async def _finalize_job(
        self,
        job: MediaJob,
        media: Media,
        result: MediaProcessorResult,
    ) -> None:
        now = datetime.now(UTC)
        job.status = MediaJobStatus.succeeded
        job.completed_at = now
        job.lease_owner = None
        job.lease_until = None
        job.last_error_code = None
        job.last_error_message = None

        outcome = result.outcome
        if outcome == MediaProcessorOutcome.ready:
            if not (media.display_url and media.feed_url and media.thumb_url):
                raise PermanentMediaJobError(
                    "variants incomplete after processing",
                    error_code="VARIANTS_INCOMPLETE",
                )
            metrics.incr("jobs_ready_total")
        elif outcome == MediaProcessorOutcome.rejected:
            metrics.incr("jobs_policy_rejected_total")
        elif outcome == MediaProcessorOutcome.review:
            metrics.incr("jobs_policy_review_total")
        elif outcome == MediaProcessorOutcome.processing:
            metrics.incr("jobs_noop_total")

    async def _mark_succeeded(self, job: MediaJob, media: Media) -> None:
        """Deprecated path — use _finalize_job."""
        await self._finalize_job(
            job,
            media,
            MediaProcessorResult(outcome=MediaProcessorOutcome.ready),
        )

    async def _mark_dead(self, job: MediaJob, *, error_code: str, message: str) -> None:
        now = datetime.now(UTC)
        job.status = MediaJobStatus.dead
        job.completed_at = now
        job.last_error_code = error_code
        job.last_error_message = message[:512]
        job.lease_owner = None
        job.lease_until = None
        media = await self._media.get_by_id(job.media_id)
        if media is not None:
            try:
                validate_lifecycle_transition(media.lifecycle_status, MediaLifecycleStatus.failed)
            except AppException:
                pass
            media.lifecycle_status = MediaLifecycleStatus.failed
            media.error_code = error_code
            media.error_message = message[:512]
        metrics.incr("jobs_dead_total")

    async def _handle_failure(
        self,
        job: MediaJob,
        media: Media,
        exc: MediaJobError,
    ) -> None:
        job.last_error_code = exc.error_code
        job.last_error_message = str(exc)[:512]
        job.lease_owner = None
        job.lease_until = None

        max_attempts = self._settings.MEDIA_JOB_MAX_ATTEMPTS
        if isinstance(exc, PermanentMediaJobError) or job.attempt_count >= max_attempts:
            job.status = MediaJobStatus.dead
            job.completed_at = datetime.now(UTC)
            try:
                validate_lifecycle_transition(media.lifecycle_status, MediaLifecycleStatus.failed)
            except AppException:
                pass
            media.lifecycle_status = MediaLifecycleStatus.failed
            media.error_code = exc.error_code
            media.error_message = str(exc)[:512]
            metrics.incr("jobs_dead_total")
            return

        delay = retry_backoff_seconds(self._settings, job.attempt_count)
        job.status = MediaJobStatus.failed
        job.available_at = datetime.now(UTC) + timedelta(seconds=delay)
        metrics.incr("jobs_retry_scheduled_total")


async def run_outbox_and_reconcile(
    session: AsyncSession,
    redis: Redis,
    settings: Settings,
) -> None:
    await dispatch_pending_outbox(session, redis, settings)
    svc = MediaJobService(session, settings)
    await svc.reconcile_undispatched_jobs()
    await dispatch_pending_outbox(session, redis, settings)
