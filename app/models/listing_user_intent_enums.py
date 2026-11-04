"""User intent lifecycle for hybrid classification (Substage 3C-1)."""

from __future__ import annotations

import enum


class ListingUserIntentStatus(str, enum.Enum):
    missing = "missing"
    provided = "provided"
