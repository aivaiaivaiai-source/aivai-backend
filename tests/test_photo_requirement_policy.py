from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.enums import Currency, ListingStatus
from app.schemas.listing import ListingCreate
from app.schemas.listing_assistant import DraftPreview
from app.schemas.user import UserRead
from app.schemas.voice import VoiceIntent
from app.services.listing_creation_assistant import ListingCreationAssistant
from app.services.photo_requirement_policy import (
    PHOTO_REMINDER_TEXT,
    PUBLISH_BLOCKED_NO_PHOTO,
    allows_placeholder_image,
    can_publish_active,
    count_real_photos,
    has_real_photo,
    is_placeholder_media,
    requires_real_photo,
)
from app.services.voice_response_builder import VoiceResponseBuilder
from app.services.voice_session_store import VoiceDialogueSession


def test_transport_requires_real_photo() -> None:
    assert requires_real_photo("transport-cars") is True
    assert allows_placeholder_image("transport-cars") is False


def test_services_allow_placeholder() -> None:
    assert allows_placeholder_image("services-beauty") is True
    assert requires_real_photo("services-beauty") is False


def test_placeholder_not_counted_as_real_photo() -> None:
    images = [
        SimpleNamespace(is_placeholder=True, url="/media/placeholders/listing-default.png"),
        SimpleNamespace(is_placeholder=False, url="/media/user/1.jpg"),
    ]
    assert count_real_photos(images) == 1
    assert is_placeholder_media(images[0]) is True
    assert has_real_photo(images) is True
    assert has_real_photo([images[0]]) is False


def test_can_publish_active_rules() -> None:
    assert can_publish_active(category_slug="transport-cars", real_photo_count=1) is True
    assert (
        can_publish_active(
            category_slug="transport-cars",
            real_photo_count=0,
            uses_placeholder=True,
        )
        is False
    )
    assert (
        can_publish_active(
            category_slug="services-beauty",
            real_photo_count=0,
            uses_placeholder=True,
        )
        is True
    )


def test_assistant_preview_shows_photo_reminder() -> None:
    session = VoiceDialogueSession(
        user_id=1,
        category_id=5,
        category_slug="electronics-phones",
        category_name="Телефоны",
        seed_text="продаю айфон",
    )
    assistant = ListingCreationAssistant(MagicMock())
    intent = VoiceIntent(intent="create_listing", confidence=0.9, extracted={})
    resp = assistant.ready_for_preview(intent, session, {"city": "Бишкек"})
    assert PHOTO_REMINDER_TEXT in resp.message
    assert resp.real_photo_required is True
    assert resp.draft_preview is not None
    assert resp.draft_preview.real_photo_required is True


@pytest.mark.asyncio
async def test_goods_publish_blocked_without_photo_creates_draft() -> None:
    listings = MagicMock()
    listings.create_listing = AsyncMock(
        return_value=SimpleNamespace(
            id=7,
            images=[],
            model_dump=lambda mode="json": {"id": 7, "status": "draft", "images": []},
        ),
    )
    assistant = ListingCreationAssistant(listings)
    session = VoiceDialogueSession(
        user_id=1,
        category_id=10,
        category_slug="transport-cars",
        known_fields={"city": "Бишкек", "year": "2018"},
        flow_stage="publish_preview",
        generated_title="Toyota Camry",
        generated_description="Продаётся Toyota Camry.",
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

    assert resp.publish_blocked_missing_photo is True
    assert resp.message == PUBLISH_BLOCKED_NO_PHOTO
    assert session.flow_stage == "publish_preview"
    call_body = listings.create_listing.await_args.args[0]
    assert call_body.status == ListingStatus.draft


@pytest.mark.asyncio
async def test_services_can_publish_with_placeholder() -> None:
    listings = MagicMock()
    listings.create_listing = AsyncMock(
        return_value=SimpleNamespace(
            id=8,
            images=[SimpleNamespace(is_placeholder=True, url="/media/placeholders/listing-default.png")],
            model_dump=lambda mode="json": {
                "id": 8,
                "status": "active",
                "uses_placeholder_image": True,
                "images": [{"is_placeholder": True}],
            },
        ),
    )
    assistant = ListingCreationAssistant(listings)
    session = VoiceDialogueSession(
        user_id=1,
        category_id=20,
        category_slug="services-beauty",
        known_fields={"city": "Бишкек"},
        flow_stage="publish_preview",
        generated_title="Барбер",
        generated_description="Оказываю услуги барбера.",
    )
    user = UserRead(
        id=1,
        phone="+70000000000",
        full_name="T",
        is_active=True,
        balance=Decimal("100"),
        last_login=None,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    intent = VoiceIntent(intent="create_listing", confidence=0.9, extracted={})
    resp = await assistant.publish_confirmed(intent, session, user)

    assert resp.promotion_offer is not None
    assert session.flow_stage == "promotion"
    call_body = listings.create_listing.await_args.args[0]
    assert call_body.status == ListingStatus.active
    assert call_body.uses_placeholder_image is True


def test_draft_allowed_without_photo_via_listing_create_default() -> None:
    body = ListingCreate(
        title="Draft item",
        description="Test",
        price=Decimal("100"),
        category_id=1,
        status=ListingStatus.draft,
    )
    assert body.status == ListingStatus.draft
    assert body.uses_placeholder_image is False


def test_draft_preview_response_includes_photo_flags() -> None:
    preview = DraftPreview(
        title="Test",
        description="Short.",
        category_id=1,
        category_slug="transport-cars",
        real_photo_required=True,
        placeholder_allowed=False,
    )
    intent = VoiceIntent(intent="create_listing", confidence=0.9, extracted={})
    resp = VoiceResponseBuilder.draft_preview(
        intent,
        preview=preview,
        message=f"Preview. {PHOTO_REMINDER_TEXT}",
        real_photo_required=True,
    )
    assert resp.real_photo_required is True
    assert PHOTO_REMINDER_TEXT in resp.message
