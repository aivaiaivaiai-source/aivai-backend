"""Raw materials for production catalogs."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.seeds.materials_sections_catalog import build_materials_section_catalog

router = APIRouter()


@router.get("/section/{section_key}")
async def get_materials_section_catalog(section_key: str) -> dict:
    catalog = build_materials_section_catalog(section_key)
    if catalog is None:
        raise HTTPException(status_code=404, detail="Unknown materials section")
    return catalog
