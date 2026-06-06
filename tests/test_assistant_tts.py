from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import AsyncClient

from app.api.deps import get_assistant_service, get_current_user, get_voice_service
from app.main import app as fastapi_app
from app.models.assistant_enums import AssistantUiState
from app.schemas.assistant import AssistantMessageRequest, AssistantVoiceResponse
from app.schemas.listing_assistant import DraftPreview
from app.schemas.user import UserRead
from app.schemas.voice import VoiceCommandResponse, VoiceIntent
from app.services.assistant_service import AssistantService
from app.services.assistant_voice_service import AssistantVoiceService
from app.services.text_to_speech_service import TTSResult
from app.services.tts_message import MAX_TTS_MESSAGE_LENGTH, prepare_tts_message
from app.core.assistant_state_policy import sanitize_assistant_state
from tests.test_assistant_conversation import (
    _ConvRepoMock,
    _MsgRepoMock,
    _user,
    _voice_resp,
)


class _TtsMock:
    def __init__(self, *, result: TTSResult | None = None) -> None:
        self.result = result
        self.calls: list[str] = []

    async def synthesize(self, text: str) -> TTSResult | None:
        self.calls.append(text)
        return self.result


class _StorageMock:
    def __init__(self) -> None:
        self.saved: list[bytes] = []

    def save_mp3(self, audio_bytes: bytes) -> str:
        self.saved.append(audio_bytes)
        return "/media/tts/test-audio.mp3"


def test_prepare_tts_message_shortens_long_text() -> None:
    long_text = (
        "Я подготовил черновик объявления. "
        "Добавьте фотографии товара перед публикацией. "
        + "Подробное описание " * 40
    )
    short = prepare_tts_message(long_text)
    assert len(short) <= MAX_TTS_MESSAGE_LENGTH
    assert "черновик" in short.lower() or "фото" in short.lower()


@pytest.mark.asyncio
async def test_assistant_returns_audio_url() -> None:
    tts = _TtsMock(
        result=TTSResult(audio_bytes=b"\xff\xfb" + b"x" * 200, provider="openai", duration_ms=1500),
    )
    voice_svc = AssistantVoiceService(tts, _StorageMock())
    out = await voice_svc.build_voice_response("В каком городе находится товар?", enabled=True)
    assert out.enabled is True
    assert out.audio_url == "/media/tts/test-audio.mp3"
    assert out.provider == "openai"
    assert out.duration_ms == 1500


@pytest.mark.asyncio
async def test_tts_failure_fallback_text_only() -> None:
    voice_svc = AssistantVoiceService(_TtsMock(result=None), _StorageMock())
    out = await voice_svc.build_voice_response("Привет", enabled=True)
    assert out.enabled is False
    assert out.audio_url is None


@pytest.mark.asyncio
async def test_no_api_key_text_only() -> None:
    from app.services.text_to_speech_service import OpenAITTSService
    from app.core.config import Settings

    settings = Settings(OPENAI_API_KEY=None)
    tts = OpenAITTSService(settings)
    assert await tts.synthesize("Тест") is None


@pytest.mark.asyncio
async def test_assistant_service_text_and_voice_response() -> None:
    conv_repo = _ConvRepoMock()
    msg_repo = _MsgRepoMock()
    session = MagicMock()
    session.commit = AsyncMock()

    tts = _TtsMock(
        result=TTSResult(audio_bytes=b"mp3data", provider="openai", duration_ms=900),
    )
    assistant_voice = AssistantVoiceService(tts, _StorageMock())

    voice = MagicMock()
    voice.handle_command = AsyncMock(return_value=_voice_resp())
    voice._dialogue = MagicMock(get_pending_session=MagicMock(return_value=None))

    from app.services.assistant_conversation_service import AssistantConversationService

    conv_svc = AssistantConversationService(session, conv_repo, msg_repo)
    svc = AssistantService(session, voice, conv_svc, assistant_voice)

    out = await svc.handle_message(
        AssistantMessageRequest(text="продаю айфон", input_channel="voice"),
        _user(),
    )
    assert out.message
    assert out.voice_response is not None
    assert out.voice_response.enabled is True
    assert out.voice_response.audio_url == "/media/tts/test-audio.mp3"
    assert out.voice_command is not None
    assert "history" not in conv_repo.rows[1].state_json


