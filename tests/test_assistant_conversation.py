from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import AsyncClient

from app.api.deps import get_assistant_service, get_current_user, get_voice_service
from app.main import app as fastapi_app
from app.models.assistant_enums import (
    AssistantMessageRole,
    AssistantMessageType,
    AssistantUiState,
)
from app.schemas.assistant import AssistantMessageRequest
from app.schemas.listing_assistant import DraftPreview
from app.schemas.user import UserRead
from app.schemas.voice import VoiceCommandResponse, VoiceDialogueState, VoiceIntent
from app.services.assistant_conversation_service import AssistantConversationService
from app.services.assistant_overlay_mapper import build_actions, resolve_ui_state
from app.services.assistant_service import AssistantService
from app.services.assistant_voice_service import AssistantVoiceService
from app.services.text_to_speech_service import TTSResult
from app.services.voice_session_state import voice_session_to_dict
from app.services.voice_session_store import InMemoryVoiceSessionStore, VoiceDialogueSession


def _user() -> UserRead:
    now = datetime.now(UTC)
    return UserRead(
        id=77,
        phone="+70000000077",
        full_name="Assistant User",
        is_active=True,
        balance=Decimal("100"),
        last_login=None,
        created_at=now,
        updated_at=now,
    )


class _TtsStorageMock:
    def save_mp3(self, audio_bytes: bytes) -> str:
        return "/media/tts/mock.mp3"


class _TtsServiceMock:
    async def synthesize(self, text: str):
        return TTSResult(audio_bytes=b"id3", provider="openai", duration_ms=500)


def _assistant_voice() -> AssistantVoiceService:
    return AssistantVoiceService(_TtsServiceMock(), _TtsStorageMock())


def _voice_resp(**kwargs) -> VoiceCommandResponse:
    defaults = {
        "intent": VoiceIntent(intent="create_listing", confidence=0.9, extracted={}),
        "message": "В каком городе находится товар?",
    }
    defaults.update(kwargs)
    return VoiceCommandResponse(**defaults)


