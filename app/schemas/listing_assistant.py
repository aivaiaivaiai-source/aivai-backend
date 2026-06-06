from __future__ import annotations

from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field


class DraftPreview(BaseModel):
    title: str
    description: str
    category_id: int
    category_slug: str | None = None
    category_name: str | None = None
    known_fields: dict[str, Any] = Field(default_factory=dict)
    price: str | None = None
    currency: str | None = None
    city: str | None = None
    real_photo_required: bool = False
    placeholder_allowed: bool = False


class PromotionOffer(BaseModel):
    enabled: bool = True
    price_kgs: Decimal = Field(default=Decimal("50"))
    listing_id: int | None = None
    message: str | None = None


class PromotionResult(BaseModel):
    activated: bool = False
    topup_required: bool = False
    balance: str | None = None
    required_amount: str | None = None
    message: str