@pytest.mark.asyncio
async def test_voice_disabled_skips_tts() -> None:
    tts = _TtsMock(
        result=TTSResult(audio_bytes=b"x", provider="openai", duration_ms=100),
    )
    assistant_voice = AssistantVoiceService(tts, _StorageMock())
    voice = MagicMock()
    voice.handle_command = AsyncMock(return_value=_voice_resp())
    voice._dialogue = MagicMock(get_pending_session=MagicMock(return_value=None))
    session = MagicMock()
    session.commit = AsyncMock()

    from app.services.assistant_conversation_service import AssistantConversationService

    svc = AssistantService(
        session,
        voice,
        AssistantConversationService(session, _ConvRepoMock(), _MsgRepoMock()),
        assistant_voice,
    )
    out = await svc.handle_message(
        AssistantMessageRequest(
            text="найди iphone",
            input_channel="text",
            assistant_voice_enabled=False,
        ),
        _user(),
    )
    assert out.message
    assert out.voice_response is not None
    assert out.voice_response.enabled is False
    assert len(tts.calls) == 0


@pytest.mark.asyncio
async def test_assistant_history_still_works_with_tts() -> None:
    conv_repo = _ConvRepoMock()
    msg_repo = _MsgRepoMock()
    session = MagicMock()
    session.commit = AsyncMock()
    assistant_voice = AssistantVoiceService(_TtsMock(result=None), _StorageMock())
    voice = MagicMock()
    voice.handle_command = AsyncMock(return_value=_voice_resp())
    voice._dialogue = MagicMock(get_pending_session=MagicMock(return_value=None))

    from app.services.assistant_conversation_service import AssistantConversationService

    svc = AssistantService(
        session,
        voice,
        AssistantConversationService(session, conv_repo, msg_repo),
        assistant_voice,
    )
    await svc.handle_message(
        AssistantMessageRequest(text="продаю", input_channel="text"),
        _user(),
    )
    history = await svc.get_conversation_history(1, 77)
    assert len(history) == 2


def test_audio_not_in_state_json() -> None:
    state = sanitize_assistant_state(
        {
            "assistant_voice_enabled": True,
            "audio": "base64",
            "audio_blob": "xxx",
            "voice_session": None,
        },
    )
    assert "audio" not in state
    assert "audio_blob" not in state


@pytest.mark.asyncio
async def test_assistant_endpoint_voice_response_field(client: AsyncClient) -> None:
    tts = _TtsMock(
        result=TTSResult(audio_bytes=b"audio", provider="openai", duration_ms=1200),
    )
    storage = _StorageMock()
    assistant_voice = AssistantVoiceService(tts, storage)

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

    from app.services.assistant_conversation_service import AssistantConversationService

    assistant_svc = AssistantService(
        db_session,
        voice,
        AssistantConversationService(db_session, conv_repo, msg_repo),
        assistant_voice,
    )

    fastapi_app.dependency_overrides[get_current_user] = _user
    fastapi_app.dependency_overrides[get_assistant_service] = lambda: assistant_svc
    fastapi_app.dependency_overrides[get_voice_service] = lambda: voice

    resp = await client.post(
        "/api/v1/assistant/message",
        json={"text": "продаю камри", "input_channel": "voice"},
        headers={"Authorization": "Bearer test"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["message"]
    assert data["voice_response"]["enabled"] is True
    assert data["voice_response"]["audio_url"] == "/media/tts/test-audio.mp3"
    assert data["voice_command"]["intent"]["intent"] == "create_listing"


@pytest.mark.asyncio
async def test_voice_audio_endpoint_still_works(client: AsyncClient) -> None:
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
