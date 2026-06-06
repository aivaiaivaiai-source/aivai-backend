from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.image_moderation_enums import ImageModerationVerdict, MediaModerationStatus


class ImageClassificationInput(BaseModel):
    content: bytes
    content_type: str
    source_name: str | None = None
    listing_id: int | None = None


class ImageClassificationResult(BaseModel):
    verdict: ImageModerationVerdict
    reason_code: str | None = None
    reason_detail: str | None = None
    provider: str = "stub"


class ImageModerationOutcome(BaseModel):
    media_id: int
    verdict: ImageModerationVerdict
    moderation_status: MediaModerationStatus
    moderation_reason: str | None = None
    moderated_at: datetime
    blocked_from_listing: bool = False
