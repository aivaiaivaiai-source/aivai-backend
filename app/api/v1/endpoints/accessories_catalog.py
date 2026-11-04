"""Accessories and tuning catalog: direction, then filter."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.seeds.accessories_tuning_catalog import (
    accessories_directions,
    build_accessories_catalog,
)

router = APIRouter()


@router.get("/directions")
async def get_accessories_directions() -> dict:
    return {"directions": accessories_directions()}


@router.get("/catalog/{applicability}")
async def get_accessories_catalog(applicability: str) -> dict:
    catalog = build_accessories_catalog(applicability)
    if catalog is None:
        raise HTTPException(status_code=404, detail="Accessories catalog not available")
    return catalog
