from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.enums import ListingStatus
from app.models.image_moderation_enums import ImageModerationVerdict, MediaModerationStatus
from app.schemas.image_moderation import ImageClassificationInput
from app.schemas.user import UserRead
from app.schemas.voice import VoiceIntent
from app.services.image_moderation_pipeline import ImageModerationPipeline
from app.services.image_moderation_service import (
    IMAGE_MODERATION_QUEUE_USER_MESSAGE,
    IMAGE_REJECTED_USER_MESSAGE,
    publish_block_reason_for_images,
)
from app.services.image_policy_classifier import StubImagePolicyClassifier
from app.services.listing_creation_assistant import ListingCreationAssistant
from app.services.listing_service import ListingService
from app.services.photo_requirement_policy import (
    can_publish_active,
    count_real_photos,
    is_approved_for_publish,
    validate_images_for_active_publish,
)
from app.services.voice_session_store import VoiceDialogueSession


def _img(
    *,
    is_placeholder: bool = False,
    status: str = MediaModerationStatus.approved.value,
    url: str = "/media/x.jpg",
) -> SimpleNamespace:
    return SimpleNamespace(
        is_placeholder=is_placeholder,
        moderation_status=status,
        url=url,
    )


@pytest.mark.asyncio
async def test_stub_classifier_approved_by_default() -> None:
    clf = StubImagePolicyClassifier()
    result = await clf.classify(
        ImageClassificationInput(content=b"\xff\xd8\xff", content_type="image/jpeg"),
    )
    assert result.verdict == ImageModerationVerdict.ALLOW


@pytest.mark.asyncio
async def test_stub_classifier_rejects_porn_hint() -> None:
    clf = StubImagePolicyClassifier()
    result = await clf.classify(
        ImageClassificationInput(
            content=b"\xff\xd8\xff",
            content_type="image/jpeg",
            source_name="product-porn-shot.jpg",
        ),
    )
    assert result.verdict == ImageModerationVerdict.REJECT


@pytest.mark.asyncio
async def test_stub_classifier_queues_passport_hint() -> None:
    clf = StubImagePolicyClassifier()
    result = await clf.classify(
        ImageClassificationInput(
            content=b"\xff\xd8\xff",
            content_type="image/jpeg",
            source_name="my-passport-scan.jpg",
        ),
    )
    assert result.verdict == ImageModerationVerdict.MODERATION_QUEUE


def test_approved_image_allows_publish() -> None:
    images = [_img(status=MediaModerationStatus.approved.value)]
    assert validate_images_for_active_publish(images) is None
    assert can_publish_active(
        category_slug="transport-cars",
        real_photo_count=1,
        images=images,
    )


def test_rejected_image_blocks_publish() -> None:
    images = [_img(status=MediaModerationStatus.rejected.value)]
    assert validate_images_for_active_publish(images) is not None
    assert count_real_photos(images) == 0
    assert not can_publish_active(
        category_slug="transport-cars",
        real_photo_count=0,
        images=images,
    )


def test_moderation_queue_blocks_active_publish() -> None:
    images = [_img(status=MediaModerationStatus.moderation_queue.value)]
    assert validate_images_for_active_publish(images) is not None
    assert not can_publish_active(
        category_slug="services-beauty",
        real_photo_count=0,
        uses_placeholder=False,
        images=images,
    )


def test_placeholder_skips_moderation_and_counts_as_approved() -> None:
    images = [_img(is_placeholder=True, url="/media/placeholders/listing-default.png")]
    assert is_approved_for_publish(images[0])
    assert validate_images_for_active_publish(images) is None
    assert can_publish_active(
        category_slug="services-beauty",
        real_photo_count=0,
        uses_placeholder=True,
        images=images,
    )


@pytest.mark.asyncio
async def test_pipeline_persists_moderation_status() -> None:
    media = SimpleNamespace(
        id=1,
        listing_id=10,
        url="/media/abc.jpg",
        is_placeholder=False,
    )
    repo = MagicMock()
    repo.update = AsyncMock(return_value=media)
    storage = MagicMock()
    storage.delete_file = MagicMock()
    pipeline = ImageModerationPipeline(
        MagicMock(),
        repo,
        storage,
        classifier=StubImagePolicyClassifier(),
    )
    outcome = await pipeline.process_existing_media(
        media,
        content=b"\xff\xd8\xff",
        content_type="image/jpeg",
        source_name="safe-photo.jpg",
    )
    assert outcome.moderation_status == MediaModerationStatus.approved
    repo.update.assert_awaited_once()
    kwargs = repo.update.await_args.kwargs
    assert kwargs["moderation_status"] == MediaModerationStatus.approved
    assert kwargs["moderated_at"] is not None


