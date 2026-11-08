"""Enqueue category-aware Media Engine jobs after category is known.

Foundation hook for Media Classification (Substage 1/2).
Does not invent categories — only starts deferred processing.
"""

from __future__ import annotations

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.media_engine.router import MediaPipelineKind, route_pipeline
from app.models.media import Media
from app.models.media_enums import MediaLifecycleStatus
from app.models.media_job import MediaJob, build_media_job_idempotency_key
from app.models.media_job_enums import MediaJobStatus
from app.repositories.category_repository import CategoryRepository
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


def _force_ready_from_variants(media: Media) -> bool:
    """Restore ready when variants already exist (no heavy reprocess needed)."""
    if not _media_has_processed_variants(media):
        return False
    if media.lifecycle_status == MediaLifecycleStatus.ready:
        return True
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
    return True


async def _category_slug(
    session: AsyncSession,
    category_id: int | None,
) -> str | None:
    if category_id is None:
        return None
    cat = await CategoryRepository(session).get_by_id(category_id)
    return cat.slug if cat is not None else None


async def heal_media_lifecycle_for_listing_category(
    session: AsyncSession,
    listing_id: int,
    *,
    settings: Settings | None = None,
) -> int:
    """
    Repair media stuck in ``queued`` when variants exist or a succeeded job
    matches the listing's current category. Also supersedes stale queued jobs.
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
    keep_key = None
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
        keep_key = key
        existing = await job_repo.get_by_idempotency_key(key)
        restored = _restore_ready_from_succeeded_job(media, existing)
        if not restored and _media_has_processed_variants(media):
            # Variants already on disk — do not wait for a duplicate job.
            if any(j.status == MediaJobStatus.succeeded for j in await job_repo.list_for_media(media.id)):
                restored = _force_ready_from_variants(media)
        if restored:
            healed += 1
        await job_repo.supersede_actionable_except(
            media.id,
            keep_idempotency_key=key
            if existing and existing.status in (
                MediaJobStatus.queued,
                MediaJobStatus.leased,
                MediaJobStatus.failed,
            )
            else None,
        )

    return healed


async def enqueue_category_aware_media_for_listing(
    session: AsyncSession,
    listing_id: int,
    *,
    settings: Settings | None = None,
) -> int:
    """
    Enqueue final Media Engine jobs for uploaded media waiting on category.

    Idempotent: at most one actionable job per media for the current category.
    Stale category-scoped queued jobs are superseded.
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
            key = build_media_job_idempotency_key(
                media.id, pipeline, category_id=category_id
            )
            await job_repo.supersede_actionable_except(
                media.id,
                keep_idempotency_key=None,
            )
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
            await job_repo.supersede_actionable_except(
                media.id,
                keep_idempotency_key=key
                if existing.status
                in (
                    MediaJobStatus.queued,
                    MediaJobStatus.leased,
                    MediaJobStatus.failed,
                )
                else None,
            )
            continue

        prior_jobs = await job_repo.list_for_media(media.id)
        actionable = [
            j
            for j in prior_jobs
            if j.status
            in (
                MediaJobStatus.queued,
                MediaJobStatus.leased,
                MediaJobStatus.failed,
            )
        ]
        # Prefer a single actionable job: supersede others, keep newest pending
        # only if it already targets this category (handled above). Otherwise
        # supersede all then create current-category job.
        if actionable:
            await job_repo.supersede_actionable_except(
                media.id,
                keep_idempotency_key=None,
            )

        await job_svc.enqueue_for_media(
            media.id,
            pipeline_version=pipeline,
            category_id=category_id,
        )
        created_count += 1
        await job_repo.supersede_actionable_except(
            media.id,
            keep_idempotency_key=key,
        )

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
    Category A→B before publish.

    Engine reads ``listing.category`` at process time — not the job key — so
    GENERAL→GENERAL flips (Repair L2, Services, …) must not spawn new heavy
    jobs. Keep one actionable job or restore ready when variants exist.

    AUTO (car-sale) may enqueue one dedicated job when entering that route.
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
    new_slug = await _category_slug(session, new_category_id)
    new_kind = route_pipeline(new_slug)

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
        prior_jobs = await job_repo.list_for_media(media.id)
        actionable = [
            j
            for j in prior_jobs
            if j.status
            in (
                MediaJobStatus.queued,
                MediaJobStatus.leased,
                MediaJobStatus.failed,
            )
        ]
        has_succeeded = any(j.status == MediaJobStatus.succeeded for j in prior_jobs)
        has_variants = _media_has_processed_variants(media)

        # --- Exact category job already exists ---
        if existing is not None and existing.status == MediaJobStatus.succeeded:
            _restore_ready_from_succeeded_job(media, existing)
            await job_repo.supersede_actionable_except(
                media.id, keep_idempotency_key=None
            )
            continue
        if existing is not None and existing.status in (
            MediaJobStatus.queued,
            MediaJobStatus.leased,
            MediaJobStatus.failed,
        ):
            await job_repo.supersede_actionable_except(
                media.id, keep_idempotency_key=key
            )
            continue

        # --- GENERAL: never multiply jobs; engine uses live listing category ---
        if new_kind != MediaPipelineKind.AUTO:
            if has_variants and (
                has_succeeded or media.lifecycle_status == MediaLifecycleStatus.ready
            ):
                _force_ready_from_variants(media)
                await job_repo.supersede_actionable_except(
                    media.id, keep_idempotency_key=None
                )
                logger.info(
                    "media_category_switch_skip_reprocess media_id=%s "
                    "new_category_id=%s kind=general",
                    media.id,
                    new_category_id,
                )
                continue
            if actionable:
                keep = max(actionable, key=lambda j: j.id)
                await job_repo.supersede_actionable_except(
                    media.id, keep_idempotency_key=keep.idempotency_key
                )
                if media.lifecycle_status == MediaLifecycleStatus.ready:
                    # Still waiting on that single job — demote only if somehow ready
                    # without variants (should not happen).
                    if not has_variants:
                        validate_lifecycle_transition(
                            media.lifecycle_status, MediaLifecycleStatus.queued
                        )
                        media.lifecycle_status = MediaLifecycleStatus.queued
                logger.info(
                    "media_category_switch_reuse_pending_job media_id=%s "
                    "keep_job_id=%s new_category_id=%s",
                    media.id,
                    keep.id,
                    new_category_id,
                )
                continue
            # No actionable job yet — enqueue once for current category.
            if media.lifecycle_status != MediaLifecycleStatus.queued:
                media.lifecycle_status = MediaLifecycleStatus.queued
            await job_svc.enqueue_for_media(
                media.id,
                pipeline_version=pipeline,
                category_id=new_category_id,
            )
            created += 1
            await job_repo.supersede_actionable_except(
                media.id, keep_idempotency_key=key
            )
            continue

        # --- AUTO (car-sale): may need dedicated focus pipeline ---
        if has_variants and has_succeeded and existing is not None:
            _force_ready_from_variants(media)
            await job_repo.supersede_actionable_except(
                media.id, keep_idempotency_key=None
            )
            continue

        await job_repo.supersede_actionable_except(
            media.id, keep_idempotency_key=None
        )
        if media.lifecycle_status in (
            MediaLifecycleStatus.ready,
            MediaLifecycleStatus.processing,
        ):
            validate_lifecycle_transition(
                media.lifecycle_status, MediaLifecycleStatus.queued
            )
            media.lifecycle_status = MediaLifecycleStatus.queued
        elif media.lifecycle_status != MediaLifecycleStatus.queued:
            media.lifecycle_status = MediaLifecycleStatus.queued

        await job_svc.enqueue_for_media(
            media.id,
            pipeline_version=pipeline,
            category_id=new_category_id,
        )
        created += 1
        await job_repo.supersede_actionable_except(
            media.id, keep_idempotency_key=key
        )

    if created:
        logger.info(
            "category_change_media_requeued listing_id=%s count=%s category_id=%s",
            listing_id,
            created,
            new_category_id,
        )
    return created


async def cleanup_duplicate_actionable_media_jobs(
    session: AsyncSession,
    *,
    media_id: int | None = None,
    settings: Settings | None = None,
) -> dict[str, int]:
    """
    Maintenance: for each media keep at most one actionable job matching the
    listing's current category (or the newest queued job if category unknown).
    """
    cfg = settings or get_settings()
    if not cfg.MEDIA_ASYNC_PIPELINE_ENABLED:
        return {"media_scanned": 0, "superseded": 0}

    media_repo = MediaRepository(session)
    job_repo = MediaJobRepository(session)
    listings = ListingRepository(session)
    pipeline = cfg.MEDIA_ASYNC_PIPELINE_VERSION

    if media_id is not None:
        media_rows = [await media_repo.get_by_id(media_id)]
        media_rows = [m for m in media_rows if m is not None]
    else:
        # Caller should pass media_id for targeted cleanup; full-scan avoided.
        return {"media_scanned": 0, "superseded": 0}

    superseded_total = 0
    for media in media_rows:
        listing = await listings.get_by_id(media.listing_id)
        keep_key = None
        if listing and listing.category_id is not None:
            keep_key = build_media_job_idempotency_key(
                media.id, pipeline, category_id=listing.category_id
            )
            existing = await job_repo.get_by_idempotency_key(keep_key)
            if existing is None or existing.status not in (
                MediaJobStatus.queued,
                MediaJobStatus.leased,
                MediaJobStatus.failed,
            ):
                # Prefer keep nothing actionable if current-cat job isn't pending;
                # variants path can heal separately.
                if _media_has_processed_variants(media):
                    keep_key = None
                    if media.lifecycle_status == MediaLifecycleStatus.queued:
                        _force_ready_from_variants(media)
        superseded_total += await job_repo.supersede_actionable_except(
            media.id,
            keep_idempotency_key=keep_key,
        )

    return {"media_scanned": len(media_rows), "superseded": superseded_total}
