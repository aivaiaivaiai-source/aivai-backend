from __future__ import annotations

import enum


class Currency(str, enum.Enum):
    KGS = "KGS"
    USD = "USD"


class ListingStatus(str, enum.Enum):
    active = "active"
    sold = "sold"
    draft = "draft"
