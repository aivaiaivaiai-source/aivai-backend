from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.core.constants import (
    MAX_LISTING_DESCRIPTION_LENGTH,
    MAX_LISTING_FIELD_KEY_LENGTH,
    MAX_LISTING_FIELD_VALUE_LENGTH,
    MAX_LISTING_FIELDS,
)
from app.models.enums import Currency, ListingStatus
from app.schemas.category import CategoryRead
from app.schemas.media import MediaRead

ListingFieldScalar = str | int | float | bool


class ListingFeedPage(BaseModel):
    """Paginated public feed — items + exact total for «Найдено N»."""

    items: list["ListingRead"]
    total: int = Field(ge=0)


def serialize_listing_fields(rows: list[Any]) -> dict[str, ListingFieldScalar]:
    """Stable JSON map from EAV rows. Brand/model expose catalog ids, not labels."""
    out: dict[str, ListingFieldScalar] = {}
    for row in rows:
        key = getattr(row, "field_key", None)
        if not key:
            continue
        if row.value_text is not None:
            out[key] = row.value_text
        elif row.value_int is not None:
            out[key] = row.value_int
        elif row.value_decimal is not None:
            out[key] = str(row.value_decimal)
        elif row.value_bool is not None:
            out[key] = row.value_bool
        elif row.value_date is not None:
            value_date: date = row.value_date
            out[key] = value_date.isoformat()
        elif row.ref_brand_id is not None:
            out[key] = row.ref_brand_id
        elif row.ref_model_id is not None:
            out[key] = row.ref_model_id
    return out


class ListingCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=MAX_LISTING_DESCRIPTION_LENGTH)
    price: Decimal = Field(..., ge=0)
    category_id: int = Field(..., ge=1)
    currency: Currency = Currency.KGS
    # Internal callers (voice/assistant) may set status. Public HTTP always forces draft.
    status: ListingStatus = ListingStatus.draft
    uses_placeholder_image: bool = False
    fields: dict[str, ListingFieldScalar] = Field(default_factory=dict)

    @field_validator("title")
    @classmethod
    def strip_title(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("title cannot be empty")
        return stripped

    @field_validator("description")
    @classmethod
    def strip_description(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None

    @field_validator("fields")
    @classmethod
    def validate_fields(
        cls,
        value: dict[str, ListingFieldScalar],
    ) -> dict[str, ListingFieldScalar]:
        if len(value) > MAX_LISTING_FIELDS:
            raise ValueError(f"At most {MAX_LISTING_FIELDS} fields are allowed")
        cleaned: dict[str, ListingFieldScalar] = {}
        for raw_key, raw_val in value.items():
            key = raw_key.strip()
            if not key:
                raise ValueError("field keys cannot be empty")
            if len(key) > MAX_LISTING_FIELD_KEY_LENGTH:
                raise ValueError(
                    f"field key exceeds {MAX_LISTING_FIELD_KEY_LENGTH} characters",
                )
            if isinstance(raw_val, str):
                text = raw_val.strip()
                if not text:
                    continue
                if len(text) > MAX_LISTING_FIELD_VALUE_LENGTH:
                    raise ValueError(
                        f"field '{key}' exceeds {MAX_LISTING_FIELD_VALUE_LENGTH} characters",
                    )
                cleaned[key] = text
            else:
                cleaned[key] = raw_val
        return cleaned


class ListingUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=255)
    description: str | None = Field(default=None, max_length=MAX_LISTING_DESCRIPTION_LENGTH)
    price: Decimal | None = Field(default=None, ge=0)
    currency: Currency | None = None
    category_id: int | None = Field(default=None, ge=1)
    # Status changes only via PATCH /listings/{id}/status (photo policy + future moderation).


class ListingStatusUpdate(BaseModel):
    status: ListingStatus


class PromotionActivate(BaseModel):
    daily_rate: int = Field(..., ge=70, le=150)
    days: int = Field(..., ge=1, le=30)


class ListingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None
    price: Decimal
    currency: Currency
    status: ListingStatus
    owner_id: int | None
    category_id: int
    category: CategoryRead
    images: list[MediaRead] = Field(default_factory=list)
    uses_placeholder_image: bool = False
    is_promoted: bool = False
    promotion_daily_rate: int | None = None
    promotion_tier: int = 0
    promotion_starts_at: datetime | None = None
    promotion_ends_at: datetime | None = None
    promotion_days_left: int = 0
    fields: dict[str, ListingFieldScalar] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

    @model_validator(mode="after")
    def sort_images_by_order(self) -> ListingRead:
        self.images.sort(key=lambda m: m.order)
        return self


class PromotionStopRead(BaseModel):
    listing: ListingRead
    refund_amount: int = 0
    charged_days: int = 0
    refunded_days: int = 0
