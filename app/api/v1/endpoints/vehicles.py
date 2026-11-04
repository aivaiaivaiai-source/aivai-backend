from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_vehicle_catalog_service
from app.schemas.vehicle import VehicleBrandRead, VehicleModelRead
from app.services.parts_vehicle_type import resolve_catalog_vehicle_type
from app.services.vehicle_catalog_service import VehicleCatalogService
from app.services.vehicle_execution import resolve_catalog_context

router = APIRouter()


@router.get("/brands", response_model=list[VehicleBrandRead])
async def list_vehicle_brands(
    popular: bool = Query(default=False, description="Return only popular brands."),
    vehicle_type: str | None = Query(
        default=None,
        description=(
            "Filter by vehicle_type enum: car, truck, motorcycle, special, bus, "
            "agricultural, electric, bicycle, watercraft, trailer, "
            "scooter, motoroller, atv, buggy, tricycle, snowmobile, kart, "
            "other_moto, "
            "e_scooter, e_moped, e_motorcycle, e_atv, hoverboard, monowheel, "
            "segway, golf_cart, other_electric, "
            "mountain_bike, city_bike, road_bike, bmx, other_bicycle, "
            "dump_truck, tractor_unit, flatbed_truck, box_truck, "
            "refrigerated_truck, light_truck, tanker_truck, "
            "tow_truck, other_truck, microbus, motorhome, "
            "excavator, loader, truck_crane, aerial_platform, bulldozer, "
            "road_roller, grader, manipulator, concrete_equipment, "
            "concrete_mixer, concrete_pump, septic_truck, mini_dumper, forklift, "
            "municipal, drilling, crushing_screening, attachment, other_special, "
            "tractor, mini_tractor, walk_behind, combine, seeder, "
            "potato_planter, tillage, forage, plow, harrow, cultivator, "
            "hiller, ditcher, mulcher, mower, walk_behind_mower, baler, "
            "header, rake, feed_mixer, sprayer, fertilizer_spreader, "
            "manure_spreader, potato_digger, kun, farm_crusher, "
            "grain_thrower, grain_cleaner, film_layer, ridge_former, "
            "agri_drone, other_agri, boat, motorboat, yacht, jet_ski, "
            "other_watercraft, drawbar_trailer, semi_trailer, camper_trailer."
        ),
    ),
    applicability: str | None = Query(
        default=None,
        description=(
            "Parts vehicle_applicability (e.g. passenger_cars, cargo). "
            "Mapped to catalog_context / vehicle_type."
        ),
    ),
    catalog_context: str | None = Query(
        default=None,
        description=(
            "Picker context: car_sale | passenger_parts | cargo_parts | bus_parts. "
            "Takes precedence for commercial LCV filtering."
        ),
    ),
    service: VehicleCatalogService = Depends(get_vehicle_catalog_service),
) -> list[VehicleBrandRead]:
    ctx = resolve_catalog_context(
        catalog_context=catalog_context,
        applicability=applicability,
        vehicle_type=None if catalog_context else vehicle_type,
    )
    # Legacy vehicle_type filter when no catalog context from applicability alone
    # that remaps car→passenger_parts: if only vehicle_type passed without
    # applicability/context, keep brand-type filter (truck/car) but apply context
    # when applicability is set.
    if catalog_context is None and applicability is None and vehicle_type is not None:
        # Explicit vehicle_type without parts applicability: brand-type filter only.
        # For car_sale Flutter should pass catalog_context=car_sale.
        vtype = resolve_catalog_vehicle_type(vehicle_type=vehicle_type)
        return await service.list_brands(popular_only=popular, vehicle_type=vtype)

    if ctx is not None:
        return await service.list_brands(popular_only=popular, catalog_context=ctx)

    vtype = resolve_catalog_vehicle_type(
        vehicle_type=vehicle_type,
        applicability=applicability,
    )
    return await service.list_brands(popular_only=popular, vehicle_type=vtype)


@router.get("/brands/{brand_slug}/models", response_model=list[VehicleModelRead])
async def list_vehicle_models(
    brand_slug: str,
    vehicle_type: str | None = Query(
        default=None,
        description="Require brand to match this vehicle_type (legacy).",
    ),
    applicability: str | None = Query(
        default=None,
        description="Parts vehicle_applicability mapped to catalog_context.",
    ),
    catalog_context: str | None = Query(
        default=None,
        description="Picker context: car_sale | passenger_parts | cargo_parts | bus_parts.",
    ),
    service: VehicleCatalogService = Depends(get_vehicle_catalog_service),
) -> list[VehicleModelRead]:
    ctx = resolve_catalog_context(
        catalog_context=catalog_context,
        applicability=applicability,
        vehicle_type=None if catalog_context else (
            vehicle_type if applicability else None
        ),
    )
    if catalog_context is None and applicability is None and vehicle_type is not None:
        vtype = resolve_catalog_vehicle_type(vehicle_type=vehicle_type)
        return await service.list_models_for_brand(brand_slug, vehicle_type=vtype)

    if ctx is not None:
        return await service.list_models_for_brand(brand_slug, catalog_context=ctx)

    vtype = resolve_catalog_vehicle_type(
        vehicle_type=vehicle_type,
        applicability=applicability,
    )
    return await service.list_models_for_brand(brand_slug, vehicle_type=vtype)
