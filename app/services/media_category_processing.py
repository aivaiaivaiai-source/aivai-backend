"""Enqueue category-aware Media Engine jobs after category is known.

Foundation hook for Media Classification (Substage 1/2).
Does not invent categories — only starts deferred processing.
"""

from __future__ import annotations

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.models.media import Media
from app.models.media_enums import MediaLifecycleStatus
from app.models.media_job import MediaJob, build_media_job_idempotency_key
from app.models.media_job_enums import MediaJobStatus
from app.repositories.listing_repository import ListingRepository
from app.repositories.media_job_repository import MediaJobRepository
from app.repositories.media_repository import MediaRepository
from app.services.media_lifecycle import validate_lifecycle_transition

logger = logging.getLogger(__name__)


def _media_has_processed_variants(media: Media) -> bool:
    return bool(
        media.display_storage_key
        or media.display_url
        or media.feed_storage_key
        or media.thumb_storage_key
    )


def _restore_ready_from_succeeded_job(media: Media, job: MediaJob | None) -> bool:
    """
    Category A→B→A can demote lifecycle to queued while the cat:A job already
    succeeded. Restore ready when variants exist so publish is not stuck waiting.
    """
    if job is None or job.status != MediaJobStatus.succeeded:
        return False
    if not _media_has_processed_variants(media):
        return False
    if media.lifecycle_status == MediaLifecycleStatus.ready:
        return False
    if media.lifecycle_status in (
        MediaLifecycleStatus.rejected,
        MediaLifecycleStatus.failed,
        MediaLifecycleStatus.uploading,
    ):
        return False
    validate_lifecycle_transition(
        media.lifecycle_status,
        MediaLifecycleStatus.ready,
    )
    media.lifecycle_status = MediaLifecycleStatus.ready
    media.error_code = None
    media.error_message = None
    logger.info(
        "media_lifecycle_restored_after_category_job_dedupe media_id=%s job_id=%s",
        media.id,
        job.id,
    )
    return True


async def heal_media_lifecycle_for_listing_category(
    session: AsyncSession,
    listing_id: int,
    *,
    settings: Settings | None = None,
) -> int:
    """
    Repair media stuck in ``queued`` when a succeeded job already exists for the
    listing's current category (category flip A→B→A dedupe hole).
    """
    cfg = settings or get_settings()
    if not cfg.MEDIA_ASYNC_PIPELINE_ENABLED:
        return 0

    listing = await ListingRepository(session).get_by_id(listing_id)
    if listing is None or listing.category_id is None:
        return 0

    media_repo = MediaRepository(session)
    job_repo = MediaJobRepository(session)
    pipeline = cfg.MEDIA_ASYNC_PIPELINE_VERSION
    category_id = listing.category_id
    healed = 0

    for media in await media_repo.list_by_listing(listing_id):
        if getattr(media, "is_placeholder", False):
            continue
        if media.lifecycle_status != MediaLifecycleStatus.queued:
            continue
        if not media.original_storage_key:
            continue
        key = build_media_job_idempotency_key(
            media.id, pipeline, category_id=category_id
        )
        existing = await job_repo.get_by_idempotency_key(key)
        if _restore_ready_from_succeeded_job(media, existing):
            healed += 1

    return healed


