from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class AiSubscriptionInfo(BaseModel):
    id: int
    status: str
    starts_at: datetime
    expires_at: datetime
    messages_today: int
    max_messages_day: int

    model_config = {"from_attributes": True}


class AiAgentInfo(BaseModel):
    agent_type: str
    title: str
    subtitle: str
    icon: str
    price_som: int
    duration_days: int
    subscription: AiSubscriptionInfo | None = None


class AiSubscribeRequest(BaseModel):
    agent_type: str


class AiSendMessageRequest(BaseModel):
    text: str = Field(..., max_length=1000)


class AiMessageOut(BaseModel):
    id: int
    role: str
    content: str
    message_type: str
    metadata_json: dict
    created_at: datetime

    model_config = {"from_attributes": True}
