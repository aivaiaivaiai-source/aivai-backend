"""Ready business catalogs."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.seeds.ready_business_sections_catalog import build_ready_business_section_catalog

router = APIRouter()


@router.get("/section/{section_key}")
async def get_ready_business_section_catalog(section_key: str) -> dict:
    catalog = build_ready_business_section_catalog(section_key)
    if catalog is None:
        raise HTTPException(status_code=404, detail="Unknown ready business section")
    return catalog
