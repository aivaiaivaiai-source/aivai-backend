"""Tires and wheels catalog: direction, then kind, then size and traits."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.seeds.tires_wheels_catalog import build_tires_catalog, tires_directions

router = APIRouter()


@router.get("/directions")
async def get_tires_directions() -> dict:
    return {"directions": tires_directions()}


@router.get("/catalog/{applicability}")
async def get_tires_catalog(applicability: str) -> dict:
    catalog = build_tires_catalog(applicability)
    if catalog is None:
        raise HTTPException(status_code=404, detail="Tires catalog not available")
    return catalog
