from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.media_enums import MediaLifecycleStatus


class DirectUploadAuthorization(BaseModel):
    method: str
    url: str
    headers: dict[str, str] = Field(default_factory=dict)
    expires_at: datetime | None = None


class DirectUploadInitiateRequest(BaseModel):
    client_upload_id: UUID
    content_type: str
    content_length: int
    content_sha256: str | None = None
    filename: str | None = None
    # Slot index 0..8 (cover = 0). Matches Media.order in DB.
    order: int | None = Field(default=None, ge=0, le=8)


class DirectUploadInitiateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    media_id: int
    client_upload_id: UUID
    status: MediaLifecycleStatus
    upload: DirectUploadAuthorization


class DirectUploadCompleteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    media_id: int
    status: MediaLifecycleStatus
    queued: bool = False
