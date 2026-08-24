"""Persist focus bbox on approved car-listing photo upload."""

from __future__ import annotations

from app.models.image_moderation_enums import MediaModerationStatus
from app.models.listing import Listing
from app.models.media import Media
from app.repositories.media_repository import MediaRepository
from app.services.focus_bbox_detection import CAR_SALE_CATEGORY_SLUGS
from app.services.focus_bbox_detector import FocusBBoxDetector


class FocusBBoxService:
    def __init__(
        self,
        media_repository: MediaRepository,
        detector: FocusBBoxDetector,
        *,
        enabled: bool = True,
    ) -> None:
        self._media = media_repository
        self._detector = detector
        self._enabled = enabled

    @staticmethod
    def _should_detect(listing: Listing, media: Media) -> bool:
        if media.is_placeholder or media.chat_id is not None:
            return False
        if media.moderation_status != MediaModerationStatus.approved:
            return False
        category = listing.category
        if category is None:
            return False
        return category.slug in CAR_SALE_CATEGORY_SLUGS

    async def maybe_detect_and_persist(
        self,
        *,
        listing: Listing,
        media: Media,
        content: bytes,
        content_type: str,
    ) -> None:
        if not self._enabled or not self._should_detect(listing, media):
            return

        result = self._detector.detect(content, content_type)
        if result is None:
            return

        await self._media.update(
            media.id,
            focus_bbox_left=result.left,
            focus_bbox_top=result.top,
            focus_bbox_width=result.width,
            focus_bbox_height=result.height,
            focus_confidence=result.confidence,
        )
