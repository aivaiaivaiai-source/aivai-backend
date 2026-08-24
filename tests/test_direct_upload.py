from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from PIL import Image

from app.core.config import Settings
from app.core.exceptions import AppException, OwnershipError
from app.models.media_enums import MediaLifecycleStatus
from app.services.direct_upload_service import DirectUploadService
from app.services.media_delivery_service import MediaDeliveryService
from app.schemas.direct_upload import DirectUploadInitiateRequest
from app.storage.memory import InMemoryObjectStorage
from app.services.storage_service import StorageService


def _jpeg_bytes() -> bytes:
    img = Image.new("RGB", (100, 80), color=(10, 20, 30))
    buf = BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def _listing(owner_id: int = 2) -> SimpleNamespace:
    return SimpleNamespace(id=1, owner_id=owner_id, category=SimpleNamespace(slug="other"))


def _service(
    *,
    settings: Settings | None = None,
    backend: InMemoryObjectStorage | None = None,
) -> tuple[DirectUploadService, MagicMock, MagicMock, StorageService]:
    settings = settings or Settings(
        MEDIA_DIRECT_UPLOAD_ENABLED=True,
        MEDIA_ASYNC_PIPELINE_ENABLED=True,
    )
    backend = backend or InMemoryObjectStorage()
    storage = StorageService(settings, backend=backend)
    session = MagicMock()
    session.commit = AsyncMock()
    session.flush = AsyncMock()
    media_repo = MagicMock()
    listing_repo = MagicMock()
    listing_repo.get_by_id = AsyncMock(return_value=_listing())
    media_repo.list_by_listing = AsyncMock(return_value=[])
    media_repo.count_incomplete_uploads_for_owner = AsyncMock(return_value=0)
    media_repo.get_by_listing_and_client_upload_id = AsyncMock(return_value=None)
    media_repo.create = AsyncMock(
        side_effect=lambda row: SimpleNamespace(
            id=99,
            listing_id=row.listing_id,
            order=row.order,
            lifecycle_status=row.lifecycle_status,
            client_upload_id=row.client_upload_id,
            original_storage_key=None,
            upload_expires_at=row.upload_expires_at,
            declared_content_type=row.declared_content_type,
            declared_content_length=row.declared_content_length,
            content_sha256=row.content_sha256,
        ),
    )
    media_repo.update = AsyncMock(return_value=True)
    media_repo.get_by_id = AsyncMock(
        side_effect=lambda mid: SimpleNamespace(
            id=mid,
            listing_id=1,
            lifecycle_status=MediaLifecycleStatus.uploading,
            client_upload_id=uuid4(),
            original_storage_key="media/1/99/original.jpg",
            upload_expires_at=datetime.now(UTC) + timedelta(hours=1),
            declared_content_type="image/jpeg",
            declared_content_length=len(_jpeg_bytes()),
            content_sha256=None,
        ),
    )
    media_repo.get_by_id_for_update = media_repo.get_by_id
    svc = DirectUploadService(
        session,
        media_repo,
        listing_repo,
        storage,
        settings=settings,
        moderation_pipeline=MagicMock(),
    )
    return svc, media_repo, listing_repo, storage


@pytest.mark.asyncio
async def test_initiate_disabled_returns_404() -> None:
    svc, _, _, _ = _service(settings=Settings(MEDIA_DIRECT_UPLOAD_ENABLED=False))
    with pytest.raises(AppException, match="not enabled"):
        await svc.initiate(
            1,
            actor_user_id=2,
            body=DirectUploadInitiateRequest(
                client_upload_id=uuid4(),
                content_type="image/jpeg",
                content_length=100,
            ),
        )


@pytest.mark.asyncio
async def test_initiate_foreign_listing_forbidden() -> None:
    svc, _, listing_repo, _ = _service()
    listing_repo.get_by_id = AsyncMock(return_value=_listing(owner_id=99))
    with pytest.raises(OwnershipError):
        await svc.initiate(
            1,
            actor_user_id=2,
            body=DirectUploadInitiateRequest(
                client_upload_id=uuid4(),
                content_type="image/jpeg",
                content_length=100,
            ),
        )


