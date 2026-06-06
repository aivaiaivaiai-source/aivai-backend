from __future__ import annotations

import uuid
from pathlib import Path

from app.core.config import Settings


class TtsAudioStorage:
    """Temporary TTS files under MEDIA_ROOT/tts (served via static /media/)."""

    def __init__(self, settings: Settings) -> None:
        self._root = Path(settings.MEDIA_ROOT).resolve() / "tts"
        base = settings.MEDIA_URL
        if not base.endswith("/"):
            base = f"{base}/"
        self._url_prefix = f"{base}tts/"

    def save_mp3(self, audio_bytes: bytes) -> str:
        self._root.mkdir(parents=True, exist_ok=True)
        filename = f"{uuid.uuid4()}.mp3"
        path = self._root / filename
        path.write_bytes(audio_bytes)
        return f"{self._url_prefix}{filename}"
