"""API schemas for media classification."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class MediaClassificationCandidateRead(BaseModel):
    category_id: int
    category_slug: str
    category_name: str
    hierarchy_path: str = ""
    confidence: float = 0.0


class MediaClassificationRead(BaseModel):
    id: int
    listing_id: int
    status: str
    classifier_version: str
    media_set_fingerprint: str
    confidence_band: str
    top_confidence: float | None = None
    candidates: list[MediaClassificationCandidateRead] = Field(default_factory=list)
    evidence_media_ids: list[int] = Field(default_factory=list)
    images_inspected: int = 0
    selected_category_id: int | None = None
    predicted_category_id: int | None = None
    user_overridden: bool = False
    feature_enabled: bool = False
    is_stale_for_current_media: bool = False
    created_at: datetime
    completed_at: datetime | None = None
    notes: str | None = None
    # Foundation only — always null in Substage 2 runtime.
    suggested_attributes: dict[str, Any] | None = None


class MediaClassificationConfirmRequest(BaseModel):
    category_id: int = Field(..., ge=1)
    classification_id: int | None = Field(default=None, ge=1)


class MediaClassificationConfirmResponse(BaseModel):
    listing_id: int
    category_id: int
    classification_id: int | None = None
    media_jobs_enqueued: int = 0
    user_overridden: bool = False
