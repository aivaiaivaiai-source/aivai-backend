"""Category Resolver lifecycle (Substage 3C-3 shadow mode)."""

from __future__ import annotations

import enum


class CategoryResolverStatus(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    suggested = "suggested"
    ambiguous = "ambiguous"
    no_match = "no_match"
    failed = "failed"
    stale = "stale"
