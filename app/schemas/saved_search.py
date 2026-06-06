from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class SavedSearchCreate(BaseModel):
    query_params: dict[str, Any]
    is_active: bool = True


class SavedSearchUpdate(BaseModel):
    query_params: dict[str, Any] | None = None
    is_active: bool | None = None


class SavedSearchRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    query_params: dict[str, Any]
    is_active: bool
    created_at: datetime
    updated_at: datetime
