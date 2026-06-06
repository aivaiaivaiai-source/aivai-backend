from __future__ import annotations

from typing import Any

from app.core.assistant_state_policy import (
    VOICE_SESSION_ALLOWED_FIELDS,
    sanitize_voice_session_dict,
)
from app.services.voice_session_store import VoiceDialogueSession


def voice_session_to_dict(session: VoiceDialogueSession) -> dict[str, Any]:
    """Serialize only whitelisted VoiceDialogueSession fields (no history/audio blobs)."""
    payload: dict[str, Any] = {}
    for name in VOICE_SESSION_ALLOWED_FIELDS:
        value = getattr(session, name)
        payload[name] = value
    sanitized = sanitize_voice_session_dict(payload)
    if sanitized is None:
        raise ValueError("voice session serialization produced empty payload")
    return sanitized


def voice_session_from_dict(data: dict[str, Any], *, user_id: int) -> VoiceDialogueSession:
    raw = sanitize_voice_session_dict(data) or {}
    payload = {k: v for k, v in raw.items() if k in VOICE_SESSION_ALLOWED_FIELDS}
    payload["user_id"] = user_id
    return VoiceDialogueSession(**payload)
