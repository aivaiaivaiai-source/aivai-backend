from __future__ import annotations

import pytest

from app.core.assistant_state_policy import (
    ASSISTANT_STATE_VERSION,
    FORBIDDEN_STATE_KEYS,
    MAX_ASSISTANT_STATE_BYTES,
    MAX_ASSISTANT_MESSAGE_METADATA_BYTES,
    sanitize_assistant_message_metadata,
    sanitize_assistant_state,
    sanitize_voice_session_dict,
)
from app.services.assistant_conversation_service import AssistantConversationService
from app.services.assistant_overlay_mapper import build_message_metadata
from app.services.voice_session_state import voice_session_from_dict, voice_session_to_dict
from app.services.voice_session_store import VoiceDialogueSession
from app.models.assistant_enums import AssistantUiState
from tests.test_assistant_conversation import (
    _ConvRepoMock,
    _MsgRepoMock,
    _voice_resp,
)
from unittest.mock import MagicMock


def test_state_json_gets_state_version() -> None:
    state = sanitize_assistant_state({"assistant_voice_enabled": True})
    assert state["state_version"] == ASSISTANT_STATE_VERSION
    assert state["assistant_voice_enabled"] is True
    assert state["voice_session"] is None


def test_forbidden_keys_removed_from_state() -> None:
    state = sanitize_assistant_state(
        {
            "history": [{"role": "user", "content": "x"}],
            "messages": ["a", "b"],
            "analytics": {"clicks": 1},
            "embeddings": [0.1, 0.2],
            "audio_blob": b"fake",  # type: ignore[dict-item]
            "assistant_voice_enabled": False,
            "voice_session": None,
        },
    )
    for key in FORBIDDEN_STATE_KEYS:
        assert key not in state
    assert "history" not in state
    assert "messages" not in state


def test_huge_state_raises_error() -> None:
    huge_session = {
        "user_id": 1,
        "seed_text": "x" * 500,
        "known_fields": {f"field_{i}": "y" * 500 for i in range(20)},
        "voice_extracted": {},
        "missing_field_keys": [],
    }
    with pytest.raises(ValueError, match="exceeds"):
        sanitize_assistant_state(
            {
                "assistant_voice_enabled": False,
                "voice_session": huge_session,
            },
        )


def test_voice_session_serialization_is_whitelist_based() -> None:
    session = VoiceDialogueSession(
        user_id=9,
        category_slug="electronics-phones",
        known_fields={"city": "Бишкек"},
        seed_text="продаю айфон",
    )
    data = voice_session_to_dict(session)
    assert "user_id" in data
    assert "category_slug" in data
    assert "history" not in data
    assert "audio" not in data

    polluted = dict(data)
    polluted["history"] = [{"role": "user"}]
    polluted["audio_blob"] = "base64..."
    cleaned = sanitize_voice_session_dict(polluted)
    assert cleaned is not None
    assert "history" not in cleaned
    assert "audio_blob" not in cleaned

    restored = voice_session_from_dict(cleaned, user_id=9)
    assert restored.known_fields.get("city") == "Бишкек"


def test_history_not_stored_in_state_json() -> None:
    state = sanitize_assistant_state(
        {
            "history": [{"id": 1, "content": "hello"}],
            "messages": ["m1", "m2"],
            "voice_session": voice_session_to_dict(
                VoiceDialogueSession(user_id=1, seed_text="test"),
            ),
        },
    )
    assert "history" not in state
    assert "messages" not in state
    assert state["voice_session"] is not None


@pytest.mark.asyncio
async def test_assistant_messages_still_store_history() -> None:
    from app.models.assistant_enums import AssistantMessageRole, AssistantMessageType

    conv_repo = _ConvRepoMock()
    msg_repo = _MsgRepoMock()
    svc = AssistantConversationService(MagicMock(), conv_repo, msg_repo)
    conv = await svc.create_conversation(3)
    assert conv.state_json.get("state_version") == ASSISTANT_STATE_VERSION

    await svc.append_message(
        conversation_id=conv.id,
        role=AssistantMessageRole.user,
        content="продаю айфон",
        message_type=AssistantMessageType.text,
    )
    await svc.append_message(
        conversation_id=conv.id,
        role=AssistantMessageRole.assistant,
        content="В каком городе?",
        message_type=AssistantMessageType.text,
    )
    history = await svc.get_history(conv.id, 3)
    assert len(history) == 2
    assert "history" not in conv_repo.rows[conv.id].state_json


def test_message_metadata_sanitizer_strips_forbidden() -> None:
    meta = build_message_metadata(
        _voice_resp(needs_clarification=True),
        ui_state=AssistantUiState.needs_input,
        actions=[],
        input_channel="text",
    )
    assert "voice_response" not in meta
    assert "history" not in meta
    assert meta["ui_state"] == "needs_input"

    raw = {
        "ui_state": "ready",
        "voice_response": {"message": "x" * 5000},
        "history": [{"role": "user"}],
    }
    cleaned = sanitize_assistant_message_metadata(raw)
    assert "voice_response" not in cleaned
    assert "history" not in cleaned


def test_huge_metadata_raises_error() -> None:
    with pytest.raises(ValueError, match="metadata exceeds"):
        sanitize_assistant_message_metadata(
            {f"field_{i}": "x" * 500 for i in range(40)},
        )


@pytest.mark.asyncio
async def test_conversation_continuation_after_sanitize() -> None:
    from app.services.voice_session_store import InMemoryVoiceSessionStore

    conv_repo = _ConvRepoMock()
    store = InMemoryVoiceSessionStore(ttl_seconds=3600.0)
    conv = await AssistantConversationService(MagicMock(), conv_repo, _MsgRepoMock()).create_conversation(5)
    session = VoiceDialogueSession(
        user_id=5,
        category_slug="transport-cars",
        known_fields={"city": "Бишкек"},
        flow_stage="publish_preview",
    )
    conv.state_json = sanitize_assistant_state(
        {
            "assistant_voice_enabled": False,
            "voice_session": voice_session_to_dict(session),
        },
    )
    svc = AssistantConversationService(MagicMock(), conv_repo, _MsgRepoMock())
    svc.hydrate_voice_session_store(conversation=conv, session_store=store, user_id=5)
    restored = store.get(5)
    assert restored is not None
    assert restored.known_fields.get("city") == "Бишкек"
