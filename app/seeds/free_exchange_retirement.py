"""Free-exchange root retirement — product decision: not an AiVai category.

User/Archi: «Отдам бесплатно, обмен и находки» removed from UI and must not
receive Package A/B / listing_mode replacements. Soft-retire only.
"""
from __future__ import annotations

from typing import Any

FREE_EXCHANGE_ROOT_SLUG = "free-exchange"
FREE_EXCHANGE_ROOT_LABEL = "Отдам бесплатно, обмен и находки"

# Root + all descendants — soft-retired as a closed set.
FREE_EXCHANGE_RETIRED_SLUGS: frozenset[str] = frozenset(
    {
        "free-exchange",
        "free-give",
        "free-exchange-swap",
        "free-found",
    }
)

FREE_EXCHANGE_RETIRED_META: tuple[tuple[str, str, str | None], ...] = (
    ("free-exchange", FREE_EXCHANGE_ROOT_LABEL, None),
    ("free-give", "Отдам бесплатно", "free-exchange"),
    ("free-exchange-swap", "Обмен", "free-exchange"),
    ("free-found", "Находки", "free-exchange"),
)

# Canonical active product roots after free-exchange retirement (exact set).
AIVAI_ACTIVE_ROOT_SLUGS: frozenset[str] = frozenset(
    {
        "real-estate",
        "transport",
        "jobs",
        "services",
        "repair-construction",
        "electronics",
        "business-equipment",
        "home-garden",
        "kids",
        "medical",
        "food-agri",
        "beauty",
        "fashion",
        "sports-hobby",
        "stationery-books",
        "animals",
        "materials",
        "ready-business",
    }
)

AIVAI_ACTIVE_ROOT_COUNT = len(AIVAI_ACTIVE_ROOT_SLUGS)


def free_exchange_assert_retirement_contracts() -> None:
    if FREE_EXCHANGE_ROOT_SLUG not in FREE_EXCHANGE_RETIRED_SLUGS:
        raise RuntimeError("free-exchange root missing from retired set")
    if FREE_EXCHANGE_ROOT_SLUG in AIVAI_ACTIVE_ROOT_SLUGS:
        raise RuntimeError("free-exchange must not be in active root inventory")
    if AIVAI_ACTIVE_ROOT_COUNT != 18:
        raise RuntimeError(
            f"expected 18 active roots, got {AIVAI_ACTIVE_ROOT_COUNT}"
        )
    if FREE_EXCHANGE_RETIRED_SLUGS & AIVAI_ACTIVE_ROOT_SLUGS:
        raise RuntimeError("retired free-exchange slugs overlap active roots")


def free_exchange_retirement_report_row() -> dict[str, Any]:
    return {
        "root": FREE_EXCHANGE_ROOT_SLUG,
        "retired_slugs": sorted(FREE_EXCHANGE_RETIRED_SLUGS),
        "active_root_count": AIVAI_ACTIVE_ROOT_COUNT,
        "active_roots": sorted(AIVAI_ACTIVE_ROOT_SLUGS),
        "package_a": "ABSENT",
        "package_b": "ABSENT",
        "replacement_modes": "ABSENT",
    }
