from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest

from app.core.exceptions import AppException, OwnershipError
from app.models.image_moderation_enums import ImageModerationVerdict, MediaModerationStatus
from app.models.media_enums import MediaLifecycleStatus
from app.schemas.image_moderation import ImageModerationOutcome
from app.schemas.media import MediaRead
from app.services.media_lifecycle import validate_lifecycle_transition
from app.services.media_service import MediaService


def _listing(*, owner_id: int = 2) -> SimpleNamespace:
    return SimpleNamespace(id=1, owner_id=owner_id, category=SimpleNamespace(slug="transport-car-sale"))


def _media_row(
    *,
    media_id: int = 99,
    order: int = 0,
    client_upload_id: UUID | None = None,
    lifecycle: MediaLifecycleStatus = MediaLifecycleStatus.ready,
    moderation: MediaModerationStatus = MediaModerationStatus.approved,
) -> SimpleNamespace:
    return SimpleNamespace(
        id=media_id,
        listing_id=1,
        url="/media/x.jpg",
        order=order,
        is_placeholder=False,
        chat_id=None,
        lifecycle_status=lifecycle,
        client_upload_id=client_upload_id,
        content_sha256="abc123",
        pipeline_version=None,
        attempt_count=0,
        error_code=None,
        processed_at=datetime.now(UTC),
        original_storage_key=None,
        original_url="/media/x.jpg",
        display_url="/media/x.jpg",
        feed_url=None,
        thumb_url=None,
        moderation_status=moderation,
        moderation_reason=None,
        moderated_at=datetime.now(UTC),
        focus_bbox_left=None,
        focus_bbox_top=None,
        focus_bbox_width=None,
        focus_bbox_height=None,
        focus_confidence=None,
    )


def _service_with_mocks(
    *,
    listing: SimpleNamespace | None = None,
    existing: list[SimpleNamespace] | None = None,
) -> tuple[MediaService, MagicMock, MagicMock, MagicMock, MagicMock]:
    listing = listing or _listing()
    repo_media = MagicMock()
    repo_media.list_by_listing = AsyncMock(return_value=existing or [])
    repo_media.get_by_listing_and_client_upload_id = AsyncMock(return_value=None)
    repo_media.create = AsyncMock(
        side_effect=lambda row: _media_row(media_id=99, order=row.order),
    )
    repo_media.get_by_id = AsyncMock(return_value=_media_row())
    repo_media.update = AsyncMock(return_value=_media_row())
    repo_media.delete = AsyncMock(return_value=True)
    repo_listing = MagicMock()
    repo_listing.get_by_id = AsyncMock(return_value=listing)
    storage = MagicMock()
    storage.validate_image = MagicMock(return_value=".jpg")
    storage.put_bytes = MagicMock(return_value="/media/media/1/99/original.jpg")
    storage.delete_key = MagicMock()
    storage.delete_media_blob = MagicMock()
    storage.save_image = MagicMock(return_value="/media/x.jpg")
    pipeline = MagicMock()
    pipeline.process_existing_media = AsyncMock(
        return_value=ImageModerationOutcome(
            media_id=99,
            verdict=ImageModerationVerdict.ALLOW,
            moderation_status=MediaModerationStatus.approved,
            moderation_reason=None,
            moderated_at=datetime.now(UTC),
            blocked_from_listing=False,
        ),
    )
    session = MagicMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    svc = MediaService(session, repo_media, repo_listing, storage, moderation_pipeline=pipeline)
    return svc, repo_media, repo_listing, storage, pipeline


@pytest.mark.parametrize(
    ("current", "target", "ok"),
    [
        (MediaLifecycleStatus.uploading, MediaLifecycleStatus.ready, True),
        (MediaLifecycleStatus.ready, MediaLifecycleStatus.processing, False),
        (MediaLifecycleStatus.processing, MediaLifecycleStatus.failed, True),
    ],
)
def test_lifecycle_transition_validation(
    current: MediaLifecycleStatus,
    target: MediaLifecycleStatus,
    ok: bool,
) -> None:
    if ok:
        validate_lifecycle_transition(current, target)
    else:
        with pytest.raises(AppException):
            validate_lifecycle_transition(current, target)


