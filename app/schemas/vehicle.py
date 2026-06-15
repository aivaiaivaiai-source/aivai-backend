from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class VehicleBrandRead(BaseModel):
    id: int
    slug: str
    name: str
    is_popular: bool = False
    country: str | None = None
    sort_order: int = Field(default=9999, description="Lower values sort first among popular brands.")


class VehicleModelRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    name: str
    brand_slug: str
