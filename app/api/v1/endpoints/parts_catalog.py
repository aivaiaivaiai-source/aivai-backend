"""Parts catalog endpoints (applicability-scoped dictionaries)."""
from __future__ import annotations

from typing import Any, Callable

from fastapi import APIRouter, HTTPException, Query

from app.schemas.parts_catalog import PartsCatalogResponse
from app.seeds.parts_bicycles import build_bicycles_catalog
from app.seeds.parts_buses import build_buses_catalog
from app.seeds.parts_cargo import build_cargo_catalog
from app.seeds.parts_electric import build_electric_catalog
from app.seeds.parts_farm import build_farm_catalog
from app.seeds.parts_moto import build_moto_catalog
from app.seeds.parts_passenger_cars import build_passenger_cars_catalog
from app.seeds.parts_special_equipment import build_special_equipment_catalog
from app.seeds.parts_trailers import build_trailers_catalog
from app.seeds.parts_water import build_water_catalog
from app.seeds.transport_v2_1 import PARTS_VEHICLE_APPLICABILITY_OPTIONS

router = APIRouter()


def _shared_sections_catalog(applicability: str, label: str) -> dict[str, Any]:
    """Reuse passenger section taxonomy until type-specific dictionaries exist.

    Brand/model SoT is still scoped by applicability via /vehicles/* — only
    the part-section tree is shared.
    """
    data = build_passenger_cars_catalog()
    data["applicability"] = applicability
    data["applicability_label"] = label
    return data


def _builder_for(applicability: str, label: str) -> Callable[[], dict[str, Any]]:
    def _build() -> dict[str, Any]:
        return _shared_sections_catalog(applicability, label)

    return _build


_BUILDERS: dict[str, Callable[..., dict[str, Any]]] = {
    "passenger_cars": build_passenger_cars_catalog,
    "cargo": build_cargo_catalog,
    "buses": build_buses_catalog,
    "special_equipment": build_special_equipment_catalog,
    "farm_machinery": build_farm_catalog,
    "moto": build_moto_catalog,
    "electric": build_electric_catalog,
    "bicycles": build_bicycles_catalog,
    "watercraft": build_water_catalog,
    "trailers": build_trailers_catalog,
}
for _value, _label in PARTS_VEHICLE_APPLICABILITY_OPTIONS:
    if _value not in _BUILDERS:
        _BUILDERS[_value] = _builder_for(_value, _label)


@router.get("/catalog/{applicability}", response_model=PartsCatalogResponse)
async def get_parts_catalog(
    applicability: str,
    equipment_type: str | None = Query(
        default=None,
        description=(
            "Subtype for special_equipment, farm_machinery, moto, electric, "
            "bicycles, cargo, buses, watercraft, or trailers. "
            "special_equipment: excavator, loader, forklift, … "
            "farm_machinery: tractor, mini_tractor, walk_behind, combine, "
            "seeder, potato_planter, plow, harrow, cultivator, hiller, "
            "ditcher, mulcher, mower, walk_behind_mower, baler, header, "
            "rake, feed_mixer, sprayer, fertilizer_spreader, "
            "manure_spreader, potato_digger, kun, farm_crusher, "
            "grain_thrower, grain_cleaner, film_layer, ridge_former, "
            "agri_drone, other_agri (tillage/forage legacy ok). "
            "moto: motorcycle, scooter, motoroller, … "
            "electric: e_scooter, e_moped, hoverboard, monowheel, "
            "segway, golf_cart, other_electric. "
            "bicycles: mountain_bike, city_bike, road_bike, "
            "teen_bike, e_bike, bmx, other_bicycle. "
            "cargo: dump_truck, tractor_unit, flatbed_truck, box_truck, "
            "refrigerated_truck, light_truck, tanker_truck, tow_truck, "
            "other_truck. "
            "buses: bus, microbus, motorhome. "
            "watercraft: boat, motorboat, yacht, jet_ski, other_watercraft. "
            "trailers: drawbar_trailer, semi_trailer, camper_trailer."
        ),
    ),
) -> PartsCatalogResponse:
    """Return section → item dictionary for a vehicle applicability value."""
    builder = _BUILDERS.get(applicability)
    if builder is None:
        raise HTTPException(
            status_code=404,
            detail=f"Parts catalog not available for applicability '{applicability}'",
        )
    if applicability in (
        "special_equipment",
        "farm_machinery",
        "moto",
        "electric",
        "bicycles",
        "cargo",
        "buses",
        "watercraft",
        "trailers",
    ):
        payload = builder(equipment_type=equipment_type)
    else:
        payload = builder()
    return PartsCatalogResponse.model_validate(payload)
