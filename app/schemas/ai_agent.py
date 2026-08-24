from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.ai_enums import AiAgentType


class AiSubscriptionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    agent_type: AiAgentType
    status: str
    price_som: int
    starts_at: datetime
    expires_at: datetime


class AiAgentInfo(BaseModel):
    agent_type: AiAgentType
    title: str
    price_som: int
    duration_days: int
    subscribed: bool
    subscription: AiSubscriptionRead | None = None
    unread_count: int = 0


class AiMessageRead(BaseModel):
    id: int
    role: str
    content: str
    message_type: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class AiSubscribeRequest(BaseModel):
    agent_type: AiAgentType


class AiSendMessageRequest(BaseModel):
    content: str


class AiSendMessageResponse(BaseModel):
    user_message: AiMessageRead
    assistant_messages: list[AiMessageRead]
