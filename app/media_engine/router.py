"""Category-aware Media Engine routing."""

from __future__ import annotations

import enum

from app.services.focus_bbox_detection import CAR_SALE_CATEGORY_SLUGS


class MediaPipelineKind(str, enum.Enum):
    AUTO = "auto"
    GENERAL = "general"
    # Future: REAL_ESTATE, ELECTRONICS, FASHION, JOBS


def route_pipeline(category_slug: str | None) -> MediaPipelineKind:
    slug = (category_slug or "").strip().lower()
    if slug in CAR_SALE_CATEGORY_SLUGS:
        return MediaPipelineKind.AUTO
    return MediaPipelineKind.GENERAL
