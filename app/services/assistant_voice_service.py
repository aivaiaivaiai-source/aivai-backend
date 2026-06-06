from __future__ import annotations

import logging

from app.schemas.assistant import AssistantVoiceResponse
from app.services.text_to_speech_service import TextToSpeechService
from app.services.tts_audio_storage import TtsAudioStorage
from app.services.tts_message import prepare_tts_message

logger = logging.getLogger(__name__)


class AssistantVoiceService:
    """Build overlay-ready TTS payloads; never raises — text flow always continues."""

    def __init__(
        self,
        tts: TextToSpeechService,
        storage: TtsAudioStorage,
    ) -> None:
        self._tts = tts
        self._storage = storage

    async def build_voice_response(
        self,
        message: str,
        *,
        enabled: bool,
    ) -> AssistantVoiceResponse:
        if not enabled:
            return AssistantVoiceResponse(enabled=False)

        tts_text = prepare_tts_message(message)
        if not tts_text:
            return AssistantVoiceResponse(enabled=False)

        result = await self._tts.synthesize(tts_text)
        if result is None:
            logger.info("tts_fallback text_only chars=%d", len(message))
            return AssistantVoiceResponse(enabled=False, tts_text=tts_text)

        try:
            audio_url = self._storage.save_mp3(result.audio_bytes)
        except OSError as exc:
            logger.warning("tts_fallback reason=storage_error detail=%s", exc)
            return AssistantVoiceResponse(enabled=False, tts_text=tts_text)

        return AssistantVoiceResponse(
            enabled=True,
            audio_url=audio_url,
            provider=result.provider,
            duration_ms=result.duration_ms,
            tts_text=tts_text,
        )
