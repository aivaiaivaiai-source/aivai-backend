from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.image_moderation_enums import MediaModerationStatus
from app.models.media_enums import MediaLifecycleStatus


class FocusBboxRead(BaseModel):
    left: float
    top: float
    width: float
    height: float


class MediaVariantsRead(BaseModel):
    """Prepared variant URLs; unset entries fall back to legacy `url` in clients."""

    original: str | None = None
    display: str | None = None
    feed: str | None = None
    thumb: str | None = None


class MediaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    listing_id: int
    url: str
    order: int
    is_placeholder: bool = False
    lifecycle_status: MediaLifecycleStatus = MediaLifecycleStatus.ready
    client_upload_id: UUID | None = None
    variants: MediaVariantsRead = Field(default_factory=MediaVariantsRead)
    pipeline_version: str | None = None
    attempt_count: int = 0
    error_code: str | None = None
    processed_at: datetime | None = None
    moderation_status: MediaModerationStatus = MediaModerationStatus.approved
    moderation_reason: str | None = None
    moderated_at: datetime | None = None
    focus_bbox: FocusBboxRead | None = None
    focus_confidence: float | None = None

    @model_validator(mode="before")
    @classmethod
    def _assemble_media_read(cls, data: Any) -> Any:
        if not hasattr(data, "focus_bbox_left"):
            return data

        bbox = None
        if (
            data.focus_bbox_left is not None
            and data.focus_bbox_top is not None
            and data.focus_bbox_width is not None
            and data.focus_bbox_height is not None
        ):
            bbox = FocusBboxRead(
                left=data.focus_bbox_left,
                top=data.focus_bbox_top,
                width=data.focus_bbox_width,
                height=data.focus_bbox_height,
            )

        legacy_url = data.url
        from app.core.config import get_settings
        from app.services.media_delivery_service import MediaDeliveryService

        delivery = MediaDeliveryService(get_settings())
        variants = delivery.resolve_variants(data)
        if variants.display == legacy_url and getattr(data, "display_url", None):
            variants = MediaVariantsRead(
                original=variants.original,
                display=getattr(data, "display_url", None) or legacy_url,
                feed=variants.feed or getattr(data, "feed_url", None),
                thumb=variants.thumb or getattr(data, "thumb_url", None),
            )

        return {
            "id": data.id,
            "listing_id": data.listing_id,
            "url": legacy_url,
            "order": data.order,
            "is_placeholder": data.is_placeholder,
            "lifecycle_status": getattr(
                data,
                "lifecycle_status",
                MediaLifecycleStatus.ready,
            ),
            "client_upload_id": getattr(data, "client_upload_id", None),
            "variants": variants,
            "pipeline_version": getattr(data, "pipeline_version", None),
            "attempt_count": getattr(data, "attempt_count", 0),
            "error_code": getattr(data, "error_code", None),
            "processed_at": getattr(data, "processed_at", None),
            "moderation_status": data.moderation_status,
            "moderation_reason": data.moderation_reason,
            "moderated_at": data.moderated_at,
            "focus_bbox": bbox,
            "focus_confidence": data.focus_confidence,
        }


class MediaReorderRequest(BaseModel):
    image_ids: list[int]
