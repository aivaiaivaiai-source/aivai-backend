"""Job vacancy catalogs."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.seeds.jobs_sections_catalog import build_job_section_catalog

router = APIRouter()


@router.get("/sewing")
async def get_sewing_jobs_catalog() -> dict:
    catalog = build_job_section_catalog("sewing")
    assert catalog is not None
    return catalog


@router.get("/section/{section_key}")
async def get_job_section_catalog(section_key: str) -> dict:
    catalog = build_job_section_catalog(section_key)
    if catalog is None:
        raise HTTPException(status_code=404, detail="Unknown job section")
    return catalog
