from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.image_moderation_enums import MediaModerationStatus
from app.models.media_enums import MediaLifecycleStatus
from app.schemas.image_moderation import ImageModerationOutcome
from app.schemas.media import FocusBboxRead, MediaRead
from app.services.focus_bbox_detection import FocusBBoxResult
from app.services.focus_bbox_service import FocusBBoxService
from app.services.media_service import MediaService


def _listing(*, slug: str = "transport-car-sale") -> SimpleNamespace:
    return SimpleNamespace(
        id=1,
        owner_id=2,
        category=SimpleNamespace(slug=slug),
    )


def _media(*, status: MediaModerationStatus = MediaModerationStatus.approved) -> SimpleNamespace:
    return SimpleNamespace(
        id=99,
        listing_id=1,
        url="/media/x.jpg",
        order=0,
        is_placeholder=False,
        chat_id=None,
        lifecycle_status=MediaLifecycleStatus.ready,
        client_upload_id=None,
        original_url="/media/x.jpg",
        display_url="/media/x.jpg",
        feed_url=None,
        thumb_url=None,
        pipeline_version=None,
        attempt_count=0,
        error_code=None,
        processed_at=datetime.now(UTC),
        moderation_status=status,
        moderation_reason=None,
        moderated_at=datetime.now(UTC),
        focus_bbox_left=None,
        focus_bbox_top=None,
        focus_bbox_width=None,
        focus_bbox_height=None,
        focus_confidence=None,
    )


class _StubDetector:
    def __init__(self, result: FocusBBoxResult | None) -> None:
        self._result = result
        self.calls = 0

    def detect(self, content: bytes, content_type: str) -> FocusBBoxResult | None:
        del content, content_type
        self.calls += 1
        return self._result


@pytest.mark.asyncio
async def test_focus_bbox_service_skips_non_car_category() -> None:
    detector = _StubDetector(
        FocusBBoxResult(left=0.1, top=0.2, width=0.5, height=0.3, confidence=0.9),
    )
    repo = MagicMock()
    repo.update = AsyncMock()
    svc = FocusBBoxService(repo, detector)

    await svc.maybe_detect_and_persist(
        listing=_listing(slug="services-beauty"),
        media=_media(),
        content=b"jpeg",
        content_type="image/jpeg",
    )

    assert detector.calls == 0
    repo.update.assert_not_awaited()


@pytest.mark.asyncio
async def test_focus_bbox_service_skips_rejected_media() -> None:
    detector = _StubDetector(
        FocusBBoxResult(left=0.1, top=0.2, width=0.5, height=0.3, confidence=0.9),
    )
    repo = MagicMock()
    repo.update = AsyncMock()
    svc = FocusBBoxService(repo, detector)

    await svc.maybe_detect_and_persist(
        listing=_listing(),
        media=_media(status=MediaModerationStatus.rejected),
        content=b"jpeg",
        content_type="image/jpeg",
    )

    assert detector.calls == 0
    repo.update.assert_not_awaited()


@pytest.mark.asyncio
async def test_focus_bbox_service_persists_detection_for_car_listing() -> None:
    detector = _StubDetector(
        FocusBBoxResult(left=0.08, top=0.35, width=0.87, height=0.33, confidence=0.97),
    )
    repo = MagicMock()
    repo.update = AsyncMock(return_value=_media())
    svc = FocusBBoxService(repo, detector)

    await svc.maybe_detect_and_persist(
        listing=_listing(),
        media=_media(),
        content=b"jpeg",
        content_type="image/jpeg",
    )

    assert detector.calls == 1
    repo.update.assert_awaited_once_with(
        99,
        focus_bbox_left=0.08,
        focus_bbox_top=0.35,
        focus_bbox_width=0.87,
        focus_bbox_height=0.33,
        focus_confidence=0.97,
    )


def test_media_read_serializes_focus_bbox_from_columns() -> None:
    row = SimpleNamespace(
        id=1,
        listing_id=2,
        url="/media/a.jpg",
        order=0,
        is_placeholder=False,
        moderation_status=MediaModerationStatus.approved,
        moderation_reason=None,
        moderated_at=None,
        focus_bbox_left=0.08,
        focus_bbox_top=0.35,
        focus_bbox_width=0.87,
        focus_bbox_height=0.33,
        focus_confidence=0.97,
    )
    read = MediaRead.model_validate(row)
    assert read.focus_confidence == 0.97
    assert read.focus_bbox == FocusBboxRead(
        left=0.08,
        top=0.35,
        width=0.87,
        height=0.33,
    )


def test_media_read_null_focus_bbox_when_columns_missing() -> None:
    row = SimpleNamespace(
        id=1,
        listing_id=2,
        url="/media/a.jpg",
        order=0,
        is_placeholder=False,
        moderation_status=MediaModerationStatus.approved,
        moderation_reason=None,
        moderated_at=None,
        focus_bbox_left=None,
        focus_bbox_top=None,
        focus_bbox_width=None,
        focus_bbox_height=None,
        focus_confidence=None,
    )
    read = MediaRead.model_validate(row)
    assert read.focus_bbox is None
    assert read.focus_confidence is None


@pytest.mark.asyncio
async def test_media_service_runs_focus_bbox_after_moderation() -> None:
    listing = _listing()
    repo_media = MagicMock()
    repo_media.list_by_listing = AsyncMock(return_value=[])
    repo_media.get_by_listing_and_client_upload_id = AsyncMock(return_value=None)
    created = _media()
    approved = _media()
    approved.focus_bbox_left = 0.08
    approved.focus_bbox_top = 0.35
    approved.focus_bbox_width = 0.87
    approved.focus_bbox_height = 0.33
    approved.focus_confidence = 0.97

    repo_media.create = AsyncMock(return_value=created)
    repo_media.update = AsyncMock(return_value=approved)
    repo_media.delete = AsyncMock(return_value=True)
    repo_media.get_by_id = AsyncMock(side_effect=[approved, approved])
    repo_listing = MagicMock()
    repo_listing.get_by_id = AsyncMock(return_value=listing)
    storage = MagicMock()
    storage.validate_image = MagicMock(return_value=".jpg")
    storage.put_bytes = MagicMock(return_value="/media/media/1/99/original.jpg")
    storage.delete_key = MagicMock()
    pipeline = MagicMock()
    from app.models.image_moderation_enums import ImageModerationVerdict

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
    focus_svc = MagicMock()
    focus_svc.maybe_detect_and_persist = AsyncMock()
    session = MagicMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()

    svc = MediaService(
        session,
        repo_media,
        repo_listing,
        storage,
        moderation_pipeline=pipeline,
        focus_bbox_service=focus_svc,
    )
    result = await svc.add_images(
        1,
        actor_user_id=2,
        payloads=[(b"\xff\xd8\xff" + b"\x00" * 16, "image/jpeg", "ok.jpg")],
    )

    focus_svc.maybe_detect_and_persist.assert_awaited_once()
    assert len(result) == 1
    assert result[0].focus_confidence == 0.97
    assert result[0].focus_bbox is not None
    assert result[0].focus_bbox.width == 0.87
