from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_vehicle_catalog_service
from app.schemas.vehicle import VehicleBrandRead, VehicleModelRead
from app.services.vehicle_catalog_service import VehicleCatalogService

router = APIRouter()


@router.get("/brands", response_model=list[VehicleBrandRead])
async def list_vehicle_brands(
    popular: bool = Query(default=False, description="Return only popular brands."),
    service: VehicleCatalogService = Depends(get_vehicle_catalog_service),
) -> list[VehicleBrandRead]:
    return await service.list_brands(popular_only=popular)


@router.get("/brands/{brand_slug}/models", response_model=list[VehicleModelRead])
async def list_vehicle_models(
    brand_slug: str,
    service: VehicleCatalogService = Depends(get_vehicle_catalog_service),
) -> list[VehicleModelRead]:
    return await service.list_models_for_brand(brand_slug)
