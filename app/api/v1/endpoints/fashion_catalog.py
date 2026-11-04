"""Fashion catalogs."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.seeds.fashion_sections_catalog import build_fashion_section_catalog

router = APIRouter()


@router.get("/section/{section_key}")
async def get_fashion_section_catalog(section_key: str) -> dict:
    catalog = build_fashion_section_catalog(section_key)
    if catalog is None:
        raise HTTPException(status_code=404, detail="Unknown fashion section")
    return catalog
