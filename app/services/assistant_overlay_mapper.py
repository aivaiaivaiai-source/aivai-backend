from __future__ import annotations

from typing import Any

from app.models.assistant_enums import (
    AssistantActionType,
    AssistantMessageType,
    AssistantUiState,
)
from app.core.assistant_state_policy import sanitize_assistant_message_metadata
from app.schemas.assistant import AssistantAction, AssistantVoiceResponse
from app.schemas.voice import VoiceCommandResponse


def resolve_ui_state(voice: VoiceCommandResponse) -> AssistantUiState:
    if voice.moderation_required:
        return AssistantUiState.moderation
    if voice.draft_preview is not None:
        return AssistantUiState.draft_preview
    if voice.promotion_offer is not None:
        return AssistantUiState.promotion_offer
    if (
        voice.needs_clarification
        or voice.next_question
        or voice.publish_confirmation_required
    ):
        return AssistantUiState.needs_input
    return AssistantUiState.ready


def resolve_message_type(voice: VoiceCommandResponse) -> AssistantMessageType:
    if voice.moderation_required:
        return AssistantMessageType.moderation
    if voice.draft_preview is not None:
        return AssistantMessageType.preview
    if voice.promotion_offer is not None:
        return AssistantMessageType.promotion
    return AssistantMessageType.text


def build_actions(voice: VoiceCommandResponse) -> list[AssistantAction]:
    actions: list[AssistantAction] = []
    data = voice.data or {}

    if voice.needs_photos or voice.publish_blocked_missing_photo or voice.real_photo_required:
        actions.append(
            AssistantAction(
                type=AssistantActionType.upload_photo,
                label="Добавить фото",
            ),
        )

    if voice.publish_confirmation_required:
        actions.append(
            AssistantAction(
                type=AssistantActionType.confirm_publish,
                label="Подтвердить публикацию",
            ),
        )

    if voice.promotion_offer is not None and data.get("topup_required"):
        actions.append(
            AssistantAction(
                type=AssistantActionType.open_balance,
                label="Пополнить баланс",
                payload={
                    "balance": data.get("balance"),
                    "required_amount": data.get("required_amount"),
                },
            ),
        )

    if voice.suggest_save_search:
        actions.append(
            AssistantAction(
                type=AssistantActionType.save_search,
                label="Сохранить поиск",
            ),
        )

    return actions


def build_message_metadata(
    voice: VoiceCommandResponse,
    *,
    ui_state: AssistantUiState,
    actions: list[AssistantAction],
    input_channel: str,
    assistant_voice: AssistantVoiceResponse | None = None,
) -> dict[str, Any]:
    meta: dict[str, Any] = {
        "ui_state": ui_state.value,
        "input_channel": input_channel,
        "actions": [a.model_dump(mode="json") for a in actions],
    }
    if voice.data:
        meta["voice_data"] = voice.data
    if voice.draft_preview is not None:
        meta["draft_preview"] = voice.draft_preview.model_dump(mode="json")
    if voice.promotion_offer is not None:
        meta["promotion_offer"] = voice.promotion_offer.model_dump(mode="json")
    if assistant_voice is not None:
        meta["voice_enabled"] = assistant_voice.enabled
        if assistant_voice.provider:
            meta["tts_provider"] = assistant_voice.provider
        if assistant_voice.audio_url:
            meta["tts_audio_url"] = assistant_voice.audio_url
        if assistant_voice.duration_ms is not None:
            meta["tts_duration_ms"] = assistant_voice.duration_ms
    return sanitize_assistant_message_metadata(meta)
