"""Substage 3C-1 — listing user intent foundation tests."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient

from app.api.deps import get_current_user, get_listing_user_intent_service
from app.core.config import Settings
from app.core.constants import MAX_USER_INTENT_TEXT_LENGTH
from app.core.exceptions import OwnershipError
from app.main import app as fastapi_app
from app.models.enums import ListingStatus
from app.models.listing_user_intent_enums import ListingUserIntentStatus
from app.schemas.listing_user_intent import ListingUserIntentUpsertRequest
from app.schemas.user import UserRead
from app.services.listing_user_intent_service import ListingUserIntentService
from app.user_intent.fingerprint import (
    hybrid_resolver_input_fingerprint,
    intent_fingerprint,
    normalize_intent_text,
)


def test_user_intent_feature_flag_default_false() -> None:
    """Production/code default is false; local .env may override for dev E2E."""
    field = Settings.model_fields["MEDIA_USER_INTENT_ENABLED"]
    assert field.default is False


def test_normalize_intent_trims_edges() -> None:
    assert normalize_intent_text("  продаю камаз  ") == "продаю камаз"


def test_intent_fingerprint_unicode_and_emoji_stable() -> None:
    a = intent_fingerprint("ищу водителя 🚛")
    b = intent_fingerprint("ищу водителя 🚛")
    c = intent_fingerprint("ищу водителя")
    assert a == b
    assert a != c


def test_intent_fingerprint_changes_on_edit() -> None:
    before = intent_fingerprint("Продаю КамАЗ")
    after = intent_fingerprint("Предлагаю грузоперевозки на КамАЗе")
    assert before != after


def test_hybrid_resolver_input_fingerprint_foundation() -> None:
    fp = hybrid_resolver_input_fingerprint(
        media_set_fingerprint="abc123",
        intent_fingerprint="def456",
        resolver_version="hybrid-v0",
        catalog_snapshot_hash="cat789",
    )
    assert len(fp) == 32
    assert fp == hybrid_resolver_input_fingerprint(
        media_set_fingerprint="abc123",
        intent_fingerprint="def456",
        resolver_version="hybrid-v0",
        catalog_snapshot_hash="cat789",
    )


def test_upsert_schema_rejects_empty_after_trim() -> None:
    with pytest.raises(ValueError):
        ListingUserIntentUpsertRequest(raw_intent_text="   \t  ")


def test_upsert_schema_rejects_over_max_length() -> None:
    with pytest.raises(ValueError):
        ListingUserIntentUpsertRequest(raw_intent_text="x" * (MAX_USER_INTENT_TEXT_LENGTH + 1))


def test_upsert_schema_accepts_unicode() -> None:
    body = ListingUserIntentUpsertRequest(raw_intent_text="  Сдаю экскаватор в аренду  ")
    assert body.raw_intent_text == "Сдаю экскаватор в аренду"


@pytest.mark.asyncio
async def test_upsert_creates_provided_intent() -> None:
    session = AsyncMock()
    listings = AsyncMock()
    intents = AsyncMock()

    listing = SimpleNamespace(
        id=10,
        owner_id=5,
        status=ListingStatus.draft,
    )
    listings.get_by_id = AsyncMock(return_value=listing)
    intents.get_by_listing_id = AsyncMock(return_value=None)

    created = SimpleNamespace(
        listing_id=10,
        raw_intent_text="Продаю КамАЗ",
        intent_status=ListingUserIntentStatus.provided,
        intent_fingerprint=intent_fingerprint("Продаю КамАЗ"),
        intent_version=1,
        updated_at=datetime.now(UTC),
    )
    intents.create = AsyncMock(return_value=created)

    svc = ListingUserIntentService(
        session,
        listings,
        intents,
        settings=Settings(MEDIA_USER_INTENT_ENABLED=True),
    )
    result = await svc.upsert_intent(
        10,
        actor_user_id=5,
        payload=ListingUserIntentUpsertRequest(raw_intent_text="Продаю КамАЗ"),
    )
    assert result.intent_status == "provided"
    assert result.raw_intent_text == "Продаю КамАЗ"
    assert result.intent_version == 1
    session.commit.assert_awaited_once()
    intents.create.assert_awaited_once()


@pytest.mark.asyncio
async def test_upsert_same_text_is_idempotent() -> None:
    session = AsyncMock()
    listings = AsyncMock()
    intents = AsyncMock()

    listing = SimpleNamespace(id=10, owner_id=5, status=ListingStatus.draft)
    listings.get_by_id = AsyncMock(return_value=listing)

    fp = intent_fingerprint("Продаю КамАЗ")
    existing = SimpleNamespace(
        listing_id=10,
        raw_intent_text="Продаю КамАЗ",
        intent_status=ListingUserIntentStatus.provided,
        intent_fingerprint=fp,
        intent_version=2,
        updated_at=datetime.now(UTC),
    )
    intents.get_by_listing_id = AsyncMock(return_value=existing)

    svc = ListingUserIntentService(
        session,
        listings,
        intents,
        settings=Settings(MEDIA_USER_INTENT_ENABLED=True),
    )
    result = await svc.upsert_intent(
        10,
        actor_user_id=5,
        payload=ListingUserIntentUpsertRequest(raw_intent_text="  Продаю КамАЗ  "),
    )
    assert result.intent_version == 2
    session.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_upsert_edit_bumps_version_and_fingerprint() -> None:
    session = AsyncMock()
    listings = AsyncMock()
    intents = AsyncMock()

    listing = SimpleNamespace(id=10, owner_id=5, status=ListingStatus.draft)
    listings.get_by_id = AsyncMock(return_value=listing)

    existing = SimpleNamespace(
        listing_id=10,
        raw_intent_text="Продаю КамАЗ",
        intent_status=ListingUserIntentStatus.provided,
        intent_fingerprint=intent_fingerprint("Продаю КамАЗ"),
        intent_version=1,
        updated_at=datetime.now(UTC),
    )
    intents.get_by_listing_id = AsyncMock(return_value=existing)
    intents.save = AsyncMock(side_effect=lambda row: row)

    svc = ListingUserIntentService(
        session,
        listings,
        intents,
        settings=Settings(MEDIA_USER_INTENT_ENABLED=True),
    )
    result = await svc.upsert_intent(
        10,
        actor_user_id=5,
        payload=ListingUserIntentUpsertRequest(
            raw_intent_text="Предлагаю грузоперевозки на КамАЗе",
        ),
    )
    assert existing.intent_version == 2
    assert existing.raw_intent_text == "Предлагаю грузоперевозки на КамАЗе"
    assert result.intent_version == 2
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_upsert_rejects_non_owner() -> None:
    session = AsyncMock()
    listings = AsyncMock()
    intents = AsyncMock()

    listing = SimpleNamespace(id=10, owner_id=99, status=ListingStatus.draft)
    listings.get_by_id = AsyncMock(return_value=listing)

    svc = ListingUserIntentService(
        session,
        listings,
        intents,
        settings=Settings(MEDIA_USER_INTENT_ENABLED=True),
    )
    with pytest.raises(OwnershipError):
        await svc.upsert_intent(
            10,
            actor_user_id=5,
            payload=ListingUserIntentUpsertRequest(raw_intent_text="Продаю КамАЗ"),
        )


@pytest.mark.asyncio
async def test_upsert_rejects_active_listing() -> None:
    session = AsyncMock()
    listings = AsyncMock()
    intents = AsyncMock()

    listing = SimpleNamespace(id=10, owner_id=5, status=ListingStatus.active)
    listings.get_by_id = AsyncMock(return_value=listing)

    svc = ListingUserIntentService(
        session,
        listings,
        intents,
        settings=Settings(MEDIA_USER_INTENT_ENABLED=True),
    )
    with pytest.raises(Exception) as exc:
        await svc.upsert_intent(
            10,
            actor_user_id=5,
            payload=ListingUserIntentUpsertRequest(raw_intent_text="Продаю КамАЗ"),
        )
    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_get_legacy_listing_without_intent_reads_missing() -> None:
    session = AsyncMock()
    listings = AsyncMock()
    intents = AsyncMock()

    listing = SimpleNamespace(id=10, owner_id=5, status=ListingStatus.draft)
    listings.get_by_id = AsyncMock(return_value=listing)
    intents.get_by_listing_id = AsyncMock(return_value=None)

    svc = ListingUserIntentService(
        session,
        listings,
        intents,
        settings=Settings(MEDIA_USER_INTENT_ENABLED=True),
    )
    result = await svc.get_intent(10, actor_user_id=5)
    assert result.intent_status == "missing"
    assert result.raw_intent_text is None
    assert result.intent_version == 0


@pytest.mark.asyncio
async def test_upsert_disabled_when_feature_flag_off() -> None:
    session = AsyncMock()
    listings = AsyncMock()
    intents = AsyncMock()

    svc = ListingUserIntentService(
        session,
        listings,
        intents,
        settings=Settings(MEDIA_USER_INTENT_ENABLED=False),
    )
    with pytest.raises(Exception) as exc:
        await svc.upsert_intent(
            10,
            actor_user_id=5,
            payload=ListingUserIntentUpsertRequest(raw_intent_text="Продаю КамАЗ"),
        )
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_intent_does_not_assign_category_or_enqueue_auto() -> None:
    """Intent service must not touch category or media classification."""
    session = AsyncMock()
    listings = AsyncMock()
    intents = AsyncMock()

    listing = SimpleNamespace(id=10, owner_id=5, status=ListingStatus.draft, category_id=None)
    listings.get_by_id = AsyncMock(return_value=listing)
    intents.get_by_listing_id = AsyncMock(return_value=None)
    intents.create = AsyncMock(
        return_value=SimpleNamespace(
            listing_id=10,
            raw_intent_text="Продаю КамАЗ",
            intent_status=ListingUserIntentStatus.provided,
            intent_fingerprint=intent_fingerprint("Продаю КамАЗ"),
            intent_version=1,
            updated_at=datetime.now(UTC),
        ),
    )

    svc = ListingUserIntentService(
        session,
        listings,
        intents,
        settings=Settings(MEDIA_USER_INTENT_ENABLED=True),
    )

    with patch(
        "app.services.media_category_processing.enqueue_category_aware_media_for_listing",
        new_callable=AsyncMock,
    ) as enqueue_mock:
        await svc.upsert_intent(
            10,
            actor_user_id=5,
            payload=ListingUserIntentUpsertRequest(raw_intent_text="Продаю КамАЗ"),
        )
        enqueue_mock.assert_not_awaited()

    listings.update.assert_not_called()


class _IntentSvcStub:
    def __init__(self) -> None:
        self.last_payload: ListingUserIntentUpsertRequest | None = None

    async def upsert_intent(
        self,
        listing_id: int,
        *,
        actor_user_id: int,
        payload: ListingUserIntentUpsertRequest,
    ):
        self.last_payload = payload
        from app.schemas.listing_user_intent import ListingUserIntentRead

        return ListingUserIntentRead(
            listing_id=listing_id,
            raw_intent_text=payload.raw_intent_text,
            intent_status="provided",
            intent_fingerprint=intent_fingerprint(payload.raw_intent_text),
            intent_version=1,
            feature_enabled=True,
            updated_at=datetime.now(UTC),
        )


@pytest.mark.asyncio
async def test_put_endpoint_accepts_intent(client: AsyncClient) -> None:
    now = datetime.now(UTC)

    async def fake_user() -> UserRead:
        return UserRead(
            id=501,
            phone="+70009990099",
            full_name="Poster",
            is_active=True,
            balance=Decimal("0"),
            last_login=None,
            created_at=now,
            updated_at=now,
        )

    stub = _IntentSvcStub()
    fastapi_app.dependency_overrides[get_current_user] = fake_user
    fastapi_app.dependency_overrides[get_listing_user_intent_service] = lambda: stub

    resp = await client.put(
        "/api/v1/listings/42/user-intent",
        json={"raw_intent_text": "  ищу водителя на камаз  "},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["intent_status"] == "provided"
    assert body["raw_intent_text"] == "ищу водителя на камаз"
    assert stub.last_payload is not None
    assert stub.last_payload.raw_intent_text == "ищу водителя на камаз"
