"""Media AI classification enums (Substage 2)."""

from __future__ import annotations

import enum


class MediaClassificationStatus(str, enum.Enum):
    pending = "pending"
    running = "running"
    succeeded = "succeeded"
    failed = "failed"
    no_match = "no_match"
    stale = "stale"
    confirmed = "confirmed"


class MediaClassificationConfidenceBand(str, enum.Enum):
    high = "high"
    medium = "medium"
    low = "low"
    none = "none"