def test_legacy_media_read_defaults() -> None:
    legacy = SimpleNamespace(
        id=1,
        listing_id=10,
        url="/media/old.jpg",
        order=0,
        is_placeholder=False,
        focus_bbox_left=None,
        focus_bbox_top=None,
        focus_bbox_width=None,
        focus_bbox_height=None,
        focus_confidence=None,
        moderation_status=MediaModerationStatus.approved,
        moderation_reason=None,
        moderated_at=None,
        lifecycle_status=MediaLifecycleStatus.ready,
        client_upload_id=None,
        original_url="/media/old.jpg",
        display_url="/media/old.jpg",
        feed_url=None,
        thumb_url=None,
        pipeline_version=None,
        attempt_count=0,
        error_code=None,
        processed_at=None,
    )
    read = MediaRead.model_validate(legacy)
    assert read.url == "/media/old.jpg"
    assert read.lifecycle_status == MediaLifecycleStatus.ready
    assert read.variants.original == "/media/old.jpg"
    assert read.variants.display == "/media/old.jpg"
    assert read.moderation_status == MediaModerationStatus.approved


@pytest.mark.asyncio
async def test_upload_without_client_upload_id_still_works() -> None:
    svc, _, _, storage, pipeline = _service_with_mocks()
    result = await svc.add_images(
        1,
        actor_user_id=2,
        payloads=[(b"\xff\xd8\xff" + b"\x00" * 16, "image/jpeg", "a.jpg")],
    )
    assert len(result) == 1
    storage.put_bytes.assert_called_once()
    pipeline.process_existing_media.assert_awaited_once()


@pytest.mark.asyncio
async def test_duplicate_client_upload_id_returns_existing() -> None:
    existing_id = uuid4()
    hit = _media_row(client_upload_id=existing_id, media_id=42)
    hit.content_sha256 = None
    svc, repo_media, _, storage, pipeline = _service_with_mocks()
    repo_media.get_by_listing_and_client_upload_id = AsyncMock(return_value=hit)

    result = await svc.add_images(
        1,
        actor_user_id=2,
        payloads=[
            (
                b"\xff\xd8\xff" + b"\x00" * 16,
                "image/jpeg",
                "a.jpg",
                str(existing_id),
            ),
        ],
    )

    assert len(result) == 1
    assert result[0].id == 42
    storage.put_bytes.assert_not_called()
    pipeline.process_existing_media.assert_not_awaited()


@pytest.mark.asyncio
async def test_upload_foreign_listing_forbidden() -> None:
    svc, _, _, _, _ = _service_with_mocks(listing=_listing(owner_id=99))
    with pytest.raises(OwnershipError):
        await svc.add_images(
            1,
            actor_user_id=2,
            payloads=[(b"\xff\xd8\xff" + b"\x00" * 16, "image/jpeg")],
        )


@pytest.mark.asyncio
async def test_delete_foreign_media_forbidden() -> None:
    svc, repo_media, repo_listing, _, _ = _service_with_mocks()
    repo_media.get_by_id = AsyncMock(return_value=_media_row(media_id=5))
    repo_listing.get_by_id = AsyncMock(return_value=_listing(owner_id=99))
    with pytest.raises(OwnershipError):
        await svc.delete_image(5, actor_user_id=2)


@pytest.mark.asyncio
async def test_reorder_foreign_listing_forbidden() -> None:
    from app.schemas.media import MediaReorderRequest

    svc, _, repo_listing, _, _ = _service_with_mocks()
    repo_listing.get_by_id = AsyncMock(return_value=_listing(owner_id=99))
    with pytest.raises(OwnershipError):
        await svc.reorder_images(
            1,
            actor_user_id=2,
            body=MediaReorderRequest(image_ids=[1]),
        )


