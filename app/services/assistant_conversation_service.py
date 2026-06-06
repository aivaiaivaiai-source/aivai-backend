from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.assistant_state_policy import empty_assistant_state, sanitize_assistant_message_metadata, sanitize_assistant_state
from app.core.exceptions import EntityNotFoundError, OwnershipError
from app.models.assistant_conversation import AssistantConversation
from app.models.assistant_enums import (
    AssistantConversationStatus,
    AssistantMessageRole,
    AssistantMessageType,
)
from app.models.assistant_message import AssistantMessage
from app.repositories.assistant_conversation_repository import AssistantConversationRepository
from app.repositories.assistant_message_repository import AssistantMessageRepository
from app.schemas.assistant import AssistantConversationRead, AssistantMessageRead
from app.services.voice_session_state import voice_session_from_dict, voice_session_to_dict
from app.services.voice_session_store import VoiceDialogueSession, VoiceSessionStoreProtocol


class AssistantConversationService:
    def __init__(
        self,
        session: AsyncSession,
        conversation_repository: AssistantConversationRepository,
        message_repository: AssistantMessageRepository,
    ) -> None:
        self._session = session
        self._conversations = conversation_repository
        self._messages = message_repository

    async def create_conversation(self, user_id: int) -> AssistantConversation:
        row = AssistantConversation(
            user_id=user_id,
            status=AssistantConversationStatus.active,
            state_json=empty_assistant_state(),
            last_activity_at=datetime.now(UTC),
        )
        return await self._conversations.create(row)

    async def get_conversation_for_user(
        self,
        conversation_id: int,
        user_id: int,
    ) -> AssistantConversation:
        row = await self._conversations.get_for_user(conversation_id, user_id)
        if row is None:
            raise EntityNotFoundError("AssistantConversation", entity_id=conversation_id)
        return row

    async def get_or_create(
        self,
        user_id: int,
        conversation_id: int | None,
    ) -> AssistantConversation:
        if conversation_id is None:
            return await self.create_conversation(user_id)
        row = await self.get_conversation_for_user(conversation_id, user_id)
        if row.status == AssistantConversationStatus.closed:
            raise OwnershipError("This assistant conversation is closed.")
        return row

    async def append_message(
        self,
        *,
        conversation_id: int,
        role: AssistantMessageRole,
        content: str,
        message_type: AssistantMessageType,
        metadata: dict[str, Any] | None = None,
    ) -> AssistantMessage:
        msg = AssistantMessage(
            conversation_id=conversation_id,
            role=role,
            content=content,
            message_type=message_type,
            metadata_json=sanitize_assistant_message_metadata(metadata),
        )
        created = await self._messages.create(msg)
        await self._conversations.touch_activity(conversation_id)
        return created

    async def get_history(
        self,
        conversation_id: int,
        user_id: int,
        *,
        limit: int = 50,
    ) -> list[AssistantMessageRead]:
        await self.get_conversation_for_user(conversation_id, user_id)
        rows = await self._messages.list_for_conversation(
            conversation_id,
            limit=limit,
        )
        return [AssistantMessageRead.model_validate(r) for r in rows]

    async def update_state(
        self,
        conversation_id: int,
        state: dict[str, Any],
    ) -> None:
        await self._conversations.update(
            conversation_id,
            state_json=sanitize_assistant_state(state),
        )

    def load_voice_session(
        self,
        conversation: AssistantConversation,
        *,
        user_id: int,
    ) -> VoiceDialogueSession | None:
        raw = conversation.state_json.get("voice_session")
        if not isinstance(raw, dict):
            return None
        return voice_session_from_dict(raw, user_id=user_id)

    def persist_voice_session(
        self,
        conversation: AssistantConversation,
        session: VoiceDialogueSession | None,
        *,
        session_store: VoiceSessionStoreProtocol,
        user_id: int,
    ) -> dict[str, Any]:
        state = dict(conversation.state_json or {})
        if session is not None:
            state["voice_session"] = voice_session_to_dict(session)
            session_store.save(session)
        else:
            state["voice_session"] = None
            session_store.clear(user_id)
        state.setdefault("assistant_voice_enabled", False)
        return sanitize_assistant_state(state)

    def hydrate_voice_session_store(
        self,
        *,
        conversation: AssistantConversation,
        session_store: VoiceSessionStoreProtocol,
        user_id: int,
    ) -> None:
        restored = self.load_voice_session(conversation, user_id=user_id)
        if restored is not None:
            session_store.save(restored)
        else:
            session_store.clear(user_id)

    def is_voice_enabled(self, conversation: AssistantConversation) -> bool:
        return bool(conversation.state_json.get("assistant_voice_enabled", False))

    async def clear_conversation(self, conversation_id: int, user_id: int) -> None:
        await self.get_conversation_for_user(conversation_id, user_id)
        await self._conversations.close(conversation_id)
        await self._conversations.update(
            conversation_id,
            state_json=empty_assistant_state(),
        )

    async def to_conversation_read(self, row: AssistantConversation) -> AssistantConversationRead:
        return AssistantConversationRead(
            id=row.id,
            user_id=row.user_id,
            status=row.status.value,
            last_activity_at=row.last_activity_at,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )
