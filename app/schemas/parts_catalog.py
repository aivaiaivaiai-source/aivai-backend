"""Schemas for parts catalog (applicability-scoped)."""
from __future__ import annotations

from pydantic import BaseModel, Field


class PartsCatalogOption(BaseModel):
    value: str
    label: str
    children: list[PartsCatalogOption] = Field(default_factory=list)


class PartsCatalogSection(BaseModel):
    value: str
    label: str
    items: list[PartsCatalogOption] = Field(default_factory=list)


class PartsListingField(BaseModel):
    field_key: str
    label: str
    field_type: str
    is_required: bool = False
    sort_order: int = 0
    options: dict | None = None


class PartsCatalogResponse(BaseModel):
    applicability: str
    applicability_label: str
    category_slug: str
    sections: list[PartsCatalogSection]
    listing_fields: list[PartsListingField]
    path_fields: list[str] = Field(default_factory=list)
    search_aliases: dict[str, dict[str, str]] = Field(default_factory=dict)