def test_listing_service_blocks_activate_with_rejected_media() -> None:
    from app.core.exceptions import AppException

    with pytest.raises(AppException) as exc:
        ListingService._validate_active_publish(
            category_slug="transport-cars",
            images=[_img(status=MediaModerationStatus.rejected.value)],
            uses_placeholder=False,
        )
    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_assistant_returns_rejection_message() -> None:
    listings = MagicMock()
    listings.get_listing = AsyncMock(
        return_value=SimpleNamespace(
            id=5,
            images=[_img(status=MediaModerationStatus.rejected.value)],
        ),
    )
    listings.create_listing = AsyncMock()
    assistant = ListingCreationAssistant(listings)
    session = VoiceDialogueSession(
        user_id=1,
        listing_id=5,
        category_id=10,
        category_slug="transport-cars",
        flow_stage="publish_preview",
        known_fields={"city": "Бишкек"},
        generated_title="Car",
        generated_description="Desc",
    )
    user = UserRead(
        id=1,
        phone="+70000000000",
        full_name="T",
        is_active=True,
        balance=Decimal("0"),
        last_login=None,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    intent = VoiceIntent(intent="create_listing", confidence=0.9, extracted={})
    resp = await assistant.publish_confirmed(intent, session, user)
    assert IMAGE_REJECTED_USER_MESSAGE in resp.message
    listings.create_listing.assert_not_awaited()


@pytest.mark.asyncio
async def test_assistant_returns_moderation_queue_message() -> None:
    listings = MagicMock()
    listings.get_listing = AsyncMock(
        return_value=SimpleNamespace(
            id=5,
            images=[_img(status=MediaModerationStatus.moderation_queue.value)],
        ),
    )
    assistant = ListingCreationAssistant(listings)
    session = VoiceDialogueSession(
        user_id=1,
        listing_id=5,
        category_id=10,
        category_slug="transport-cars",
        flow_stage="publish_preview",
        known_fields={"city": "Бишкек"},
        generated_title="Car",
        generated_description="Desc",
    )
    user = UserRead(
        id=1,
        phone="+70000000000",
        full_name="T",
        is_active=True,
        balance=Decimal("0"),
        last_login=None,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    intent = VoiceIntent(intent="create_listing", confidence=0.9, extracted={})
    resp = await assistant.publish_confirmed(intent, session, user)
    assert resp.message == IMAGE_MODERATION_QUEUE_USER_MESSAGE


def test_old_media_rows_without_status_treated_as_approved() -> None:
    legacy = SimpleNamespace(is_placeholder=False, url="/media/old.jpg")
    assert is_approved_for_publish(legacy)
    assert count_real_photos([legacy]) == 1


def test_upload_api_signature_unchanged() -> None:
    import inspect

    from app.api.v1.endpoints import media as media_ep

    sig = inspect.signature(media_ep.upload_listing_media)
    assert "listing_id" in sig.parameters
    assert "files" in sig.parameters


@pytest.mark.asyncio
async def test_media_service_add_images_returns_media_read_list() -> None:
    from app.services.media_service import MediaService

    listing = SimpleNamespace(id=1, owner_id=2, images=[])
    repo_media = MagicMock()
    repo_media.list_by_listing = AsyncMock(return_value=[])
    repo_media.create = AsyncMock(
        side_effect=lambda row: SimpleNamespace(
            id=99,
            listing_id=row.listing_id,
            url=row.url,
            order=row.order,
            is_placeholder=False,
            moderation_status=MediaModerationStatus.pending,
            moderation_reason=None,
            moderated_at=None,
        ),
    )
    repo_media.get_by_id = AsyncMock(
        return_value=SimpleNamespace(
            id=99,
            listing_id=1,
            url="/media/x.jpg",
            order=0,
            is_placeholder=False,
            moderation_status=MediaModerationStatus.approved,
            moderation_reason=None,
            moderated_at=datetime.now(UTC),
        ),
    )
    repo_listing = MagicMock()
    repo_listing.get_by_id = AsyncMock(return_value=listing)
    storage = MagicMock()
    storage.save_image = MagicMock(return_value="/media/x.jpg")
    pipeline = MagicMock()
    pipeline.process_existing_media = AsyncMock()
    session = MagicMock()
    session.commit = AsyncMock()

    svc = MediaService(
        session,
        repo_media,
        repo_listing,
        storage,
        moderation_pipeline=pipeline,
    )
    result = await svc.add_images(
        1,
        actor_user_id=2,
        payloads=[(b"\xff\xd8\xff" + b"\x00" * 16, "image/jpeg", "ok.jpg")],
    )
    assert len(result) == 1
    assert result[0].moderation_status == MediaModerationStatus.approved
    pipeline.process_existing_media.assert_awaited_once()


def test_publish_block_reason_for_images() -> None:
    assert publish_block_reason_for_images([_img(status="rejected")]) is not None
    assert publish_block_reason_for_images([_img(status="approved")]) is None
