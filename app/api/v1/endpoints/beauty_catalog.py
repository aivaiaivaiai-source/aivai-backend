"""Beauty catalogs."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.seeds.beauty_sections_catalog import build_beauty_section_catalog

router = APIRouter()


@router.get("/section/{section_key}")
async def get_beauty_section_catalog(section_key: str) -> dict:
    catalog = build_beauty_section_catalog(section_key)
    if catalog is None:
        raise HTTPException(status_code=404, detail="Unknown beauty section")
    return catalog
