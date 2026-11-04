"""Kids World catalogs."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.seeds.kids_sections_catalog import build_kids_section_catalog

router = APIRouter()


@router.get("/newborn")
async def get_newborn_goods_catalog() -> dict:
    catalog = build_kids_section_catalog("newborn")
    assert catalog is not None
    return catalog


@router.get("/section/{section_key}")
async def get_kids_section_catalog(section_key: str) -> dict:
    catalog = build_kids_section_catalog(section_key)
    if catalog is None:
        raise HTTPException(status_code=404, detail="Unknown kids section")
    return catalog
