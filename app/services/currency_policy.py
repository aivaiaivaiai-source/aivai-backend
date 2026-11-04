# -*- coding: utf-8 -*-
"""Category default currency policy (Backend SoT).

Whole-vehicle sale → USD.
Products / services / jobs / rental / RE rent → KGS.
Real Estate sale → USD (deal_type rent → KGS).
"""
from __future__ import annotations

from app.models.enums import Currency

# Exact whole-vehicle sale leaf/parent slugs (Transport V2 sale branches).
_WHOLE_VEHICLE_SLUGS: frozenset[str] = frozenset(
    {
        "transport-car-sale",
        "transport-moto",
        "transport-mototechnika",
        "transport-buses-microbuses-motorhomes",
        "transport-cargo",
        "transport-special-equipment",
        "transport-watercraft",
        "transport-trailers",
        "transport-farm-machinery",
    }
)

_WHOLE_VEHICLE_PREFIXES: tuple[str, ...] = (
    "transport-car-sale",
    "transport-moto-",
    "transport-mototechnika-",
    "transport-buses-",
    "transport-microbus",
    "transport-motorhome",
    "transport-cargo-",
    "transport-special-",
    "transport-water-",
    "transport-watercraft-",
    "transport-trailers-",
    "transport-trailer-",
    "transport-farm-",
)

# Explicit product/service/rental under Transport that must stay KGS.
# Bicycles are non-motorized goods → KGS (product policy; user may override to USD).
_TRANSPORT_PRODUCT_PREFIXES: tuple[str, ...] = (
    "transport-auto-parts",
    "transport-tires-wheels",
    "transport-rental",
    "transport-auto-services",
    "transport-tuning",
    "transport-accessories",
    "transport-buyback-exchange",
    "transport-bicycles",
)

_SERVICE_ROOT_PREFIXES: tuple[str, ...] = (
    "services",
    "construction-services",
    "repair-",
)

_PRODUCT_ROOT_PREFIXES: tuple[str, ...] = (
    "electronics",
    "home-garden",
    "fashion",
    "kids",
    "animals",
    "food",
    "business-equipment",
    "medical",
    "materials",
    "sports",
    "stationery",
    "beauty",
    "ready-business",
)


def _is_whole_vehicle_sale(slug: str) -> bool:
    if slug in _WHOLE_VEHICLE_SLUGS:
        return True
    for p in _TRANSPORT_PRODUCT_PREFIXES:
        if slug == p or slug.startswith(p + "-") or slug.startswith(p):
            return False
    for p in _WHOLE_VEHICLE_PREFIXES:
        if slug == p.rstrip("-") or slug.startswith(p):
            return True
    # Mototechnika / electric vehicle sale leaves often under transport-moto-*
    if slug.startswith("transport-electric-") and "parts" not in slug:
        # Electric vehicles sale → treat as whole vehicle USD
        if "parts" in slug or "zapchasti" in slug:
            return False
        return True
    # Bicycles are NOT whole-vehicle USD — see _TRANSPORT_PRODUCT_PREFIXES.
    return False


def _is_real_estate(slug: str) -> bool:
    return slug == "real-estate" or slug.startswith("real-estate-")


def _is_rent_deal(deal_type: str | None) -> bool:
    if not deal_type:
        return False
    low = deal_type.strip().lower()
    return any(
        tok in low
        for tok in (
            "сдам",
            "сдаю",
            "аренда",
            "аренду",
            "сниму",
            "койко",
            "rent",
        )
    )


def default_currency_for(
    slug: str | None,
    *,
    deal_type: str | None = None,
    entity_type: str | None = None,
) -> Currency:
    """Resolve PriceDialog / Search filter default currency."""
    s = (slug or "").strip()
    if not s:
        # Jobs / services often identified by entity_type when slug missing.
        if entity_type in ("job", "service"):
            return Currency.KGS
        return Currency.KGS

    if s == "jobs" or s.startswith("jobs-") or entity_type == "job":
        return Currency.KGS

    if _is_real_estate(s):
        if _is_rent_deal(deal_type):
            return Currency.KGS
        # Sale (and unspecified offer default) → USD.
        return Currency.USD

    for p in _TRANSPORT_PRODUCT_PREFIXES:
        if s == p or s.startswith(p + "-") or s.startswith(p):
            return Currency.KGS

    if _is_whole_vehicle_sale(s):
        return Currency.USD

    for p in _SERVICE_ROOT_PREFIXES:
        if s == p.rstrip("-") or s.startswith(p):
            return Currency.KGS

    for p in _PRODUCT_ROOT_PREFIXES:
        if s == p or s.startswith(p + "-") or s.startswith(p):
            return Currency.KGS

    if entity_type == "service":
        return Currency.KGS

    # Safe marketplace fallback.
    return Currency.KGS
