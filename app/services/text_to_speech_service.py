"""Text-to-speech abstraction and OpenAI TTS implementation (non-blocking fallback)."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass

import httpx

from app.core.config import Settings

logger = logging.getLogger(__name__)

OPENAI_TTS_PROVIDER = "openai"
OPENAI_TTS_MODEL = "tts-1"
OPENAI_TTS_VOICE = "nova"
OPENAI_TTS_URL = "https://api.openai.com/v1/audio/speech"
MP3_BYTES_PER_SECOND_ESTIMATE = 16_000


@dataclass(frozen=True)
class TTSResult:
    audio_bytes: bytes
    provider: str
    duration_ms: int


def estimate_mp3_duration_ms(audio_bytes: bytes) -> int:
    if not audio_bytes:
        return 0
    seconds = max(1, len(audio_bytes) / MP3_BYTES_PER_SECOND_ESTIMATE)
    return int(seconds * 1000)


class TextToSpeechService(ABC):
    @abstractmethod
    async def synthesize(self, text: str) -> TTSResult | None:
        """Return audio bytes or None on any failure (caller keeps text-only flow)."""
        ...


class OpenAITTSService(TextToSpeechService):
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def synthesize(self, text: str) -> TTSResult | None:
        spoken = text.strip()
        if not spoken:
            return None

        key = self._settings.OPENAI_API_KEY
        if not key or not key.strip():
            logger.info("tts_skipped reason=api_key_not_configured")
            return None

        payload = {
            "model": OPENAI_TTS_MODEL,
            "input": spoken,
            "voice": OPENAI_TTS_VOICE,
            "response_format": "mp3",
        }

        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(60.0, connect=10.0)) as client:
                response = await client.post(
                    OPENAI_TTS_URL,
                    headers={
                        "Authorization": f"Bearer {key.strip()}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )
        except httpx.TimeoutException:
            logger.warning("tts_unavailable reason=timeout")
            return None
        except httpx.HTTPError as exc:
            logger.warning("tts_unavailable reason=http_error detail=%s", exc)
            return None

        if response.is_error:
            logger.warning(
                "tts_unavailable reason=api_error status=%s",
                response.status_code,
            )
            return None

        audio = response.content
        if not audio:
            logger.warning("tts_unavailable reason=empty_audio")
            return None

        duration_ms = estimate_mp3_duration_ms(audio)
        logger.info("tts_ok provider=%s bytes=%d duration_ms=%d", OPENAI_TTS_PROVIDER, len(audio), duration_ms)
        return TTSResult(
            audio_bytes=audio,
            provider=OPENAI_TTS_PROVIDER,
            duration_ms=duration_ms,
        )


class NullTextToSpeechService(TextToSpeechService):
    async def synthesize(self, text: str) -> TTSResult | None:
        return None