@pytest.mark.asyncio
async def test_max_nine_listing_photos_enforced() -> None:
    existing = [_media_row(media_id=i, order=i) for i in range(9)]
    svc, _, _, _, _ = _service_with_mocks(existing=existing)
    with pytest.raises(AppException, match="at most 9"):
        await svc.add_images(
            1,
            actor_user_id=2,
            payloads=[(b"\xff\xd8\xff" + b"\x00" * 16, "image/jpeg")],
        )


@pytest.mark.asyncio
async def test_idempotent_retry_does_not_count_toward_limit() -> None:
    existing_id = uuid4()
    existing = [_media_row(media_id=i, order=i) for i in range(9)]
    hit = _media_row(media_id=100, client_upload_id=existing_id)
    hit.content_sha256 = None
    svc, repo_media, _, storage, _ = _service_with_mocks(existing=existing)
    repo_media.get_by_listing_and_client_upload_id = AsyncMock(return_value=hit)

    result = await svc.add_images(
        1,
        actor_user_id=2,
        payloads=[
            (
                b"\xff\xd8\xff" + b"\x00" * 16,
                "image/jpeg",
                "a.jpg",
                str(existing_id),
            ),
        ],
    )
    assert len(result) == 1
    storage.put_bytes.assert_not_called()


def test_media_read_focus_bbox_unchanged() -> None:
    row = _media_row()
    row.focus_bbox_left = 0.1
    row.focus_bbox_top = 0.2
    row.focus_bbox_width = 0.3
    row.focus_bbox_height = 0.4
    row.focus_confidence = 0.95
    read = MediaRead.model_validate(row)
    assert read.focus_bbox is not None
    assert read.focus_bbox.width == 0.3
    assert read.focus_confidence == 0.95


def test_media_read_does_not_expose_error_message() -> None:
    fields = MediaRead.model_fields
    assert "error_message" not in fields


def test_upload_api_backward_compatible_signature() -> None:
    import inspect

    from app.api.v1.endpoints import media as media_ep

    sig = inspect.signature(media_ep.upload_listing_media)
    assert "listing_id" in sig.parameters
    assert "files" in sig.parameters
    assert "client_upload_ids" in sig.parameters


@pytest.mark.asyncio
async def test_storage_put_failure_does_not_leave_ready_media() -> None:
    svc, repo_media, _, storage, pipeline = _service_with_mocks()
    storage.put_bytes = MagicMock(side_effect=RuntimeError("disk full"))

    with pytest.raises(Exception):
        await svc.add_images(
            1,
            actor_user_id=2,
            payloads=[(b"\xff\xd8\xff" + b"\x00" * 16, "image/jpeg")],
        )

    repo_media.delete.assert_awaited()
    pipeline.process_existing_media.assert_not_awaited()


@pytest.mark.asyncio
async def test_db_update_failure_after_put_cleans_blob() -> None:
    svc, repo_media, _, storage, _ = _service_with_mocks()
    repo_media.update = AsyncMock(return_value=None)

    with pytest.raises(Exception):
        await svc.add_images(
            1,
            actor_user_id=2,
            payloads=[(b"\xff\xd8\xff" + b"\x00" * 16, "image/jpeg")],
        )

    storage.delete_key.assert_called()


@pytest.mark.asyncio
async def test_deterministic_listing_storage_key_on_upload() -> None:
    svc, _, _, storage, _ = _service_with_mocks()
    await svc.add_images(
        1,
        actor_user_id=2,
        payloads=[(b"\xff\xd8\xff" + b"\x00" * 16, "image/jpeg")],
    )
    key = storage.put_bytes.call_args.args[0]
    assert key == "media/1/99/original.jpg"
