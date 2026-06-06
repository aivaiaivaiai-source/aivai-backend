from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.enums import Currency, ListingStatus
from app.schemas.category import CategoryRead
from app.schemas.media import MediaRead


class ListingCreate(BaseModel):
    title: str = Field(..., max_length=255)
    description: str | None = None
    price: Decimal = Field(..., ge=0)
    category_id: int
    currency: Currency = Currency.KGS
    status: ListingStatus = ListingStatus.draft
    uses_placeholder_image: bool = False


class ListingUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=255)
    description: str | None = None
    price: Decimal | None = Field(default=None, ge=0)
    currency: Currency | None = None
    category_id: int | None = None
    status: ListingStatus | None = None


class ListingStatusUpdate(BaseModel):
    status: ListingStatus


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
    created_at: datetime
    updated_at: datetime

    @model_validator(mode="after")
    def sort_images_by_order(self) -> ListingRead:
        self.images.sort(key=lambda m: m.order)
        return self
