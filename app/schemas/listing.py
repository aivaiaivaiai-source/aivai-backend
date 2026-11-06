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
from app.models.category_enums import VehicleExecution
from app.models.enums import Currency, ListingStatus
from app.models.job_create_intent import VALID_JOB_CREATE_INTENTS
from app.schemas.category import CategoryRead
from app.schemas.media import MediaRead

ListingFieldScalar = str | int | float | bool | dict[str, Any]


class ListingFacetOptionCount(BaseModel):
    """One controlled option count for a requested facet field."""

    value: str
    count: int = Field(ge=0)


class ListingFeedPage(BaseModel):
    """Paginated public feed — items + exact total for «Найдено N».

    Facets (optional, Package B+):
    - Omitted when the client does not request ``facets``.
    - Self-exclusion: each field facet is computed with all current filters
      EXCEPT that field's own constraint (EAV attrs and column-backed
      brand/model/fuel/transmission/year/steering/engine_volume).
    - brand/model facet values are canonical ref ids, not display names.
    - Counts cover the full filtered active set (not the current page).
    - Stable option values are identities; labels come from category metadata.
    - ``_category`` facet groups by listing.category_id among category_ids.
    """

    items: list["ListingRead"]
    total: int = Field(ge=0)
    facets: dict[str, list[ListingFacetOptionCount]] | None = None



def _ref_presentation(ref_id: int, related: Any) -> ListingFieldScalar:
    """Backward-compatible: int when label unknown; {id, label} when loaded."""
    name = getattr(related, "name", None) if related is not None else None
    if isinstance(name, str) and name.strip():
        return {"id": ref_id, "label": name.strip()}
    return ref_id


def serialize_listing_fields(rows: list[Any]) -> dict[str, ListingFieldScalar]:
    """Stable JSON map from EAV rows.

    Brand/model: prefer ``{id, label}`` when relationship is loaded; else bare id
    (legacy clients already resolve ids via Vehicle Catalog).
    """
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
            out[key] = _ref_presentation(
                row.ref_brand_id,
                getattr(row, "ref_brand", None),
            )
        elif row.ref_model_id is not None:
            out[key] = _ref_presentation(
                row.ref_model_id,
                getattr(row, "ref_model", None),
            )
    return out


class ListingCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=MAX_LISTING_DESCRIPTION_LENGTH)
    price: Decimal = Field(..., ge=0)
    # Null = unknown category (draft + early photo upload). Required for active.
    category_id: int | None = Field(default=None, ge=1)
    currency: Currency = Currency.KGS
    # Internal callers (voice/assistant) may set status. Public HTTP always forces draft.
    status: ListingStatus = ListingStatus.draft
    uses_placeholder_image: bool = False
    # Exactly one selected execution when the model requires it (SoT on listing).
    vehicle_execution: VehicleExecution | None = None
    # Jobs V2: hiring | job_seeking. Null for non-jobs / legacy.
    job_intent: str | None = None
    fields: dict[str, ListingFieldScalar] = Field(default_factory=dict)

    @model_validator(mode="after")
    def category_required_when_active(self) -> ListingCreate:
        if self.status == ListingStatus.active and self.category_id is None:
            raise ValueError("category_id is required when status is active")
        if self.category_id is None and self.fields:
            raise ValueError("fields require category_id")
        if self.job_intent is not None and self.job_intent not in VALID_JOB_CREATE_INTENTS:
            raise ValueError("job_intent must be hiring or job_seeking")
        return self

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
    vehicle_execution: VehicleExecution | None = None
    job_intent: str | None = None
    fields: dict[str, ListingFieldScalar] | None = None
    # Status changes only via PATCH /listings/{id}/status (photo policy + future moderation).

    @field_validator("fields")
    @classmethod
    def validate_fields(
        cls,
        value: dict[str, ListingFieldScalar] | None,
    ) -> dict[str, ListingFieldScalar] | None:
        if value is None:
            return None
        return ListingCreate.validate_fields(value)

    @field_validator("job_intent")
    @classmethod
    def validate_job_intent(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if value not in VALID_JOB_CREATE_INTENTS:
            raise ValueError("job_intent must be hiring or job_seeking")
        return value


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
    # Currency V2: publication/repricing FX snapshot (USD→KGS). Client formats cards.
    exchange_rate_snapshot: Decimal | None = None
    status: ListingStatus
    owner_id: int | None
    category_id: int | None = None
    category_selection_source: str | None = None
    category: CategoryRead | None = None
    images: list[MediaRead] = Field(default_factory=list)
    uses_placeholder_image: bool = False
    is_promoted: bool = False
    promotion_daily_rate: int | None = None
    promotion_tier: int = 0
    promotion_starts_at: datetime | None = None
    promotion_ends_at: datetime | None = None
    promotion_days_left: int = 0
    vehicle_execution: VehicleExecution | None = None
    job_intent: str | None = None
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
