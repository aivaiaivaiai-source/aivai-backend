from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from httpx import AsyncClient

from app.api.deps import get_current_user, get_voice_service
from app.main import app as fastapi_app
from app.schemas.user import UserRead
from app.services.speech_to_text_service import SpeechToTextService


class _ListingStub:
    async def create_listing(self, *_a, **_k):
        raise AssertionError("create_listing should not be called for this test")

    async def get_feed(self, **_k):
        raise AssertionError("get_feed should not be called for this test")


class _SavedStub:
    async def create_saved_search(self, *_a, **_k):
        raise AssertionError("create_saved_search should not be called for this test")


class _UnusedSttStub(SpeechToTextService):
    async def transcribe(self, audio_bytes: bytes) -> str:
        raise AssertionError("STT should not be called for this test")


def _stub_user() -> UserRead:
    now = datetime.now(UTC)
    return UserRead(
        id=1,
        phone="+70000000000",
        full_name="Voice Tester",
        is_active=True,
        balance=Decimal("0"),
        last_login=None,
        created_at=now,
        updated_at=now,
    )


@pytest.mark.asyncio
async def test_voice_command_whitespace_only_returns_400(client: AsyncClient) -> None:
    from app.services.voice_service import VoiceService

    fastapi_app.dependency_overrides[get_current_user] = _stub_user
    fastapi_app.dependency_overrides[get_voice_service] = lambda: VoiceService(
        _ListingStub(),
        _SavedStub(),
        _UnusedSttStub(),
    )

    resp = await client.post("/api/v1/voice/command", json={"text": "   \t"})
    assert resp.status_code == 400
    body = resp.json()
    assert body["status"] == 400
    assert "Некорректная длина текста" in body["detail"]


@pytest.mark.asyncio
async def test_voice_command_too_long_returns_400(client: AsyncClient) -> None:
    from app.services.voice_service import VoiceService

    fastapi_app.dependency_overrides[get_current_user] = _stub_user
    fastapi_app.dependency_overrides[get_voice_service] = lambda: VoiceService(
        _ListingStub(),
        _SavedStub(),
        _UnusedSttStub(),
    )

    resp = await client.post("/api/v1/voice/command", json={"text": "x" * 1001})
    assert resp.status_code == 400
    assert "Некорректная длина текста" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_voice_command_unknown_intent(client: AsyncClient) -> None:
    from app.services.voice_service import VoiceService

    fastapi_app.dependency_overrides[get_current_user] = _stub_user
    fastapi_app.dependency_overrides[get_voice_service] = lambda: VoiceService(
        _ListingStub(),
        _SavedStub(),
        _UnusedSttStub(),
    )

    resp = await client.post("/api/v1/voice/command", json={"text": "просто какой-то текст без команд"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["intent"]["intent"] == "unknown"
    assert data["data"] is None


@pytest.mark.asyncio
async def test_voice_audio_disallowed_extension_returns_400(client: AsyncClient) -> None:
    from app.services.voice_service import VoiceService

    fastapi_app.dependency_overrides[get_current_user] = _stub_user
    fastapi_app.dependency_overrides[get_voice_service] = lambda: VoiceService(
        _ListingStub(),
        _SavedStub(),
        _UnusedSttStub(),
    )

    files = {"file": ("clip.bin", b"deadbeef", "application/octet-stream")}
    resp = await client.post("/api/v1/voice/audio", files=files)
    assert resp.status_code == 400
    assert "wav" in resp.json()["detail"].lower()
