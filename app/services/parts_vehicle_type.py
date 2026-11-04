"""Map parts vehicle_applicability → VehicleBrand.vehicle_type.

Brand/model catalogs are scoped by vehicle type, not by brand name alone:
the same manufacturer name may exist under car and truck (or bus) rows.
"""
from __future__ import annotations

from fastapi import HTTPException

from app.models.category_enums import VehicleType

# Parts Step 1 applicability values → catalog vehicle_type.
# Keys must match PARTS_VEHICLE_APPLICABILITY_OPTIONS in transport_v2_1.
PARTS_APPLICABILITY_TO_VEHICLE_TYPE: dict[str, VehicleType] = {
    "passenger_cars": VehicleType.car,
    "cargo": VehicleType.truck,
    "buses": VehicleType.bus,
    "special_equipment": VehicleType.special,
    "farm_machinery": VehicleType.agricultural,
    "moto": VehicleType.motorcycle,
    "electric": VehicleType.electric,
    "bicycles": VehicleType.bicycle,
    "watercraft": VehicleType.watercraft,
    "trailers": VehicleType.trailer,
}


def resolve_catalog_vehicle_type(
    *,
    vehicle_type: str | None = None,
    applicability: str | None = None,
) -> VehicleType | None:
    """Resolve optional filter for brands/models endpoints.

    Prefer explicit ``vehicle_type`` when both are provided.
    Returns None when neither is set (unfiltered — car-sale / legacy).
    """
    if vehicle_type:
        raw = vehicle_type.strip().lower()
        try:
            return VehicleType(raw)
        except ValueError as exc:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown vehicle_type '{vehicle_type}'",
            ) from exc

    if applicability:
        key = applicability.strip().lower()
        mapped = PARTS_APPLICABILITY_TO_VEHICLE_TYPE.get(key)
        if mapped is None:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"No vehicle brand/model catalog for applicability '{applicability}'"
                ),
            )
        return mapped

    return None
