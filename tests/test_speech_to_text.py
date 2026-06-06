from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.core.config import Settings
from app.core.exceptions import AppException
from app.services.speech_to_text_service import (
    WhisperSpeechToTextService,
    _classify_openai_error,
    _multipart_file_meta,
)


def _wav_bytes() -> bytes:
    return b"RIFF\x24\x00\x00\x00WAVEfmt "


def test_multipart_file_meta_wav() -> None:
    data = _wav_bytes()
    name, mime = _multipart_file_meta(data)
    assert name == "audio.wav"
    assert mime == "audio/wav"


def test_classify_openai_error_invalid_key() -> None:
    assert _classify_openai_error(401, '{"error":{"message":"invalid"}}') == "invalid_api_key"


def test_classify_openai_error_quota() -> None:
    body = '{"error":{"message":"You exceeded your current quota"}}'
    assert _classify_openai_error(400, body) == "quota_billing"


@pytest.mark.asyncio
async def test_whisper_missing_api_key_raises_502() -> None:
    svc = WhisperSpeechToTextService(Settings(OPENAI_API_KEY=None))
    with pytest.raises(AppException) as exc:
        await svc.transcribe(_wav_bytes())
    assert exc.value.status_code == 502
    assert "временно недоступен" in exc.value.message


@pytest.mark.asyncio
async def test_whisper_blank_api_key_raises_502() -> None:
    svc = WhisperSpeechToTextService(Settings(OPENAI_API_KEY="   "))
    with pytest.raises(AppException) as exc:
        await svc.transcribe(_wav_bytes())
    assert exc.value.status_code == 502


@pytest.mark.asyncio
async def test_whisper_success() -> None:
    svc = WhisperSpeechToTextService(Settings(OPENAI_API_KEY="sk-test"))

    mock_response = MagicMock()
    mock_response.is_error = False
    mock_response.status_code = 200
    mock_response.json.return_value = {"text": " найди квартиру "}

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("app.services.speech_to_text_service.httpx.AsyncClient", return_value=mock_client):
        text = await svc.transcribe(_wav_bytes())

    assert text == "найди квартиру"
    mock_client.post.assert_awaited_once()
    call_kwargs = mock_client.post.await_args.kwargs
    assert call_kwargs["headers"]["Authorization"] == "Bearer sk-test"
    assert call_kwargs["data"] == {"model": "whisper-1"}
    assert "file" in call_kwargs["files"]


@pytest.mark.asyncio
async def test_whisper_api_error_raises_502() -> None:
    svc = WhisperSpeechToTextService(Settings(OPENAI_API_KEY="sk-test"))

    mock_response = MagicMock()
    mock_response.is_error = True
    mock_response.status_code = 401
    mock_response.text = '{"error":{"message":"Incorrect API key"}}'

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("app.services.speech_to_text_service.httpx.AsyncClient", return_value=mock_client):
        with pytest.raises(AppException) as exc:
            await svc.transcribe(_wav_bytes())

    assert exc.value.status_code == 502


@pytest.mark.asyncio
async def test_whisper_timeout_raises_502() -> None:
    svc = WhisperSpeechToTextService(Settings(OPENAI_API_KEY="sk-test"))

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(side_effect=httpx.TimeoutException("timed out"))
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("app.services.speech_to_text_service.httpx.AsyncClient", return_value=mock_client):
        with pytest.raises(AppException) as exc:
            await svc.transcribe(_wav_bytes())

    assert exc.value.status_code == 502


@pytest.mark.asyncio
async def test_whisper_empty_transcript_raises_400() -> None:
    svc = WhisperSpeechToTextService(Settings(OPENAI_API_KEY="sk-test"))

    mock_response = MagicMock()
    mock_response.is_error = False
    mock_response.status_code = 200
    mock_response.json.return_value = {"text": "   "}

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("app.services.speech_to_text_service.httpx.AsyncClient", return_value=mock_client):
        with pytest.raises(AppException) as exc:
            await svc.transcribe(_wav_bytes())

    assert exc.value.status_code == 400
    assert "Не удалось распознать речь" in exc.value.message
