from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.schemas.listing_assistant import DraftPreview, PromotionOffer


class VoiceCommandRequest(BaseModel):
    text: str


class VoiceIntent(BaseModel):
    intent: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    extracted: dict[str, Any] = Field(default_factory=dict)


class VoiceDialogueState(BaseModel):
    category_id: int | None = None
    category_slug: str | None = None
    category_name: str | None = None
    known_fields: dict[str, Any] = Field(default_factory=dict)
    missing_fields: list[str] = Field(default_factory=list)
    awaiting_field: str | None = None


class VoiceCommandResponse(BaseModel):
    intent: VoiceIntent
    message: str
    data: dict[str, Any] | None = None
    needs_clarification: bool = False
    missing_fields: list[dict[str, Any]] = Field(default_factory=list)
    next_question: str | None = None
    moderation_required: bool = False
    moderation_reason: str | None = None
    suggest_save_search: bool = False
    suggestions: list[dict[str, str]] = Field(default_factory=list)
    dialogue: VoiceDialogueState | None = None
    draft_preview: DraftPreview | None = None
    needs_photos: bool = False
    real_photo_required: bool = False
    publish_confirmation_required: bool = False
    publish_blocked_missing_photo: bool = False
    promotion_offer: PromotionOffer | None = None
