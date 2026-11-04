"""Description mode preference schemas (Substage 3C-2)."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ListingDescriptionModeRead(BaseModel):
    listing_id: int
    description_mode: str | None = None
    feature_enabled: bool = False


class ListingDescriptionModeUpsertRequest(BaseModel):
    description_mode: str = Field(..., min_length=1, max_length=32)
