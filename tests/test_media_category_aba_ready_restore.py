"""Regression: category A→B→A must not leave media stuck in queued."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.config import Settings
from app.models.media_enums import MediaLifecycleStatus
from app.models.media_job import build_media_job_idempotency_key
from app.models.media_job_enums import MediaJobStatus
from app.services.media_category_processing import (
    heal_media_lifecycle_for_listing_category,
    requeue_media_for_category_change,
)


@pytest.mark.asyncio
async def test_requeue_aba_restores_ready_when_prior_category_job_succeeded(
    monkeypatch,
) -> None:
    """
    Real Samsung Farm case: leaf 833 → other leaves → back to 833.
    Prior job media:X:pipeline:v2:cat:833 already succeeded; requeue must
    restore lifecycle ready instead of leaving queued with no new job.
    """
    settings = Settings(MEDIA_ASYNC_PIPELINE_ENABLED=True)
    session = AsyncMock()

    media = MagicMock()
    media.id = 582
    media.is_placeholder = False
    media.original_storage_key = "media/603/582/original.jpg"
    media.display_storage_key = "media/603/582/v2/display.jpg"
    media.display_url = "/media/media/603/582/v2/display.jpg"
    media.feed_storage_key = "media/603/582/v2/feed.jpg"
    media.thumb_storage_key = "media/603/582/v2/thumb.jpg"
    media.lifecycle_status = MediaLifecycleStatus.ready
    media.pipeline_version = "v2"
    media.error_code = None
    media.error_message = None

    prior_key = build_media_job_idempotency_key(
        582, settings.MEDIA_ASYNC_PIPELINE_VERSION, category_id=833
    )
    succeeded = MagicMock()
    succeeded.id = 295
    succeeded.status = MediaJobStatus.succeeded

    enqueued: list[int] = []

    class _JobRepo:
        async def get_by_idempotency_key(self, k):
            return succeeded if k == prior_key else None

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
        AsyncMock(return_value="transport-farm-machinery-traktory"),
    )

    # Simulate demotion path: ready media, switch back to previously processed cat.
    media.lifecycle_status = MediaLifecycleStatus.ready
    n = await requeue_media_for_category_change(
        session,
        603,
        new_category_id=833,
        settings=settings,
    )
    assert n == 0
    assert enqueued == []
    assert media.lifecycle_status == MediaLifecycleStatus.ready


@pytest.mark.asyncio
async def test_heal_restores_stuck_queued_after_aba(monkeypatch) -> None:
    settings = Settings(MEDIA_ASYNC_PIPELINE_ENABLED=True)
    session = AsyncMock()

    listing = MagicMock()
    listing.id = 603
    listing.category_id = 833

    media = MagicMock()
    media.id = 582
    media.is_placeholder = False
    media.original_storage_key = "media/603/582/original.jpg"
    media.display_storage_key = "media/603/582/v2/display.jpg"
    media.display_url = "/media/..."
    media.feed_storage_key = "x"
    media.thumb_storage_key = "y"
    media.lifecycle_status = MediaLifecycleStatus.queued
    media.error_code = None
    media.error_message = None

    key = build_media_job_idempotency_key(
        582, settings.MEDIA_ASYNC_PIPELINE_VERSION, category_id=833
    )
    succeeded = MagicMock()
    succeeded.id = 295
    succeeded.status = MediaJobStatus.succeeded

    class _JobRepo:
        async def get_by_idempotency_key(self, k):
            return succeeded if k == key else None

        async def list_for_media(self, media_id):
            return [succeeded]

        async def supersede_actionable_except(self, *a, **k):
            return 0

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

    healed = await heal_media_lifecycle_for_listing_category(
        session, 603, settings=settings
    )
    assert healed == 1
    assert media.lifecycle_status == MediaLifecycleStatus.ready
