"""API schemas for listing user intent (Substage 3C-1)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.core.constants import MAX_USER_INTENT_TEXT_LENGTH
from app.user_intent.fingerprint import normalize_intent_text


class ListingUserIntentRead(BaseModel):
    listing_id: int
    raw_intent_text: str | None = None
    intent_status: str
    intent_fingerprint: str = ""
    intent_version: int = 0
    feature_enabled: bool = False
    updated_at: datetime | None = None


class ListingUserIntentUpsertRequest(BaseModel):
    raw_intent_text: str = Field(..., min_length=1, max_length=MAX_USER_INTENT_TEXT_LENGTH)

    @field_validator("raw_intent_text")
    @classmethod
    def validate_intent_text(cls, value: str) -> str:
        normalized = normalize_intent_text(value)
        if not normalized:
            raise ValueError("raw_intent_text cannot be empty")
        if len(normalized) > MAX_USER_INTENT_TEXT_LENGTH:
            raise ValueError(
                f"raw_intent_text exceeds {MAX_USER_INTENT_TEXT_LENGTH} characters",
            )
        return normalized
