from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException, TransactionFailedError
from app.models.assistant_enums import AssistantMessageRole, AssistantMessageType
from app.repositories.assistant_conversation_repository import AssistantConversationRepository
from app.repositories.assistant_message_repository import AssistantMessageRepository
from app.schemas.assistant import AssistantMessageRead, AssistantMessageRequest, AssistantMessageResponse
from app.schemas.user import UserRead
from app.schemas.voice import VoiceCommandRequest
from app.services.assistant_conversation_service import AssistantConversationService
from app.services.assistant_overlay_mapper import (
    build_actions,
    build_message_metadata,
    resolve_message_type,
    resolve_ui_state,
)
from app.services.assistant_voice_service import AssistantVoiceService
from app.services.voice_service import VoiceService
from app.services.voice_session_store import pending_voice_sessions


class AssistantService:
    """Unified text/voice assistant layer for mobile overlay (same dialogue engine as /voice)."""

    def __init__(
        self,
        session: AsyncSession,
        voice_service: VoiceService,
        conversation_service: AssistantConversationService,
        assistant_voice_service: AssistantVoiceService,
    ) -> None:
        self._session = session
        self._voice = voice_service
        self._conversations = conversation_service
        self._assistant_voice = assistant_voice_service

    @staticmethod
    def _validate_text(text: str) -> str:
        stripped = text.strip()
        if not stripped or len(stripped) > 1000:
            raise AppException("Некорректная длина текста", status_code=400)
        return stripped

    def _resolve_voice_enabled(
        self,
        payload: AssistantMessageRequest,
        conversation,
    ) -> bool:
        if payload.assistant_voice_enabled is not None:
            return payload.assistant_voice_enabled
        if payload.input_channel == "voice":
            return True
        return self._conversations.is_voice_enabled(conversation)

    async def handle_message(
        self,
        payload: AssistantMessageRequest,
        current_user: UserRead,
    ) -> AssistantMessageResponse:
        text = self._validate_text(payload.text)
        user_msg_type = (
            AssistantMessageType.voice
            if payload.input_channel == "voice"
            else AssistantMessageType.text
        )

        conversation = await self._conversations.get_or_create(
            current_user.id,
            payload.conversation_id,
        )

        voice_enabled = self._resolve_voice_enabled(payload, conversation)

        self._conversations.hydrate_voice_session_store(
            conversation=conversation,
            session_store=pending_voice_sessions,
            user_id=current_user.id,
        )

        await self._conversations.append_message(
            conversation_id=conversation.id,
            role=AssistantMessageRole.user,
            content=text,
            message_type=user_msg_type,
            metadata={"input_channel": payload.input_channel},
        )

        voice_resp = await self._voice.handle_command(
            VoiceCommandRequest(text=text),
            current_user,
        )

        voice_session = self._voice._dialogue.get_pending_session(current_user.id)
        new_state = self._conversations.persist_voice_session(
            conversation,
            voice_session,
            session_store=pending_voice_sessions,
            user_id=current_user.id,
        )
        new_state["assistant_voice_enabled"] = voice_enabled
        await self._conversations.update_state(conversation.id, new_state)

        ui_state = resolve_ui_state(voice_resp)
        actions = build_actions(voice_resp)
        assistant_msg_type = resolve_message_type(voice_resp)

        tts_response = await self._assistant_voice.build_voice_response(
            voice_resp.message,
            enabled=voice_enabled,
        )

        await self._conversations.append_message(
            conversation_id=conversation.id,
            role=AssistantMessageRole.assistant,
            content=voice_resp.message,
            message_type=assistant_msg_type,
            metadata=build_message_metadata(
                voice_resp,
                ui_state=ui_state,
                actions=actions,
                input_channel=payload.input_channel,
                assistant_voice=tts_response,
            ),
        )

        try:
            await self._session.commit()
        except Exception as exc:
            await self._session.rollback()
            raise TransactionFailedError(
                "Failed to persist assistant conversation; transaction rolled back.",
            ) from exc

        history = await self._conversations.get_history(
            conversation.id,
            current_user.id,
            limit=20,
        )

        return AssistantMessageResponse(
            conversation_id=conversation.id,
            message=voice_resp.message,
            ui_state=ui_state,
            actions=actions,
            dialogue=voice_resp.dialogue,
            intent=voice_resp.intent,
            data=voice_resp.data,
            draft_preview=voice_resp.draft_preview,
            promotion_offer=voice_resp.promotion_offer,
            needs_clarification=voice_resp.needs_clarification,
            moderation_required=voice_resp.moderation_required,
            moderation_reason=voice_resp.moderation_reason,
            publish_confirmation_required=voice_resp.publish_confirmation_required,
            needs_photos=voice_resp.needs_photos,
            real_photo_required=voice_resp.real_photo_required,
            assistant_voice_enabled=voice_enabled,
            voice_command=voice_resp,
            voice_response=tts_response,
            history=history,
        )

    async def get_conversation_history(
        self,
        conversation_id: int,
        user_id: int,
        *,
        limit: int = 50,
    ) -> list[AssistantMessageRead]:
        return await self._conversations.get_history(conversation_id, user_id, limit=limit)


def build_assistant_conversation_service(session: AsyncSession) -> AssistantConversationService:
    return AssistantConversationService(
        session,
        AssistantConversationRepository(session),
        AssistantMessageRepository(session),
    )
