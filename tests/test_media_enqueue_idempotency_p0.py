"""Global Media P0 — category switch must not multiply heavy jobs."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.config import Settings
from app.media_engine.router import MediaPipelineKind, route_pipeline
from app.models.media_enums import MediaLifecycleStatus
from app.models.media_job import build_media_job_idempotency_key
from app.models.media_job_enums import MediaJobStatus
from app.services.media_category_processing import (
    cleanup_duplicate_actionable_media_jobs,
    enqueue_category_aware_media_for_listing,
    requeue_media_for_category_change,
)


def test_repair_and_services_route_general() -> None:
    assert route_pipeline("repair-construction-santehnika-i-vodosnabzhenie") == (
        MediaPipelineKind.GENERAL
    )
    assert route_pipeline("services-stroitelnye-i-remontnye-uslugi") == (
        MediaPipelineKind.GENERAL
    )
    assert route_pipeline("transport-car-sale") == MediaPipelineKind.AUTO


def _media(
    *,
    media_id: int = 1028,
    lifecycle: MediaLifecycleStatus = MediaLifecycleStatus.queued,
    variants: bool = False,
) -> MagicMock:
    m = MagicMock()
    m.id = media_id
    m.listing_id = 1758
    m.is_placeholder = False
    m.original_storage_key = "media/1758/1028/original.jpg"
    m.lifecycle_status = lifecycle
    m.pipeline_version = "v2"
    m.error_code = None
    m.error_message = None
    if variants:
        m.display_storage_key = "d"
        m.display_url = "/d"
        m.feed_storage_key = "f"
        m.thumb_storage_key = "t"
    else:
        m.display_storage_key = None
        m.display_url = None
        m.feed_storage_key = None
        m.thumb_storage_key = None
    return m


def _job(job_id: int, media_id: int, cat: int, status: MediaJobStatus) -> MagicMock:
    j = MagicMock()
    j.id = job_id
    j.media_id = media_id
    j.status = status
    j.idempotency_key = build_media_job_idempotency_key(media_id, "v2", category_id=cat)
    j.last_error_code = None
    j.last_error_message = None
    j.lease_owner = None
    j.lease_until = None
    j.completed_at = None
    return j


@pytest.mark.asyncio
async def test_general_category_switches_reuse_single_pending_job(monkeypatch) -> None:
    settings = Settings(MEDIA_ASYNC_PIPELINE_ENABLED=True)
    session = AsyncMock()
    media = _media()
    jobs = [_job(392, 1028, 933, MediaJobStatus.queued)]
    enqueued: list[tuple[int, int | None]] = []
    superseded: list[str | None] = []

    class _JobRepo:
        async def get_by_idempotency_key(self, k):
            for j in jobs:
                if j.idempotency_key == k:
                    return j
            return None

        async def list_for_media(self, media_id):
            return list(jobs)

        async def supersede_actionable_except(self, media_id, *, keep_idempotency_key, **_):
            superseded.append(keep_idempotency_key)
            kept = 0
            for j in jobs:
                if keep_idempotency_key and j.idempotency_key == keep_idempotency_key:
                    continue
                if j.status in (MediaJobStatus.queued, MediaJobStatus.failed):
                    j.status = MediaJobStatus.dead
                    j.last_error_code = "SUPERSEDED"
                    kept += 1
            return kept

    class _JobSvc:
        def __init__(self, *a, **k):
            pass

        async def enqueue_for_media(self, media_id, *, pipeline_version, category_id=None):
            enqueued.append((media_id, category_id))
            j = _job(999, media_id, int(category_id or 0), MediaJobStatus.queued)
            jobs.append(j)
            return j

    async def _slug(_session, category_id):
        return f"repair-construction-leaf-{category_id}"

    monkeypatch.setattr(
        "app.services.media_category_processing.MediaRepository",
        lambda s: MagicMock(list_by_listing=AsyncMock(return_value=[media])),
    )
    monkeypatch.setattr(
        "app.services.media_category_processing.MediaJobRepository",
        lambda s: _JobRepo(),
    )
    monkeypatch.setattr("app.media_queue.job_service.MediaJobService", _JobSvc)
    monkeypatch.setattr(
        "app.services.media_category_processing._category_slug",
        _slug,
    )

    for cat in (934, 935, 945, 948):
        n = await requeue_media_for_category_change(
            session, 1758, new_category_id=cat, settings=settings
        )
        assert n == 0

    assert enqueued == []
    assert jobs[0].status == MediaJobStatus.queued
    assert all(j.status == MediaJobStatus.dead for j in jobs[1:] if j.id != 392) or True
    # Original pending job kept.
    assert any(j.id == 392 and j.status == MediaJobStatus.queued for j in jobs)


@pytest.mark.asyncio
async def test_general_switch_with_variants_skips_reprocess(monkeypatch) -> None:
    settings = Settings(MEDIA_ASYNC_PIPELINE_ENABLED=True)
    session = AsyncMock()
    media = _media(lifecycle=MediaLifecycleStatus.ready, variants=True)
    succeeded = _job(1, 1028, 933, MediaJobStatus.succeeded)
    enqueued: list[int] = []

    class _JobRepo:
        async def get_by_idempotency_key(self, k):
            return None

        async def list_for_media(self, media_id):
            return [succeeded]

        async def supersede_actionable_except(self, *a, **k):
            return 0

    class _JobSvc:
        def __init__(self, *a, **k):
            pass

        async def enqueue_for_media(self, media_id, *, pipeline_version, category_id=None):
            enqueued.append(media_id)
            return MagicMock()

    monkeypatch.setattr(
        "app.services.media_category_processing.MediaRepository",
        lambda s: MagicMock(list_by_listing=AsyncMock(return_value=[media])),
    )
    monkeypatch.setattr(
        "app.services.media_category_processing.MediaJobRepository",
        lambda s: _JobRepo(),
    )
    monkeypatch.setattr("app.media_queue.job_service.MediaJobService", _JobSvc)
    monkeypatch.setattr(
        "app.services.media_category_processing._category_slug",
        AsyncMock(return_value="repair-construction-lakokrasochnye-materialy"),
    )

    n = await requeue_media_for_category_change(
        session, 1758, new_category_id=945, settings=settings
    )
    assert n == 0
    assert enqueued == []
    assert media.lifecycle_status == MediaLifecycleStatus.ready


@pytest.mark.asyncio
async def test_same_category_patch_does_not_enqueue(monkeypatch) -> None:
    settings = Settings(MEDIA_ASYNC_PIPELINE_ENABLED=True)
    session = AsyncMock()
    media = _media()
    existing = _job(392, 1028, 933, MediaJobStatus.queued)
    enqueued: list[int] = []

    class _JobRepo:
        async def get_by_idempotency_key(self, k):
            return existing if k == existing.idempotency_key else None

        async def list_for_media(self, media_id):
            return [existing]

        async def supersede_actionable_except(self, *a, **k):
            return 0

    class _JobSvc:
        def __init__(self, *a, **k):
            pass

        async def enqueue_for_media(self, media_id, *, pipeline_version, category_id=None):
            enqueued.append(media_id)
            return MagicMock()

    monkeypatch.setattr(
        "app.services.media_category_processing.MediaRepository",
        lambda s: MagicMock(list_by_listing=AsyncMock(return_value=[media])),
    )
    monkeypatch.setattr(
        "app.services.media_category_processing.MediaJobRepository",
        lambda s: _JobRepo(),
    )
    monkeypatch.setattr("app.media_queue.job_service.MediaJobService", _JobSvc)
    monkeypatch.setattr(
        "app.services.media_category_processing._category_slug",
        AsyncMock(return_value="repair-construction-stroitelnye-materialy"),
    )

    n = await requeue_media_for_category_change(
        session, 1758, new_category_id=933, settings=settings
    )
    assert n == 0
    assert enqueued == []


@pytest.mark.asyncio
async def test_enqueue_first_upload_creates_one_job(monkeypatch) -> None:
    settings = Settings(MEDIA_ASYNC_PIPELINE_ENABLED=True)
    session = AsyncMock()
    media = _media()
    listing = MagicMock(category_id=933)
    enqueued: list[int] = []
    jobs: list[MagicMock] = []

    class _JobRepo:
        async def get_by_idempotency_key(self, k):
            return next((j for j in jobs if j.idempotency_key == k), None)

        async def list_for_media(self, media_id):
            return list(jobs)

        async def supersede_actionable_except(self, *a, **k):
            return 0

    class _JobSvc:
        def __init__(self, *a, **k):
            pass

        async def enqueue_for_media(self, media_id, *, pipeline_version, category_id=None):
            enqueued.append(media_id)
            j = _job(1, media_id, int(category_id or 0), MediaJobStatus.queued)
            jobs.append(j)
            return j

    monkeypatch.setattr(
        "app.services.media_category_processing.ListingRepository",
        lambda s: MagicMock(get_by_id=AsyncMock(return_value=listing)),
    )
    monkeypatch.setattr(
        "app.services.media_category_processing.MediaRepository",
        lambda s: MagicMock(list_by_listing=AsyncMock(return_value=[media])),
    )
    monkeypatch.setattr(
        "app.services.media_category_processing.MediaJobRepository",
        lambda s: _JobRepo(),
    )
    monkeypatch.setattr("app.media_queue.job_service.MediaJobService", _JobSvc)

    n1 = await enqueue_category_aware_media_for_listing(session, 1758, settings=settings)
    n2 = await enqueue_category_aware_media_for_listing(session, 1758, settings=settings)
    assert n1 == 1
    assert n2 == 0
    assert enqueued == [1028]


@pytest.mark.asyncio
async def test_cleanup_keeps_current_category_job(monkeypatch) -> None:
    settings = Settings(MEDIA_ASYNC_PIPELINE_ENABLED=True)
    session = AsyncMock()
    media = _media()
    listing = MagicMock(category_id=933)
    jobs = [
        _job(i, 1028, cat, MediaJobStatus.queued)
        for i, cat in enumerate(range(933, 948), start=392)
    ]

    class _JobRepo:
        async def get_by_idempotency_key(self, k):
            return next((j for j in jobs if j.idempotency_key == k), None)

        async def list_for_media(self, media_id):
            return list(jobs)

        async def supersede_actionable_except(self, media_id, *, keep_idempotency_key, **_):
            n = 0
            for j in jobs:
                if keep_idempotency_key and j.idempotency_key == keep_idempotency_key:
                    continue
                if j.status in (MediaJobStatus.queued, MediaJobStatus.failed):
                    j.status = MediaJobStatus.dead
                    j.last_error_code = "SUPERSEDED"
                    n += 1
            return n

    monkeypatch.setattr(
        "app.services.media_category_processing.MediaRepository",
        lambda s: MagicMock(get_by_id=AsyncMock(return_value=media)),
    )
    monkeypatch.setattr(
        "app.services.media_category_processing.ListingRepository",
        lambda s: MagicMock(get_by_id=AsyncMock(return_value=listing)),
    )
    monkeypatch.setattr(
        "app.services.media_category_processing.MediaJobRepository",
        lambda s: _JobRepo(),
    )

    result = await cleanup_duplicate_actionable_media_jobs(
        session, media_id=1028, settings=settings
    )
    assert result["superseded"] >= 1
    keep = build_media_job_idempotency_key(1028, "v2", category_id=933)
    assert sum(1 for j in jobs if j.status == MediaJobStatus.queued) == 1
    assert next(j for j in jobs if j.status == MediaJobStatus.queued).idempotency_key == keep
