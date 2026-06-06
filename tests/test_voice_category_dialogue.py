from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient

from app.api.deps import get_current_user, get_voice_service
from app.main import app as fastapi_app
from app.models.category_enums import CategoryFieldType, ModerationAction
from app.schemas.category_intelligence import (
    CategoryDialogueResponse,
    CategoryFieldRead,
    CategoryRoutingResult,
)
from app.models.enums import ListingStatus
from app.schemas.user import UserRead
from app.schemas.voice import VoiceCommandRequest
from app.services.speech_to_text_service import SpeechToTextService
from app.services.voice_service import VoiceService
from app.services.voice_session_store import InMemoryVoiceSessionStore


def _field(key: str, hint: str | None = None) -> CategoryFieldRead:
    return CategoryFieldRead(
        field_key=key,
        label=key,
        field_type=CategoryFieldType.string,
        is_required=True,
        sort_order=0,
        ai_hint=hint,
    )


def _routing(
    *,
    category_id: int | None = 10,
    slug: str = "transport-cars",
    name: str = "Легковые автомобили",
    mode: str = "alias",
    confidence: float = 0.9,
) -> CategoryRoutingResult:
    return CategoryRoutingResult(
        category_id=category_id,
        category_slug=slug,
        category_name=name,
        confidence=confidence,
        mode=mode,
        extracted={"vehicle_model": "camry"},
    )


def _dialogue(
    *,
    routing: CategoryRoutingResult | None = None,
    missing: list[CategoryFieldRead] | None = None,
    next_question: str | None = None,
    moderation_action: ModerationAction = ModerationAction.allow,
    message: str = "ok",
) -> CategoryDialogueResponse:
    r = routing or _routing()
    missing = missing or []
    return CategoryDialogueResponse(
        routing=r,
        missing_core_fields=missing,
        next_question=next_question,
        moderation_action=moderation_action,
        message=message or (next_question or "ok"),
    )


class _ListingStub:
    def __init__(self) -> None:
        self.created: list[dict[str, Any]] = []

    async def create_listing(self, body, owner_id: int):
        self.created.append({"body": body, "owner_id": owner_id})

        class _Created:
            id = 99
            images: list = []

            def model_dump(self, mode: str = "json"):
                return {
                    "id": 99,
                    "title": body.title,
                    "category_id": body.category_id,
                    "owner_id": owner_id,
                    "images": [],
                }

        return _Created()

    async def get_feed(self, **_k):
        return []


class _SavedStub:
    async def create_saved_search(self, *_a, **_k):
        raise AssertionError("not expected")


class _UnusedSttStub(SpeechToTextService):
    async def transcribe(self, audio_bytes: bytes) -> str:
        raise AssertionError("STT should not be called")


_TEST_SESSION_STORE = InMemoryVoiceSessionStore(ttl_seconds=3600.0)


class _IntelMock:
    def __init__(self, responses: list[CategoryDialogueResponse]) -> None:
        self._responses = list(responses)
        self.calls: list[dict[str, Any]] = []

    async def dialogue(self, payload):
        self.calls.append({"text": payload.text, "known_fields": dict(payload.known_fields)})
        if not self._responses:
            return _dialogue()
        return self._responses.pop(0)


def _stub_user() -> UserRead:
    now = datetime.now(UTC)
    return UserRead(
        id=42,
        phone="+70000000001",
        full_name="Dialogue Tester",
        is_active=True,
        balance=Decimal("0"),
        last_login=None,
        created_at=now,
        updated_at=now,
    )


def _wire_voice(intel: _IntelMock, listings: _ListingStub | None = None) -> VoiceService:
    return VoiceService(
        listings or _ListingStub(),
        _SavedStub(),
        _UnusedSttStub(),
        category_intelligence=intel,
        session_store=_TEST_SESSION_STORE,
    )


def _override_voice(intel: _IntelMock, listings: _ListingStub | None = None):
    return lambda: _wire_voice(intel, listings)


@pytest.fixture(autouse=True)
def _clear_pending_sessions():
    _TEST_SESSION_STORE._sessions.clear()
    yield
    _TEST_SESSION_STORE._sessions.clear()


