from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class NotificationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    body: str
    type: str
    payload: dict[str, Any]
    is_read: bool
    created_at: datetime


class NotificationMarkReadRequest(BaseModel):
    ids: list[int] = Field(default_factory=list)