async def enqueue_category_aware_media_for_listing(
    session: AsyncSession,
    listing_id: int,
    *,
    settings: Settings | None = None,
) -> int:
    """
    Enqueue final Media Engine jobs for uploaded media waiting on category.

    Idempotent via existing job idempotency keys (includes category_id).
    Returns number of newly created jobs.
    """
    cfg = settings or get_settings()
    if not cfg.MEDIA_ASYNC_PIPELINE_ENABLED:
        return 0

    listing = await ListingRepository(session).get_by_id(listing_id)
    if listing is None or listing.category_id is None:
        return 0

    from app.media_queue.job_service import MediaJobService

    media_repo = MediaRepository(session)
    job_repo = MediaJobRepository(session)
    rows = await media_repo.list_by_listing(listing_id)
    job_svc = MediaJobService(session, cfg)
    created_count = 0
    pipeline = cfg.MEDIA_ASYNC_PIPELINE_VERSION
    category_id = listing.category_id

    for media in rows:
        if getattr(media, "is_placeholder", False):
            continue
        if not media.original_storage_key:
            continue
        if media.lifecycle_status in (
            MediaLifecycleStatus.ready,
            MediaLifecycleStatus.rejected,
            MediaLifecycleStatus.failed,
            MediaLifecycleStatus.uploading,
            MediaLifecycleStatus.processing,
        ):
            continue

        # Deferred uploads sit in ``queued`` without a MediaJob until category.
        if media.lifecycle_status != MediaLifecycleStatus.queued:
            media.lifecycle_status = MediaLifecycleStatus.queued
        media.pipeline_version = pipeline

        key = build_media_job_idempotency_key(
            media.id, pipeline, category_id=category_id
        )
        existing = await job_repo.get_by_idempotency_key(key)
        if existing is not None:
            # A→B→A: job for this category already finished — do not leave queued.
            _restore_ready_from_succeeded_job(media, existing)
            continue

        # Extra guard: one media → one non-dead processing lifecycle.
        prior_jobs = await job_repo.list_for_media(media.id)
        if any(j.status != MediaJobStatus.dead for j in prior_jobs):
            continue

        await job_svc.enqueue_for_media(
            media.id,
            pipeline_version=pipeline,
            category_id=category_id,
        )
        created_count += 1

    if created_count:
        logger.info(
            "category_aware_media_enqueued listing_id=%s count=%s category_id=%s",
            listing_id,
            created_count,
            listing.category_id,
        )
    return created_count


async def requeue_media_for_category_change(
    session: AsyncSession,
    listing_id: int,
    *,
    new_category_id: int,
    settings: Settings | None = None,
) -> int:
    """
    Category A→B before publish: enqueue new category-context jobs.

    Does not bump global MEDIA_PIPELINE_VERSION. Old variants remain; new job
    identity uses category_id in the idempotency key.

    Important: only demote lifecycle to ``queued`` when a *new* job will be
    created. If the target category already has a succeeded job (A→B→A),
    restore/keep ``ready`` so publish readiness is not stuck forever.
    """
    cfg = settings or get_settings()
    if not cfg.MEDIA_ASYNC_PIPELINE_ENABLED:
        return 0

    from app.media_queue.job_service import MediaJobService

    media_repo = MediaRepository(session)
    job_repo = MediaJobRepository(session)
    rows = await media_repo.list_by_listing(listing_id)
    job_svc = MediaJobService(session, cfg)
    pipeline = cfg.MEDIA_ASYNC_PIPELINE_VERSION
    created = 0

    for media in rows:
        if getattr(media, "is_placeholder", False):
            continue
        if not media.original_storage_key:
            continue
        if media.lifecycle_status in (
            MediaLifecycleStatus.rejected,
            MediaLifecycleStatus.failed,
            MediaLifecycleStatus.uploading,
        ):
            continue

        media.pipeline_version = pipeline
        key = build_media_job_idempotency_key(
            media.id, pipeline, category_id=new_category_id
        )
        existing = await job_repo.get_by_idempotency_key(key)
        if existing is not None:
            # Returning to a previously processed category: never leave queued.
            if not _restore_ready_from_succeeded_job(media, existing):
                # Job exists but not succeeded yet — leave current lifecycle;
                # if still ready from prior category and job is in-flight for
                # this category, demote only when job is actively queued/leased.
                if existing.status in (
                    MediaJobStatus.queued,
                    MediaJobStatus.leased,
                    MediaJobStatus.failed,
                ) and media.lifecycle_status in (
                    MediaLifecycleStatus.ready,
                    MediaLifecycleStatus.processing,
                ):
                    validate_lifecycle_transition(
                        media.lifecycle_status, MediaLifecycleStatus.queued
                    )
                    media.lifecycle_status = MediaLifecycleStatus.queued
            continue

        # New category context → demote then enqueue.
        if media.lifecycle_status in (
            MediaLifecycleStatus.ready,
            MediaLifecycleStatus.processing,
        ):
            validate_lifecycle_transition(
                media.lifecycle_status, MediaLifecycleStatus.queued
            )
            media.lifecycle_status = MediaLifecycleStatus.queued

        await job_svc.enqueue_for_media(
            media.id,
            pipeline_version=pipeline,
            category_id=new_category_id,
        )
        created += 1

    if created:
        logger.info(
            "category_change_media_requeued listing_id=%s count=%s category_id=%s",
            listing_id,
            created,
            new_category_id,
        )
    return created
