"""Provenance for listing.category_id (Substage 3C-4 draft enrichment)."""

from __future__ import annotations

import enum


class CategorySelectionSource(str, enum.Enum):
    manual = "manual"
    resolver = "resolver"
