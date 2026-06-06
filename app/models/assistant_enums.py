from __future__ import annotations

import enum


class AssistantConversationStatus(str, enum.Enum):
    active = "active"
    closed = "closed"


class AssistantMessageRole(str, enum.Enum):
    user = "user"
    assistant = "assistant"
    system = "system"


class AssistantMessageType(str, enum.Enum):
    text = "text"
    voice = "voice"
    draft = "draft"
    preview = "preview"
    moderation = "moderation"
    promotion = "promotion"
    system = "system"


class AssistantUiState(str, enum.Enum):
    listening = "listening"
    thinking = "thinking"
    needs_input = "needs_input"
    draft_preview = "draft_preview"
    promotion_offer = "promotion_offer"
    moderation = "moderation"
    ready = "ready"


class AssistantActionType(str, enum.Enum):
    upload_photo = "upload_photo"
    confirm_publish = "confirm_publish"
    open_balance = "open_balance"
    save_search = "save_search"