class _ConvRepoMock:
    def __init__(self) -> None:
        self.rows: dict[int, SimpleNamespace] = {}
        self._next_id = 1

    async def create(self, obj) -> SimpleNamespace:
        cid = self._next_id
        self._next_id += 1
        row = SimpleNamespace(
            id=cid,
            user_id=obj.user_id,
            status=obj.status,
            state_json=dict(obj.state_json),
            last_activity_at=obj.last_activity_at,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        self.rows[cid] = row
        return row

    async def get_for_user(self, conversation_id: int, user_id: int):
        row = self.rows.get(conversation_id)
        if row is None or row.user_id != user_id:
            return None
        return row

    async def update(self, conversation_id: int, **values):
        row = self.rows.get(conversation_id)
        if row is None:
            return None
        for k, v in values.items():
            setattr(row, k, v)
        return row

    async def touch_activity(self, conversation_id: int) -> None:
        await self.update(conversation_id, last_activity_at=datetime.now(UTC))


class _MsgRepoMock:
    def __init__(self) -> None:
        self.messages: list[SimpleNamespace] = []
        self._next_id = 1

    async def create(self, obj) -> SimpleNamespace:
        mid = self._next_id
        self._next_id += 1
        row = SimpleNamespace(
            id=mid,
            conversation_id=obj.conversation_id,
            role=obj.role,
            content=obj.content,
            message_type=obj.message_type,
            metadata_json=dict(obj.metadata_json),
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        self.messages.append(row)
        return row

    async def list_for_conversation(self, conversation_id: int, *, limit: int = 50, offset: int = 0):
        rows = [m for m in self.messages if m.conversation_id == conversation_id]
        return rows[offset : offset + limit]


@pytest.mark.asyncio
async def test_create_conversation() -> None:
    from app.models.assistant_conversation import AssistantConversation
    from app.models.assistant_enums import AssistantConversationStatus

    svc = AssistantConversationService(
        MagicMock(),
        _ConvRepoMock(),
        _MsgRepoMock(),
    )
    row = await svc.create_conversation(77)
    assert row.user_id == 77
    assert row.status == AssistantConversationStatus.active


@pytest.mark.asyncio
async def test_append_assistant_and_user_messages() -> None:
    conv_repo = _ConvRepoMock()
    msg_repo = _MsgRepoMock()
    svc = AssistantConversationService(MagicMock(), conv_repo, msg_repo)
    conv = await svc.create_conversation(1)
    await svc.append_message(
        conversation_id=conv.id,
        role=AssistantMessageRole.user,
        content="продаю айфон",
        message_type=AssistantMessageType.text,
    )
    await svc.append_message(
        conversation_id=conv.id,
        role=AssistantMessageRole.assistant,
        content="В каком городе находится товар?",
        message_type=AssistantMessageType.text,
    )
    history = await svc.get_history(conv.id, 1)
    assert len(history) == 2
    assert history[0].role == AssistantMessageRole.user
    assert history[1].role == AssistantMessageRole.assistant


@pytest.mark.asyncio
async def test_conversation_continuation_restores_voice_session() -> None:
    conv_repo = _ConvRepoMock()
    store = InMemoryVoiceSessionStore(ttl_seconds=3600.0)
    conv = await AssistantConversationService(MagicMock(), conv_repo, _MsgRepoMock()).create_conversation(5)
    session = VoiceDialogueSession(
        user_id=5,
        category_slug="transport-cars",
        known_fields={"city": "Бишкек"},
        flow_stage="publish_preview",
    )
    from app.core.assistant_state_policy import sanitize_assistant_state

    conv.state_json = sanitize_assistant_state(
        {
            "voice_session": voice_session_to_dict(session),
            "assistant_voice_enabled": False,
        },
    )
    svc = AssistantConversationService(MagicMock(), conv_repo, _MsgRepoMock())
    svc.hydrate_voice_session_store(conversation=conv, session_store=store, user_id=5)
    restored = store.get(5)
    assert restored is not None
    assert restored.known_fields.get("city") == "Бишкек"


def test_ui_state_draft_preview() -> None:
    preview = DraftPreview(title="iPhone", description="Продаётся.", category_id=1)
    resp = _voice_resp(draft_preview=preview, publish_confirmation_required=True)
    assert resolve_ui_state(resp) == AssistantUiState.draft_preview


def test_ui_state_promotion_offer() -> None:
    from app.schemas.listing_assistant import PromotionOffer

    resp = _voice_resp(promotion_offer=PromotionOffer(listing_id=10))
    assert resolve_ui_state(resp) == AssistantUiState.promotion_offer


def test_ui_state_moderation() -> None:
    resp = _voice_resp(moderation_required=True, moderation_reason="blocked")
    assert resolve_ui_state(resp) == AssistantUiState.moderation


def test_ui_state_needs_input() -> None:
    resp = _voice_resp(needs_clarification=True, next_question="Какой год?")
    assert resolve_ui_state(resp) == AssistantUiState.needs_input


def test_actions_upload_and_confirm() -> None:
    preview = DraftPreview(title="T", description="D", category_id=1)
    resp = _voice_resp(
        draft_preview=preview,
        publish_confirmation_required=True,
        needs_photos=True,
        real_photo_required=True,
    )
    actions = build_actions(resp)
    types = {a.type.value for a in actions}
    assert "upload_photo" in types
    assert "confirm_publish" in types


@pytest.mark.asyncio
async def test_assistant_service_overlay_text_flow() -> None:
    conv_repo = _ConvRepoMock()
    msg_repo = _MsgRepoMock()
    session = MagicMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()

    conv_svc = AssistantConversationService(session, conv_repo, msg_repo)
    voice = MagicMock()
    voice.handle_command = AsyncMock(
        return_value=_voice_resp(
            needs_clarification=True,
            next_question="В каком городе находится товар?",
            dialogue=VoiceDialogueState(category_slug="electronics-phones"),
        ),
    )
    voice._dialogue = MagicMock()
    voice._dialogue.get_pending_session = MagicMock(return_value=None)

    svc = AssistantService(session, voice, conv_svc, _assistant_voice())
    out = await svc.handle_message(
        AssistantMessageRequest(text="продаю айфон", input_channel="text"),
        _user(),
    )
    assert out.conversation_id == 1
    assert out.ui_state == AssistantUiState.needs_input
    assert len(out.history) >= 2
    voice.handle_command.assert_awaited_once()


@pytest.mark.asyncio
async def test_overlay_voice_channel_message_type() -> None:
    conv_repo = _ConvRepoMock()
    msg_repo = _MsgRepoMock()
    session = MagicMock()
    session.commit = AsyncMock()

    conv_svc = AssistantConversationService(session, conv_repo, msg_repo)
    voice = MagicMock()
    voice.handle_command = AsyncMock(return_value=_voice_resp())
    voice._dialogue = MagicMock(get_pending_session=MagicMock(return_value=None))

    svc = AssistantService(session, voice, conv_svc, _assistant_voice())
    await svc.handle_message(
        AssistantMessageRequest(text="найди iphone", input_channel="voice"),
        _user(),
    )
    user_msgs = [m for m in msg_repo.messages if m.role == AssistantMessageRole.user]
    assert user_msgs[0].message_type == AssistantMessageType.voice


@pytest.mark.asyncio
async def test_assistant_endpoint_integration_mock(client: AsyncClient) -> None:
    voice = MagicMock()
    voice.handle_command = AsyncMock(
        return_value=_voice_resp(
            draft_preview=DraftPreview(title="Camry", description="Продаётся.", category_id=1),
            publish_confirmation_required=True,
        ),
    )
    voice._dialogue = MagicMock(get_pending_session=MagicMock(return_value=None))

    conv_repo = _ConvRepoMock()
    msg_repo = _MsgRepoMock()
    db_session = MagicMock()
    db_session.commit = AsyncMock()

    assistant_svc = AssistantService(
        db_session,
        voice,
        AssistantConversationService(db_session, conv_repo, msg_repo),
        _assistant_voice(),
    )

    fastapi_app.dependency_overrides[get_current_user] = _user
    fastapi_app.dependency_overrides[get_assistant_service] = lambda: assistant_svc
    fastapi_app.dependency_overrides[get_voice_service] = lambda: voice

    r1 = await client.post(
        "/api/v1/assistant/message",
        json={"text": "продаю камри", "input_channel": "text"},
        headers={"Authorization": "Bearer test"},
    )
    assert r1.status_code == 200
    d1 = r1.json()
    assert d1["ui_state"] == "draft_preview"
    assert d1["conversation_id"] == 1

    r2 = await client.post(
        "/api/v1/assistant/message",
        json={
            "text": "Бишкек",
            "conversation_id": d1["conversation_id"],
            "input_channel": "text",
        },
        headers={"Authorization": "Bearer test"},
    )
    assert r2.status_code == 200

    hist = await client.get(
        f"/api/v1/assistant/conversations/{d1['conversation_id']}/messages",
        headers={"Authorization": "Bearer test"},
    )
    assert hist.status_code == 200
    assert len(hist.json()) >= 2


@pytest.mark.asyncio
async def test_voice_endpoint_still_works(client: AsyncClient) -> None:
    from app.services.voice_service import VoiceService
    from app.services.speech_to_text_service import SpeechToTextService

    class _Stt(SpeechToTextService):
        async def transcribe(self, audio_bytes: bytes) -> str:
            return "найди iphone"

    voice = VoiceService(
        MagicMock(),
        MagicMock(),
        _Stt(),
        category_intelligence=None,
        session_store=InMemoryVoiceSessionStore(ttl_seconds=3600.0),
    )
    voice._listings.get_feed = AsyncMock(return_value=[])

    fastapi_app.dependency_overrides[get_current_user] = _user
    fastapi_app.dependency_overrides[get_voice_service] = lambda: voice

    resp = await client.post(
        "/api/v1/voice/command",
        json={"text": "найди iphone"},
        headers={"Authorization": "Bearer test"},
    )
    assert resp.status_code == 200
    assert resp.json()["intent"]["intent"] == "search_listings"
