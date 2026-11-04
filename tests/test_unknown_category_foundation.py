"""Media Classification Substage 1 — unknown category foundation."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.core.config import Settings
from app.core.exceptions import AppException
from app.media_engine.router import MediaPipelineKind, route_pipeline
from app.models.enums import Currency, ListingStatus
from app.models.media_enums import MediaLifecycleStatus
from app.models.media_job import build_media_job_idempotency_key
from app.schemas.listing import ListingCreate, ListingStatusUpdate
from app.services.direct_upload_service import DirectUploadService
from app.services.listing_service import ListingService
from app.services.media_category_processing import enqueue_category_aware_media_for_listing
from app.services.storage_service import StorageService
from app.storage.memory import InMemoryObjectStorage


def test_route_pipeline_unknown_is_general_not_auto() -> None:
    assert route_pipeline(None) == MediaPipelineKind.GENERAL
    assert route_pipeline("") == MediaPipelineKind.GENERAL
    assert route_pipeline("transport-car-sale") == MediaPipelineKind.AUTO
    assert route_pipeline("realty-apartment") == MediaPipelineKind.GENERAL


def test_listing_create_allows_null_category_for_draft() -> None:
    body = ListingCreate(
        title="Черновик",
        price=Decimal("0"),
        category_id=None,
        status=ListingStatus.draft,
    )
    assert body.category_id is None


def test_listing_create_rejects_null_category_for_active() -> None:
    with pytest.raises(ValueError):
        ListingCreate(
            title="Active",
            price=Decimal("100"),
            category_id=None,
            status=ListingStatus.active,
        )


def test_listing_create_rejects_fields_without_category() -> None:
    with pytest.raises(ValueError):
        ListingCreate(
            title="Draft",
            price=Decimal("0"),
            category_id=None,
            fields={"brand": 1},
        )


@pytest.mark.asyncio
async def test_create_draft_with_null_category() -> None:
    from types import SimpleNamespace

    session = AsyncMock()
    listings = AsyncMock()
    categories = AsyncMock()
    notifications = AsyncMock()

    created = SimpleNamespace(
        id=42,
        status=ListingStatus.draft,
        category_id=None,
        category=None,
        images=[],
        owner_id=1,
        title="Черновик объявления",
        description=None,
        price=Decimal("0"),
        currency=Currency.KGS,
        uses_placeholder_image=False,
        is_promoted=False,
        promotion_daily_rate=None,
        promotion_tier=0,
        promotion_starts_at=None,
        promotion_ends_at=None,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    created.__dict__["field_values"] = []

    listings.create = AsyncMock(return_value=created)
    listings.get_by_id = AsyncMock(return_value=created)

    svc = ListingService(session, listings, categories, notifications)
    body = ListingCreate(
        title="Черновик объявления",
        price=Decimal("0"),
        category_id=None,
        status=ListingStatus.draft,
    )
    read = await svc.create_listing(body, owner_id=1)
    assert read.id == 42
    assert read.category_id is None
    categories.get_by_id.assert_not_called()


@pytest.mark.asyncio
async def test_activate_without_category_forbidden() -> None:
    session = AsyncMock()
    listings = AsyncMock()
    categories = AsyncMock()
    notifications = AsyncMock()

    listing = MagicMock()
    listing.id = 7
    listing.owner_id = 1
    listing.status = ListingStatus.draft
    listing.category_id = None
    listing.images = []
    listing.uses_placeholder_image = False
    listings.get_by_id = AsyncMock(return_value=listing)

    svc = ListingService(session, listings, categories, notifications)
    with pytest.raises(AppException) as exc:
        await svc.change_status(
            7,
            actor_user_id=1,
            payload=ListingStatusUpdate(status=ListingStatus.active),
        )
    assert exc.value.status_code == 400
    assert "category" in str(exc.value).lower()


def _direct_svc(*, category_id: int | None):
    settings = Settings(
        MEDIA_DIRECT_UPLOAD_ENABLED=True,
        MEDIA_ASYNC_PIPELINE_ENABLED=True,
    )
    backend = InMemoryObjectStorage()
    storage = StorageService(settings, backend=backend)
    session = AsyncMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()

    listing = MagicMock()
    listing.id = 10
    listing.owner_id = 1
    listing.category_id = category_id
    listing.category = None

    key = "listings/10/media/99/original.jpg"
    media = MagicMock()
    media.id = 99
    media.listing_id = 10
    media.order = 0
    media.lifecycle_status = MediaLifecycleStatus.uploading
    media.client_upload_id = uuid4()
    media.content_sha256 = None
    media.original_storage_key = key
    media.upload_expires_at = datetime.now(UTC).replace(year=2099)
    media.declared_content_type = "image/jpeg"
    media.declared_content_length = None
    media.is_placeholder = False

    media_repo = MagicMock()
    media_repo.get_by_id_for_update = AsyncMock(return_value=media)
    media_repo.get_by_id = AsyncMock(return_value=media)

    listings = MagicMock()
    listings.get_by_id = AsyncMock(return_value=listing)

    svc = DirectUploadService(
        session,
        media_repo,
        listings,
        storage,
        settings=settings,
        moderation_pipeline=MagicMock(),
    )
    return svc, media, backend, key, session


@pytest.mark.asyncio
async def test_direct_upload_complete_defers_job_without_category(monkeypatch) -> None:
    svc, media, backend, key, session = _direct_svc(category_id=None)
    backend.put(key, b"\xff\xd8\xff\xd9", content_type="image/jpeg")

    enqueued: list[int] = []

    class _JobSvc:
        def __init__(self, *a, **k):
            pass

        async def enqueue_for_media(self, media_id, *, pipeline_version, category_id=None):
            enqueued.append(media_id)
            return MagicMock()

    monkeypatch.setattr("app.media_queue.job_service.MediaJobService", _JobSvc)

    result = await svc.complete(listing_id=10, media_id=99, actor_user_id=1)
    assert result.status == MediaLifecycleStatus.queued
    assert result.queued is False
    assert enqueued == []
    assert media.lifecycle_status == MediaLifecycleStatus.queued


@pytest.mark.asyncio
async def test_direct_upload_complete_enqueues_when_category_known(monkeypatch) -> None:
    svc, media, backend, key, session = _direct_svc(category_id=5)
    backend.put(key, b"\xff\xd8\xff\xd9", content_type="image/jpeg")

    enqueued: list[int] = []

    class _JobSvc:
        def __init__(self, *a, **k):
            pass

        async def enqueue_for_media(self, media_id, *, pipeline_version, category_id=None):
            enqueued.append(media_id)
            return MagicMock()

    monkeypatch.setattr("app.media_queue.job_service.MediaJobService", _JobSvc)
    monkeypatch.setattr(
        "app.services.direct_upload_service.DirectUploadService._best_effort_dispatch_outbox",
        AsyncMock(),
    )

    result = await svc.complete(listing_id=10, media_id=99, actor_user_id=1)
    assert result.queued is True
    assert enqueued == [99]


@pytest.mark.asyncio
async def test_enqueue_category_aware_idempotent(monkeypatch) -> None:
    settings = Settings(MEDIA_ASYNC_PIPELINE_ENABLED=True)
    session = AsyncMock()

    listing = MagicMock()
    listing.id = 3
    listing.category_id = 8

    media = MagicMock()
    media.id = 50
    media.is_placeholder = False
    media.original_storage_key = "k"
    media.lifecycle_status = MediaLifecycleStatus.queued
    media.pipeline_version = None

    monkeypatch.setattr(
        "app.services.media_category_processing.ListingRepository",
        lambda s: MagicMock(get_by_id=AsyncMock(return_value=listing)),
    )
    monkeypatch.setattr(
        "app.services.media_category_processing.MediaRepository",
        lambda s: MagicMock(list_by_listing=AsyncMock(return_value=[media])),
    )

    key = build_media_job_idempotency_key(
        50, settings.MEDIA_ASYNC_PIPELINE_VERSION, category_id=8
    )
    existing_job = MagicMock()
    calls = {"n": 0}

    class _JobRepo:
        async def get_by_idempotency_key(self, k):
            return existing_job if k == key else None

        async def list_for_media(self, media_id):
            return []

    class _JobSvc:
        def __init__(self, *a, **k):
            pass

        async def enqueue_for_media(self, media_id, *, pipeline_version, category_id=None):
            calls["n"] += 1
            return MagicMock()

    monkeypatch.setattr(
        "app.services.media_category_processing.MediaJobRepository",
        lambda s: _JobRepo(),
    )
    monkeypatch.setattr("app.media_queue.job_service.MediaJobService", _JobSvc)

    n = await enqueue_category_aware_media_for_listing(session, 3, settings=settings)
    assert n == 0
    assert calls["n"] == 0

    monkeypatch.setattr(
        "app.services.media_category_processing.MediaJobRepository",
        lambda s: MagicMock(
            get_by_idempotency_key=AsyncMock(return_value=None),
            list_for_media=AsyncMock(return_value=[]),
        ),
    )
    n2 = await enqueue_category_aware_media_for_listing(session, 3, settings=settings)
    assert n2 == 1
    assert calls["n"] == 1


@pytest.mark.asyncio
async def test_enqueue_multiple_queued_media_when_category_known(monkeypatch) -> None:
    settings = Settings(MEDIA_ASYNC_PIPELINE_ENABLED=True)
    session = AsyncMock()
    listing = MagicMock()
    listing.id = 3
    listing.category_id = 681

    medias = []
    for mid in (101, 102, 103):
        m = MagicMock()
        m.id = mid
        m.is_placeholder = False
        m.original_storage_key = f"k{mid}"
        m.lifecycle_status = MediaLifecycleStatus.queued
        m.pipeline_version = None
        medias.append(m)

    monkeypatch.setattr(
        "app.services.media_category_processing.ListingRepository",
        lambda s: MagicMock(get_by_id=AsyncMock(return_value=listing)),
    )
    monkeypatch.setattr(
        "app.services.media_category_processing.MediaRepository",
        lambda s: MagicMock(list_by_listing=AsyncMock(return_value=medias)),
    )
    enqueued: list[int] = []

    class _JobRepo:
        async def get_by_idempotency_key(self, k):
            return None

        async def list_for_media(self, media_id):
            return []

    class _JobSvc:
        def __init__(self, *a, **k):
            pass

        async def enqueue_for_media(self, media_id, *, pipeline_version, category_id=None):
            enqueued.append(media_id)
            return MagicMock()

    monkeypatch.setattr(
        "app.services.media_category_processing.MediaJobRepository",
        lambda s: _JobRepo(),
    )
    monkeypatch.setattr("app.media_queue.job_service.MediaJobService", _JobSvc)

    n = await enqueue_category_aware_media_for_listing(session, 3, settings=settings)
    assert n == 3
    assert enqueued == [101, 102, 103]


@pytest.mark.asyncio
async def test_enqueue_skips_when_non_dead_job_already_exists(monkeypatch) -> None:
    from app.models.media_job_enums import MediaJobStatus

    settings = Settings(MEDIA_ASYNC_PIPELINE_ENABLED=True)
    session = AsyncMock()
    listing = MagicMock()
    listing.id = 3
    listing.category_id = 8

    media = MagicMock()
    media.id = 50
    media.is_placeholder = False
    media.original_storage_key = "k"
    media.lifecycle_status = MediaLifecycleStatus.queued
    media.pipeline_version = None

    prior = MagicMock()
    prior.status = MediaJobStatus.queued

    monkeypatch.setattr(
        "app.services.media_category_processing.ListingRepository",
        lambda s: MagicMock(get_by_id=AsyncMock(return_value=listing)),
    )
    monkeypatch.setattr(
        "app.services.media_category_processing.MediaRepository",
        lambda s: MagicMock(list_by_listing=AsyncMock(return_value=[media])),
    )
    calls = {"n": 0}

    class _JobRepo:
        async def get_by_idempotency_key(self, k):
            return None

        async def list_for_media(self, media_id):
            return [prior]

    class _JobSvc:
        def __init__(self, *a, **k):
            pass

        async def enqueue_for_media(self, media_id, *, pipeline_version, category_id=None):
            calls["n"] += 1
            return MagicMock()

    monkeypatch.setattr(
        "app.services.media_category_processing.MediaJobRepository",
        lambda s: _JobRepo(),
    )
    monkeypatch.setattr("app.media_queue.job_service.MediaJobService", _JobSvc)

    n = await enqueue_category_aware_media_for_listing(session, 3, settings=settings)
    assert n == 0
    assert calls["n"] == 0


@pytest.mark.asyncio
async def test_enqueue_skipped_when_category_still_null(monkeypatch) -> None:
    settings = Settings(MEDIA_ASYNC_PIPELINE_ENABLED=True)
    session = AsyncMock()
    listing = MagicMock()
    listing.id = 3
    listing.category_id = None
    monkeypatch.setattr(
        "app.services.media_category_processing.ListingRepository",
        lambda s: MagicMock(get_by_id=AsyncMock(return_value=listing)),
    )
    n = await enqueue_category_aware_media_for_listing(session, 3, settings=settings)
    assert n == 0
