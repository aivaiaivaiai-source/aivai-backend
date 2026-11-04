"""Category Resolver API schemas (shadow mode)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class CategoryResolverPathNode(BaseModel):
    id: int
    slug: str
    name: str


class CategoryResolverAlternative(BaseModel):
    slug: str
    score: float
    reasons: list[str] = Field(default_factory=list)


class CategoryResolverRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    listing_id: int
    status: str
    suggested_category_id: int | None = None
    suggested_slug: str | None = None
    confidence: float | None = None
    needs_confirmation: bool = True
    candidate_path: list[CategoryResolverPathNode] = Field(default_factory=list)
    alternatives: list[CategoryResolverAlternative] = Field(default_factory=list)
    evidence_summary: dict[str, Any] = Field(default_factory=dict)
    intent_semantics: dict[str, Any] = Field(default_factory=dict)
    input_fingerprint: str = ""
    catalog_snapshot_hash: str = ""
    resolver_version: str = ""
    feature_enabled: bool = False
    auto_assign_enabled: bool = False
    draft_enrichment_enabled: bool = False
    draft_enrichment_applied: bool = False
    enrichment_category_id: int | None = None
    category_selection_source: str | None = None
    updated_at: datetime | None = None


class CategoryResolverResolveResponse(BaseModel):
    result: CategoryResolverRead
    created: bool = False
