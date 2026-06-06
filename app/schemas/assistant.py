from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.models.assistant_enums import (
    AssistantActionType,
    AssistantMessageRole,
    AssistantMessageType,
    AssistantUiState,
)
from app.schemas.listing_assistant import DraftPreview, PromotionOffer
from app.schemas.voice import VoiceCommandResponse, VoiceDialogueState, VoiceIntent


class AssistantAction(BaseModel):
    type: AssistantActionType
    label: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


class AssistantVoiceResponse(BaseModel):
    """Overlay TTS payload (audio URL only — no binary in JSON)."""

    enabled: bool = False
    audio_url: str | None = None
    provider: str | None = None
    duration_ms: int | None = None
    tts_text: str | None = None


class AssistantMessageRequest(BaseModel):
    text: str
    conversation_id: int | None = None
    input_channel: Literal["text", "voice"] = "text"
    assistant_voice_enabled: bool | None = None


class AssistantMessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    conversation_id: int
    role: AssistantMessageRole
    content: str
    message_type: AssistantMessageType
    metadata_json: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class AssistantMessageResponse(BaseModel):
    conversation_id: int
    message: str
    ui_state: AssistantUiState
    actions: list[AssistantAction] = Field(default_factory=list)
    dialogue: VoiceDialogueState | None = None
    intent: VoiceIntent | None = None
    data: dict[str, Any] | None = None
    draft_preview: DraftPreview | None = None
    promotion_offer: PromotionOffer | None = None
    needs_clarification: bool = False
    moderation_required: bool = False
    moderation_reason: str | None = None
    publish_confirmation_required: bool = False
    needs_photos: bool = False
    real_photo_required: bool = False
    assistant_voice_enabled: bool = False
    voice_command: VoiceCommandResponse | None = None
    voice_response: AssistantVoiceResponse | None = None
    history: list[AssistantMessageRead] = Field(default_factory=list)


class AssistantConversationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    status: str
    last_activity_at: datetime
    created_at: datetime
    updated_at: datetime
