"""Construction and repair services catalog."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.seeds.services_construction_catalog import (
    build_construction_services_catalog,
)
from app.seeds.services_plumbing_catalog import build_plumbing_services_catalog
from app.seeds.services_electrical_catalog import (
    build_electrical_services_catalog,
)
from app.seeds.services_climate_catalog import build_climate_services_catalog
from app.seeds.services_furniture_catalog import build_furniture_services_catalog
from app.seeds.services_household_catalog import build_household_services_catalog
from app.seeds.services_rest_catalog import build_service_section_catalog

router = APIRouter()


@router.get("/construction")
async def get_construction_services_catalog() -> dict:
    return build_construction_services_catalog()


@router.get("/plumbing")
async def get_plumbing_services_catalog() -> dict:
    return build_plumbing_services_catalog()


@router.get("/electrical")
async def get_electrical_services_catalog() -> dict:
    return build_electrical_services_catalog()


@router.get("/climate")
async def get_climate_services_catalog() -> dict:
    return build_climate_services_catalog()


@router.get("/furniture")
async def get_furniture_services_catalog() -> dict:
    return build_furniture_services_catalog()


@router.get("/household")
async def get_household_services_catalog() -> dict:
    return build_household_services_catalog()


@router.get("/section/{section_key}")
async def get_service_section_catalog(section_key: str) -> dict:
    catalog = build_service_section_catalog(section_key)
    if catalog is None:
        raise HTTPException(status_code=404, detail="Unknown service section")
    return catalog
