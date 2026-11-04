"""Visual evidence job lifecycle — separate from media lifecycle."""

from __future__ import annotations

import enum


class VisualEvidenceStatus(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    ready = "ready"
    no_match = "no_match"
    failed = "failed"
    stale = "stale"