@pytest.mark.asyncio
async def test_initiate_returns_presign_without_credentials() -> None:
    svc, _, _, _ = _service()
    with patch("app.services.direct_upload_service.MEDIA_UPLOAD_INITIATE_LIMITER") as lim:
        lim.hit = AsyncMock()
        resp = await svc.initiate(
            1,
            actor_user_id=2,
            body=DirectUploadInitiateRequest(
                client_upload_id=uuid4(),
                content_type="image/jpeg",
                content_length=len(_jpeg_bytes()),
            ),
        )
    assert resp.media_id == 99
    assert resp.upload.method == "PUT"
    assert "secret" not in resp.upload.url.lower()
    assert "access_key" not in resp.upload.url.lower()


@pytest.mark.asyncio
async def test_complete_missing_blob_rejected() -> None:
    svc, media_repo, _, _ = _service()
    media_repo.get_by_id_for_update = AsyncMock(
        return_value=SimpleNamespace(
            id=99,
            listing_id=1,
            lifecycle_status=MediaLifecycleStatus.uploading,
            original_storage_key="media/1/99/original.jpg",
            upload_expires_at=datetime.now(UTC) + timedelta(hours=1),
            declared_content_type="image/jpeg",
            declared_content_length=100,
        ),
    )
    with pytest.raises(AppException, match="not found"):
        await svc.complete(1, 99, actor_user_id=2)


@pytest.mark.asyncio
async def test_complete_valid_blob_queues_job() -> None:
    backend = InMemoryObjectStorage()
    content = _jpeg_bytes()
    key = "media/1/99/original.jpg"
    backend.put(key, content, content_type="image/jpeg")
    svc, media_repo, _, _ = _service(backend=backend)
    media = SimpleNamespace(
        id=99,
        listing_id=1,
        lifecycle_status=MediaLifecycleStatus.uploading,
        original_storage_key=key,
        upload_expires_at=datetime.now(UTC) + timedelta(hours=1),
        declared_content_type="image/jpeg",
        declared_content_length=len(content),
        url="/pending",
        moderation_status=None,
        pipeline_version=None,
    )
    media_repo.get_by_id_for_update = AsyncMock(return_value=media)

    with patch("app.media_queue.job_service.MediaJobService") as job_cls:
        job_cls.return_value.enqueue_for_media = AsyncMock()
        resp = await svc.complete(1, 99, actor_user_id=2)

    assert resp.queued is True
    assert resp.status == MediaLifecycleStatus.queued
    job_cls.return_value.enqueue_for_media.assert_awaited_once()


@pytest.mark.asyncio
async def test_complete_idempotent_when_already_queued() -> None:
    svc, media_repo, _, _ = _service()
    media_repo.get_by_id_for_update = AsyncMock(
        return_value=SimpleNamespace(
            id=99,
            listing_id=1,
            lifecycle_status=MediaLifecycleStatus.queued,
        ),
    )
    resp = await svc.complete(1, 99, actor_user_id=2)
    assert resp.status == MediaLifecycleStatus.queued


def test_cdn_url_resolves_from_storage_key_without_db_url() -> None:
    settings = Settings(MEDIA_CDN_BASE_URL="https://cdn.example.com")
    delivery = MediaDeliveryService(settings)
    url = delivery.public_variant_url("media/1/2/v1/display.jpg")
    assert url == "https://cdn.example.com/media/1/2/v1/display.jpg"


def test_original_private_by_default() -> None:
    settings = Settings(MEDIA_ORIGINAL_PUBLIC=False, MEDIA_CDN_BASE_URL="https://cdn.example.com")
    delivery = MediaDeliveryService(settings)
    assert delivery.original_url("media/1/2/original.jpg") is None


def test_original_not_in_public_variant_resolution() -> None:
    settings = Settings(MEDIA_CDN_BASE_URL="https://cdn.example.com")
    delivery = MediaDeliveryService(settings)
    assert delivery.public_variant_url("media/1/2/original.jpg") is None


@pytest.mark.asyncio
async def test_cleanup_expires_abandoned_upload() -> None:
    from app.services.media_storage_cleanup_service import MediaStorageCleanupService

    session = MagicMock()
    session.commit = AsyncMock()
    session.execute = AsyncMock()
    expired_media = SimpleNamespace(
        id=5,
        original_storage_key="media/1/5/original.jpg",
        lifecycle_status=MediaLifecycleStatus.uploading,
    )
    result = MagicMock()
    result.scalars.return_value.all.return_value = [expired_media]
    session.execute.return_value = result

    settings = Settings()
    storage = StorageService(settings, backend=InMemoryObjectStorage())
    svc = MediaStorageCleanupService(session, storage, settings)
    n = await svc.expire_abandoned_uploads()
    assert n == 1
