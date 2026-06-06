from __future__ import annotations

import json
from dataclasses import fields
from typing import Any

from app.services.voice_session_store import VoiceDialogueSession

ASSISTANT_STATE_VERSION = 1

# Compact dialogue state only; history lives in assistant_messages.
MAX_ASSISTANT_STATE_BYTES = 8_192
MAX_ASSISTANT_MESSAGE_METADATA_BYTES = 16_384

MAX_VOICE_SESSION_STRING_LENGTH = 2_000
MAX_VOICE_SESSION_NESTED_STRING_LENGTH = 500
MAX_VOICE_SESSION_NESTED_KEYS = 40

FORBIDDEN_STATE_KEYS = frozenset(
    {
        "history",
        "messages",
        "analytics",
        "embeddings",
        "audio",
        "audio_blob",
        "tts_cache",
        "voice_audio",
        "files",
        "images",
        "voice_response",
        "binary",
        "blob",
        "payload",
    },
)

ALLOWED_STATE_ROOT_KEYS = frozenset(
    {
        "state_version",
        "assistant_voice_enabled",
        "voice_session",
        "ui_context",
    },
)

ALLOWED_UI_CONTEXT_KEYS = frozenset(
    {
        "last_ui_state",
        "last_input_channel",
        "overlay_visible",
    },
)

VOICE_SESSION_ALLOWED_FIELDS = frozenset(f.name for f in fields(VoiceDialogueSession))

FORBIDDEN_METADATA_KEYS = frozenset(
    FORBIDDEN_STATE_KEYS
    | {
        "voice_response",
        "history",
        "raw_response",
    },
)


def _json_utf8_size(payload: dict[str, Any]) -> int:
    return len(json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))


def _cap_string(value: Any, *, max_len: int) -> str | None:
    if value is None:
        return None
    text = str(value)
    if len(text) > max_len:
        raise ValueError(
            f"assistant state string exceeds {max_len} characters ({len(text)} chars)",
        )
    return text


def _sanitize_scalar_map(
    raw: Any,
    *,
    max_keys: int = MAX_VOICE_SESSION_NESTED_KEYS,
    max_value_len: int = MAX_VOICE_SESSION_NESTED_STRING_LENGTH,
) -> dict[str, Any]:
    if not isinstance(raw, dict):
        return {}
    cleaned: dict[str, Any] = {}
    for key, value in list(raw.items())[:max_keys]:
        if not isinstance(key, str) or key in FORBIDDEN_STATE_KEYS:
            continue
        if isinstance(value, (str, int, float, bool)) or value is None:
            if isinstance(value, str):
                cleaned[key] = _cap_string(value, max_len=max_value_len)
            else:
                cleaned[key] = value
    return cleaned


def sanitize_voice_session_dict(data: dict[str, Any] | None) -> dict[str, Any] | None:
    """Whitelist VoiceDialogueSession fields; reject oversized strings."""
    if data is None:
        return None
    if not isinstance(data, dict):
        return None

    cleaned: dict[str, Any] = {}
    for key, value in data.items():
        if key in FORBIDDEN_STATE_KEYS or key not in VOICE_SESSION_ALLOWED_FIELDS:
            continue
        if key in ("known_fields", "voice_extracted"):
            cleaned[key] = _sanitize_scalar_map(value)
        elif key == "missing_field_keys":
            if isinstance(value, list):
                cleaned[key] = [
                    _cap_string(item, max_len=128)
                    for item in value[:MAX_VOICE_SESSION_NESTED_KEYS]
                    if item is not None
                ]
        elif isinstance(value, str) or value is None:
            cleaned[key] = _cap_string(value, max_len=MAX_VOICE_SESSION_STRING_LENGTH)
        elif isinstance(value, (int, float, bool)):
            cleaned[key] = value
        elif key in ("category_id", "listing_id", "real_photo_count", "user_id") and value is not None:
            cleaned[key] = int(value)

    return cleaned or None


def _sanitize_ui_context(raw: Any) -> dict[str, Any] | None:
    if not isinstance(raw, dict):
        return None
    cleaned: dict[str, Any] = {}
    for key, value in raw.items():
        if key not in ALLOWED_UI_CONTEXT_KEYS or key in FORBIDDEN_STATE_KEYS:
            continue
        if isinstance(value, bool):
            cleaned[key] = value
        elif isinstance(value, (int, float)):
            cleaned[key] = value
        elif isinstance(value, str):
            cleaned[key] = _cap_string(value, max_len=128)
    return cleaned or None


def sanitize_assistant_state(state: dict[str, Any] | None) -> dict[str, Any]:
    """Keep state_json minimal: voice_session, flags, version. Raise if still too large."""
    raw = dict(state or {})

    cleaned: dict[str, Any] = {
        "assistant_voice_enabled": bool(raw.get("assistant_voice_enabled", False)),
        "voice_session": sanitize_voice_session_dict(raw.get("voice_session")),
        "state_version": ASSISTANT_STATE_VERSION,
    }

    ui_context = _sanitize_ui_context(raw.get("ui_context"))
    if ui_context:
        cleaned["ui_context"] = ui_context

    size = _json_utf8_size(cleaned)
    if size > MAX_ASSISTANT_STATE_BYTES:
        raise ValueError(
            f"assistant state_json exceeds {MAX_ASSISTANT_STATE_BYTES} bytes "
            f"({size} bytes after sanitization)",
        )
    return cleaned


def sanitize_assistant_message_metadata(metadata: dict[str, Any] | None) -> dict[str, Any]:
    """Lightweight overlay metadata only; no full voice_response or history."""
    if not metadata:
        return {}

    cleaned: dict[str, Any] = {}
    for key, value in metadata.items():
        if key in FORBIDDEN_METADATA_KEYS:
            continue
        if key == "actions" and isinstance(value, list):
            cleaned[key] = value[:20]
        elif key in ("draft_preview", "promotion_offer") and isinstance(value, dict):
            cleaned[key] = value
        elif key == "voice_data" and isinstance(value, dict):
            cleaned[key] = _sanitize_scalar_map(value, max_keys=20)
        elif key in ("tts_audio_url",) and isinstance(value, str):
            cleaned[key] = _cap_string(value, max_len=256)
        elif key in ("tts_provider",) and isinstance(value, str):
            cleaned[key] = _cap_string(value, max_len=32)
        elif key in ("tts_duration_ms", "voice_enabled") and isinstance(value, (int, float, bool)):
            cleaned[key] = value
        elif isinstance(value, (str, int, float, bool)) or value is None:
            if isinstance(value, str):
                cleaned[key] = _cap_string(value, max_len=500)
            else:
                cleaned[key] = value
        elif isinstance(value, list) and key == "actions":
            cleaned[key] = value[:20]

    size = _json_utf8_size(cleaned)
    if size > MAX_ASSISTANT_MESSAGE_METADATA_BYTES:
        raise ValueError(
            f"assistant message metadata exceeds {MAX_ASSISTANT_MESSAGE_METADATA_BYTES} bytes "
            f"({size} bytes after sanitization)",
        )
    return cleaned


def empty_assistant_state() -> dict[str, Any]:
    return sanitize_assistant_state(
        {"assistant_voice_enabled": False, "voice_session": None},
    )
