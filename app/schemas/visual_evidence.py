"""Visual evidence API schemas — internal evidence, not category."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class VisualConceptObservationRead(BaseModel):
    concept: str
    score: float
    evidence_media_ids: list[int] = Field(default_factory=list)


class VisualEvidenceRead(BaseModel):
    id: int
    listing_id: int
    status: str
    model_version: str
    prompt_version: str
    media_set_fingerprint: str
    observations: list[VisualConceptObservationRead] = Field(default_factory=list)
    top_concepts: list[str] = Field(default_factory=list)
    images_inspected: int = 0
    processing_ms: int | None = None
    feature_enabled: bool = False
    is_stale_for_current_media: bool = False
    created_at: datetime
    completed_at: datetime | None = None
