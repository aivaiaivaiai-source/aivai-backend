from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.image_moderation_enums import MediaModerationStatus


class MediaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    listing_id: int
    url: str
    order: int
    is_placeholder: bool = False
    moderation_status: MediaModerationStatus = MediaModerationStatus.approved
    moderation_reason: str | None = None
    moderated_at: datetime | None = None


class MediaReorderRequest(BaseModel):
    image_ids: list[int]