@pytest.mark.asyncio
async def test_implicit_create_listing_asks_city(client: AsyncClient) -> None:
    intel = _IntelMock(
        [
            _dialogue(
                missing=[_field("city", "В каком городе?")],
                next_question="В каком городе?",
                message="В каком городе?",
            ),
        ],
    )
    fastapi_app.dependency_overrides[get_current_user] = _stub_user
    fastapi_app.dependency_overrides[get_voice_service] = _override_voice(intel)

    resp = await client.post("/api/v1/voice/command", json={"text": "продаю камри"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["intent"]["intent"] == "create_listing"
    assert data["needs_clarification"] is True
    assert data["next_question"] == "В каком городе?"
    assert intel.calls[0]["known_fields"] == {}


@pytest.mark.asyncio
async def test_multi_step_vehicle_dialogue(client: AsyncClient) -> None:
    listings = _ListingStub()
    intel = _IntelMock(
        [
            _dialogue(
                missing=[_field("city", "В каком городе?")],
                next_question="В каком городе?",
            ),
            _dialogue(
                missing=[_field("year", "Какой год выпуска?")],
                next_question="Какой год выпуска?",
            ),
            _dialogue(
                missing=[_field("steering_side", "Левый или правый руль?")],
                next_question="Левый или правый руль?",
            ),
            _dialogue(missing=[], message="Готово"),
        ],
    )
    fastapi_app.dependency_overrides[get_current_user] = _stub_user
    fastapi_app.dependency_overrides[get_voice_service] = _override_voice(intel, listings)

    r1 = await client.post("/api/v1/voice/command", json={"text": "продаю камри"})
    assert r1.json()["needs_clarification"] is True

    r2 = await client.post("/api/v1/voice/command", json={"text": "Бишкек"})
    assert r2.json()["next_question"] == "Какой год выпуска?"
    assert intel.calls[1]["known_fields"].get("city") == "Бишкек"

    r3 = await client.post("/api/v1/voice/command", json={"text": "2018"})
    assert r3.json()["next_question"] == "Левый или правый руль?"
    assert intel.calls[2]["known_fields"].get("year") == "2018"

    r4 = await client.post("/api/v1/voice/command", json={"text": "левый"})
    d4 = r4.json()
    assert d4.get("publish_confirmation_required") is True
    assert d4.get("draft_preview") is not None
    assert d4.get("real_photo_required") is True
    assert "доверия" in d4["message"]
    assert len(listings.created) == 0

    r5 = await client.post("/api/v1/voice/command", json={"text": "подтверждаю"})
    d5 = r5.json()
    assert "фото" in d5["message"].lower()
    assert d5.get("publish_blocked_missing_photo") is True
    assert len(listings.created) == 1
    assert listings.created[0]["body"].status == ListingStatus.draft
    assert d5.get("promotion_offer") is None


@pytest.mark.asyncio
async def test_contextual_year_not_new_intent(client: AsyncClient) -> None:
    intel = _IntelMock(
        [
            _dialogue(
                missing=[_field("year", "Какой год?")],
                next_question="Какой год?",
            ),
            _dialogue(missing=[]),
        ],
    )
    voice = _wire_voice(intel)
    user = _stub_user()
    await voice.handle_command(VoiceCommandRequest(text="продаю камри"), user)
    resp = await voice.handle_command(VoiceCommandRequest(text="2018"), user)
    assert resp.publish_confirmation_required is True or resp.draft_preview is not None
    assert intel.calls[-1]["known_fields"].get("year") == "2018"


@pytest.mark.asyncio
async def test_low_confidence_category_clarification(client: AsyncClient) -> None:
    intel = _IntelMock(
        [
            _dialogue(
                routing=_routing(
                    category_id=None,
                    mode="clarification",
                    confidence=0.4,
                    slug=None,
                    name="Авто",
                ),
                missing=[],
                message="Уточните категорию",
            ),
        ],
    )
    fastapi_app.dependency_overrides[get_current_user] = _stub_user
    fastapi_app.dependency_overrides[get_voice_service] = _override_voice(intel)

    resp = await client.post("/api/v1/voice/command", json={"text": "продаю что-то странное"})
    data = resp.json()
    assert data["needs_clarification"] is True
    assert data["intent"]["intent"] == "create_listing"


@pytest.mark.asyncio
async def test_moderation_interrupt(client: AsyncClient) -> None:
    listings = _ListingStub()
    intel = _IntelMock(
        [
            _dialogue(
                moderation_action=ModerationAction.block,
                message="Запрещено",
            ),
        ],
    )
    fastapi_app.dependency_overrides[get_current_user] = _stub_user
    fastapi_app.dependency_overrides[get_voice_service] = _override_voice(intel, listings)

    resp = await client.post("/api/v1/voice/command", json={"text": "продаю лекарство"})
    data = resp.json()
    assert data["moderation_required"] is True
    assert len(listings.created) == 0


@pytest.mark.asyncio
async def test_livestock_dialogue_age_then_city(client: AsyncClient) -> None:
    intel = _IntelMock(
        [
            _dialogue(
                routing=_routing(category_id=20, slug="animals-livestock", name="Сельхоз животные"),
                missing=[_field("age", "Сколько лет?")],
                next_question="Сколько лет?",
            ),
            _dialogue(
                routing=_routing(category_id=20, slug="animals-livestock", name="Сельхоз животные"),
                missing=[_field("purpose", "Дойная?")],
                next_question="Дойная?",
            ),
            _dialogue(
                routing=_routing(category_id=20, slug="animals-livestock", name="Сельхоз животные"),
                missing=[_field("city", "Где находится?")],
                next_question="Где находится?",
            ),
            _dialogue(routing=_routing(category_id=20, slug="animals-livestock", name="Сельхоз"), missing=[]),
        ],
    )
    fastapi_app.dependency_overrides[get_current_user] = _stub_user
    fastapi_app.dependency_overrides[get_voice_service] = _override_voice(intel)

    await client.post("/api/v1/voice/command", json={"text": "продаю корову"})
    r2 = await client.post("/api/v1/voice/command", json={"text": "4 года"})
    assert intel.calls[1]["known_fields"].get("age") == "4 года"
    r3 = await client.post("/api/v1/voice/command", json={"text": "да"})
    assert intel.calls[2]["known_fields"].get("purpose") == "да"


@pytest.mark.asyncio
async def test_fashion_size_dialogue(client: AsyncClient) -> None:
    intel = _IntelMock(
        [
            _dialogue(
                routing=_routing(category_id=30, slug="fashion-clothing", name="Одежда"),
                missing=[_field("size", "Какой размер?")],
                next_question="Какой размер?",
            ),
            _dialogue(routing=_routing(category_id=30, slug="fashion-clothing", name="Одежда"), missing=[]),
        ],
    )
    fastapi_app.dependency_overrides[get_current_user] = _stub_user
    fastapi_app.dependency_overrides[get_voice_service] = _override_voice(intel)

    await client.post("/api/v1/voice/command", json={"text": "продаю платье"})
    r2 = await client.post("/api/v1/voice/command", json={"text": "M"})
    assert intel.calls[1]["known_fields"].get("size") == "M"


@pytest.mark.asyncio
async def test_search_empty_suggests_save(client: AsyncClient) -> None:
    intel = _IntelMock([])
    fastapi_app.dependency_overrides[get_current_user] = _stub_user
    fastapi_app.dependency_overrides[get_voice_service] = _override_voice(intel)

    resp = await client.post("/api/v1/voice/command", json={"text": "найди iphone"})
    data = resp.json()
    assert data["intent"]["intent"] == "search_listings"
    assert data["suggest_save_search"] is True


@pytest.mark.asyncio
async def test_new_command_resets_session(client: AsyncClient) -> None:
    intel = _IntelMock(
        [
            _dialogue(
                missing=[_field("city", "В каком городе?")],
                next_question="В каком городе?",
            ),
            _dialogue(missing=[]),
        ],
    )
    voice = _wire_voice(intel)
    user = _stub_user()
    await voice.handle_command(VoiceCommandRequest(text="продаю камри"), user)
    await voice.handle_command(VoiceCommandRequest(text="найди iphone"), user)
    assert len(intel.calls) == 1
    assert _TEST_SESSION_STORE.get(user.id) is None


@pytest.mark.asyncio
async def test_city_required_in_missing_fields(client: AsyncClient) -> None:
    intel = _IntelMock(
        [
            _dialogue(
                missing=[_field("city", "В каком городе?")],
                next_question="В каком городе?",
            ),
        ],
    )
    fastapi_app.dependency_overrides[get_current_user] = _stub_user
    fastapi_app.dependency_overrides[get_voice_service] = _override_voice(intel)

    resp = await client.post("/api/v1/voice/command", json={"text": "продаю камри"})
    missing_keys = [f["field_key"] for f in resp.json()["missing_fields"]]
    assert "city" in missing_keys
