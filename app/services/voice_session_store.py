from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


@dataclass
class VoiceDialogueSession:
    """Multi-step voice dialogue state (per user)."""

    user_id: int
    conversation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    intent_name: str = "create_listing"
    seed_text: str = ""
    category_id: int | None = None
    category_slug: str | None = None
    category_name: str | None = None
    known_fields: dict[str, Any] = field(default_factory=dict)
    missing_field_keys: list[str] = field(default_factory=list)
    awaiting_field_key: str | None = None
    last_question: str | None = None
    voice_extracted: dict[str, Any] = field(default_factory=dict)
    moderation_action: str = "allow"
    moderation_reason: str | None = None
    flow_stage: str = "collecting"
    generated_title: str | None = None
    generated_description: str | None = None
    listing_id: int | None = None
    photos_reminder_shown: bool = False
    photos_acknowledged: bool = False
    real_photo_count: int = 0
    created_at: float = field(default_factory=time.monotonic)
    updated_at: float = field(default_factory=time.monotonic)


@runtime_checkable
class VoiceSessionStoreProtocol(Protocol):
    def get(self, user_id: int) -> VoiceDialogueSession | None: ...

    def save(self, session: VoiceDialogueSession) -> None: ...

    def clear(self, user_id: int) -> None: ...


class InMemoryVoiceSessionStore:
    """Process-local pending voice sessions with idle TTL (Redis-ready adapter later)."""

    def __init__(self, *, ttl_seconds: float = 1800.0) -> None:
        self._ttl = ttl_seconds
        self._sessions: dict[int, VoiceDialogueSession] = {}

    def get(self, user_id: int) -> VoiceDialogueSession | None:
        self._evict_expired()
        session = self._sessions.get(user_id)
        if session is None:
            return None
        if time.monotonic() - session.updated_at > self._ttl:
            del self._sessions[user_id]
            return None
        return session

    def save(self, session: VoiceDialogueSession) -> None:
        session.updated_at = time.monotonic()
        self._sessions[session.user_id] = session

    def clear(self, user_id: int) -> None:
        self._sessions.pop(user_id, None)

    def _evict_expired(self) -> None:
        now = time.monotonic()
        expired = [uid for uid, s in self._sessions.items() if now - s.updated_at > self._ttl]
        for uid in expired:
            del self._sessions[uid]


# Backward-compatible alias + shared instance for app lifetime.
VoiceSessionStore = InMemoryVoiceSessionStore
pending_voice_sessions: InMemoryVoiceSessionStore = InMemoryVoiceSessionStore()
