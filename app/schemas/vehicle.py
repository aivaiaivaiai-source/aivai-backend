from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.models.category_enums import VehicleExecution, VehicleType


class VehicleBrandRead(BaseModel):
    id: int
    slug: str
    name: str
    is_popular: bool = False
    country: str | None = None
    vehicle_type: VehicleType | None = None
    sort_order: int = Field(
        default=9999,
        description="Lower values sort first among popular brands.",
    )


class VehicleModelRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    name: str
    brand_slug: str
    allowed_executions: list[VehicleExecution] = Field(default_factory=list)
    allowed_execution_labels_ru: dict[str, str] = Field(default_factory=dict)
    requires_execution_choice: bool = False
    placement_by_execution: dict[str, str] = Field(default_factory=dict)
