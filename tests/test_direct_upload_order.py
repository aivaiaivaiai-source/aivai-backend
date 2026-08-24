"""Direct upload slot order — client order wins over initiate timing."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.core.config import Settings
from app.core.exceptions import AppException
from app.models.media_enums import MediaLifecycleStatus
from app.schemas.direct_upload import DirectUploadInitiateRequest
from app.services.direct_upload_service import DirectUploadService
from app.services.storage_service import StorageService
from app.storage.memory import InMemoryObjectStorage


def _listing(owner_id: int = 2) -> SimpleNamespace:
    return SimpleNamespace(id=1, owner_id=owner_id, category=SimpleNamespace(slug="other"))


def _media_row(
    *,
    media_id: int,
    order: int,
    client_upload_id,
) -> SimpleNamespace:
    return SimpleNamespace(
        id=media_id,
        listing_id=1,
        order=order,
        lifecycle_status=MediaLifecycleStatus.uploading,
        client_upload_id=client_upload_id,
        original_storage_key=f"media/1/{media_id}/original.jpg",
        upload_expires_at=datetime.now(UTC) + timedelta(hours=1),
        declared_content_type="image/jpeg",
        declared_content_length=100,
        content_sha256=None,
    )


def _service(
    *,
    existing: list | None = None,
) -> tuple[DirectUploadService, MagicMock, MagicMock]:
    settings = Settings(
        MEDIA_DIRECT_UPLOAD_ENABLED=True,
        MEDIA_ASYNC_PIPELINE_ENABLED=True,
    )
    storage = StorageService(settings, backend=InMemoryObjectStorage())
    session = MagicMock()
    session.commit = AsyncMock()
    media_repo = MagicMock()
    listing_repo = MagicMock()
    listing_repo.get_by_id = AsyncMock(return_value=_listing())
    media_repo.list_by_listing = AsyncMock(return_value=existing or [])
    media_repo.count_incomplete_uploads_for_owner = AsyncMock(return_value=0)
    media_repo.get_by_listing_and_client_upload_id = AsyncMock(return_value=None)
    created_orders: list[int] = []

    async def _create(row):
        created_orders.append(row.order)
        return SimpleNamespace(
            id=100 + row.order,
            listing_id=row.listing_id,
            order=row.order,
            lifecycle_status=row.lifecycle_status,
            client_upload_id=row.client_upload_id,
            original_storage_key=None,
            upload_expires_at=row.upload_expires_at,
            declared_content_type=row.declared_content_type,
            declared_content_length=row.declared_content_length,
            content_sha256=row.content_sha256,
        )

    media_repo.create = AsyncMock(side_effect=_create)
    media_repo.update = AsyncMock(return_value=True)
    media_repo.get_by_id = AsyncMock(
        side_effect=lambda mid: SimpleNamespace(
            id=mid,
            listing_id=1,
            lifecycle_status=MediaLifecycleStatus.uploading,
            client_upload_id=uuid4(),
            original_storage_key=f"media/1/{mid}/original.jpg",
            upload_expires_at=datetime.now(UTC) + timedelta(hours=1),
            declared_content_type="image/jpeg",
            declared_content_length=100,
            content_sha256=None,
        ),
    )
    svc = DirectUploadService(
        session,
        media_repo,
        listing_repo,
        storage,
        settings=settings,
        moderation_pipeline=MagicMock(),
    )
    svc._created_orders = created_orders  # type: ignore[attr-defined]
    return svc, media_repo, listing_repo


@pytest.mark.asyncio
async def test_initiate_uses_client_order_slot_zero() -> None:
    svc, media_repo, _ = _service()
    client_id = uuid4()
    with patch("app.services.direct_upload_service.MEDIA_UPLOAD_INITIATE_LIMITER") as lim:
        lim.hit = AsyncMock()
        await svc.initiate(
            1,
            actor_user_id=2,
            body=DirectUploadInitiateRequest(
                client_upload_id=client_id,
                content_type="image/jpeg",
                content_length=100,
                order=0,
            ),
        )
    create_call = media_repo.create.await_args.args[0]
    assert create_call.order == 0


@pytest.mark.asyncio
async def test_initiate_second_slot_order_one_even_if_first_in_db() -> None:
    first_id = uuid4()
    existing = [_media_row(media_id=50, order=0, client_upload_id=first_id)]
    svc, media_repo, _ = _service(existing=existing)
    with patch("app.services.direct_upload_service.MEDIA_UPLOAD_INITIATE_LIMITER") as lim:
        lim.hit = AsyncMock()
        await svc.initiate(
            1,
            actor_user_id=2,
            body=DirectUploadInitiateRequest(
                client_upload_id=uuid4(),
                content_type="image/jpeg",
                content_length=100,
                order=1,
            ),
        )
    create_call = media_repo.create.await_args.args[0]
    assert create_call.order == 1


@pytest.mark.asyncio
async def test_initiate_duplicate_order_rejected() -> None:
    existing = [_media_row(media_id=50, order=0, client_upload_id=uuid4())]
    svc, _, _ = _service(existing=existing)
    with patch("app.services.direct_upload_service.MEDIA_UPLOAD_INITIATE_LIMITER") as lim:
        lim.hit = AsyncMock()
        with pytest.raises(AppException, match="order slot"):
            await svc.initiate(
                1,
                actor_user_id=2,
                body=DirectUploadInitiateRequest(
                    client_upload_id=uuid4(),
                    content_type="image/jpeg",
                    content_length=100,
                    order=0,
                ),
            )


@pytest.mark.asyncio
async def test_initiate_idempotent_retry_preserves_order() -> None:
    client_id = uuid4()
    hit = _media_row(media_id=77, order=2, client_upload_id=client_id)
    svc, media_repo, _ = _service()
    media_repo.get_by_listing_and_client_upload_id = AsyncMock(return_value=hit)
    with patch("app.services.direct_upload_service.MEDIA_UPLOAD_INITIATE_LIMITER") as lim:
        lim.hit = AsyncMock()
        resp = await svc.initiate(
            1,
            actor_user_id=2,
            body=DirectUploadInitiateRequest(
                client_upload_id=client_id,
                content_type="image/jpeg",
                content_length=100,
                order=0,
            ),
        )
    media_repo.create.assert_not_awaited()
    assert resp.media_id == 77


@pytest.mark.asyncio
async def test_initiate_without_order_falls_back_to_next() -> None:
    existing = [_media_row(media_id=50, order=0, client_upload_id=uuid4())]
    svc, media_repo, _ = _service(existing=existing)
    with patch("app.services.direct_upload_service.MEDIA_UPLOAD_INITIATE_LIMITER") as lim:
        lim.hit = AsyncMock()
        await svc.initiate(
            1,
            actor_user_id=2,
            body=DirectUploadInitiateRequest(
                client_upload_id=uuid4(),
                content_type="image/jpeg",
                content_length=100,
            ),
        )
    create_call = media_repo.create.await_args.args[0]
    assert create_call.order == 1
