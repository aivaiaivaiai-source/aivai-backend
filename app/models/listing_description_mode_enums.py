"""Description fill preference for create-listing draft (Substage 3C-2)."""

from __future__ import annotations

import enum


class ListingDescriptionMode(str, enum.Enum):
    ai_assisted = "ai_assisted"
    manual = "manual"
