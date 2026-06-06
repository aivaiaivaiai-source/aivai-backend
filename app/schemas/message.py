from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.media import MediaRead


class MessageCreate(BaseModel):
    text: str = Field(default="", max_length=8000)
    media_ids: list[int] = Field(default_factory=list, max_length=10)


class MessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    chat_id: int
    sender_id: int
    text: str
    read_at: datetime | None
    created_at: datetime
    attachments: list[MediaRead] = Field(default_factory=list)
