"""Speech-to-text abstraction and OpenAI Whisper implementation."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod

import httpx

from app.core.config import Settings
from app.core.exceptions import AppException

logger = logging.getLogger(__name__)

_UNAVAILABLE = "Сервис распознавания речи временно недоступен"


def _multipart_file_meta(audio_bytes: bytes) -> tuple[str, str]:
    """Infer filename and mime type for Whisper multipart upload."""
    if len(audio_bytes) >= 12 and audio_bytes.startswith(b"RIFF") and audio_bytes[8:12] == b"WAVE":
        return "audio.wav", "audio/wav"
    if audio_bytes.startswith(b"ID3") or audio_bytes[:2] in (b"\xff\xfb", b"\xff\xfa", b"\xff\xf3", b"\xff\xf2"):
        return "audio.mp3", "audio/mpeg"
    if len(audio_bytes) >= 8 and audio_bytes[4:8] == b"ftyp":
        return "audio.m4a", "audio/mp4"
    return "audio.bin", "application/octet-stream"


def _truncate(text: str, limit: int = 500) -> str:
    text = text.strip()
    if len(text) <= limit:
        return text
    return f"{text[:limit]}..."


def _classify_openai_error(status_code: int, body: str) -> str:
    body_l = body.lower()
    if status_code == 401:
        return "invalid_api_key"
    if status_code == 403:
        return "forbidden"
    if status_code == 429:
        return "rate_limit_or_quota"
    if status_code >= 500:
        return "openai_server_error"
    if "insufficient_quota" in body_l or "billing" in body_l or "exceeded your current quota" in body_l:
        return "quota_billing"
    return "api_error"


class SpeechToTextService(ABC):
    @abstractmethod
    async def transcribe(self, audio_bytes: bytes) -> str:
        """Return non-empty trimmed transcript text or raise AppException."""
        ...


class WhisperSpeechToTextService(SpeechToTextService):
    _TRANSCRIPTION_URL = "https://api.openai.com/v1/audio/transcriptions"

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def transcribe(self, audio_bytes: bytes) -> str:
        if not audio_bytes:
            raise AppException("Не удалось распознать речь", status_code=400)

        key = self._settings.OPENAI_API_KEY
        if not key or not key.strip():
            logger.error("whisper_unavailable reason=api_key_not_configured")
            raise AppException(_UNAVAILABLE, status_code=502)

        filename, mime_type = _multipart_file_meta(audio_bytes)
        files = {"file": (filename, audio_bytes, mime_type)}
        data = {"model": "whisper-1"}

        logger.info(
            "whisper_request bytes=%d filename=%s mime=%s",
            len(audio_bytes),
            filename,
            mime_type,
        )

        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(120.0, connect=10.0)) as client:
                response = await client.post(
                    self._TRANSCRIPTION_URL,
                    headers={"Authorization": f"Bearer {key.strip()}"},
                    data=data,
                    files=files,
                )
        except httpx.TimeoutException as exc:
            logger.error("whisper_unavailable reason=timeout detail=%s", exc)
            raise AppException(_UNAVAILABLE, status_code=502) from None
        except httpx.ConnectError as exc:
            logger.error("whisper_unavailable reason=network_connect detail=%s", exc)
            raise AppException(_UNAVAILABLE, status_code=502) from None
        except httpx.HTTPError as exc:
            logger.error(
                "whisper_unavailable reason=http_error type=%s detail=%s",
                exc.__class__.__name__,
                exc,
            )
            raise AppException(_UNAVAILABLE, status_code=502) from None

        if response.is_error:
            body = response.text
            reason = _classify_openai_error(response.status_code, body)
            logger.error(
                "whisper_unavailable reason=%s status=%s body=%s",
                reason,
                response.status_code,
                _truncate(body),
            )
            raise AppException(_UNAVAILABLE, status_code=502)

        try:
            payload = response.json()
        except ValueError:
            logger.error(
                "whisper_unavailable reason=json_parse_error status=%s body=%s",
                response.status_code,
                _truncate(response.text),
            )
            raise AppException(_UNAVAILABLE, status_code=502)

        raw = payload.get("text")
        text = raw.strip() if isinstance(raw, str) else ""
        if not text:
            logger.warning(
                "whisper_empty_transcript status=%s payload_keys=%s",
                response.status_code,
                list(payload.keys()) if isinstance(payload, dict) else type(payload).__name__,
            )
            raise AppException("Не удалось распознать речь", status_code=400)

        logger.info("whisper_ok transcript_chars=%d", len(text))
        return text

