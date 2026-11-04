"""Transport catalog canonicalization constants (Phase 1)."""
from __future__ import annotations

from pathlib import Path

# Legacy transport L2 slugs retired from active bootstrap (rows remain in DB, inactive).
RETIRED_TRANSPORT_SLUGS: frozenset[str] = frozenset(
    {
        "transport-cars",
        "transport-parts",
        "transport-trucks",
        "transport-moto",
        "transport-water",
    }
)

# Mobile v2 canonical transport L2 slugs (intelligence seeded here after Phase 1).
TRANSPORT_CANONICAL_SLUGS: frozenset[str] = frozenset(
    {
        "transport-car-sale",
        "transport-auto-parts",
        "transport-accessories-tuning",
        "transport-tires-wheels",
        "transport-cargo",
        "transport-special-equipment",
        "transport-moto-tech",
        "transport-watercraft",
    }
)

LEGACY_TRANSPORT_IDS: tuple[int, ...] = (606, 607, 608, 609, 610)

CANONICAL_MAP_V1_PATH = Path(__file__).with_name("catalog_canonical_map_v1.json")

# Explicit alias split rules (legacy transport-parts / transport-trucks).
PARTS_ALIAS_TO_CANONICAL_SLUG: dict[str, str] = {
    "запчасти": "transport-auto-parts",
    "аккумулятор": "transport-auto-parts",
    "бампер": "transport-auto-parts",
    "фара": "transport-auto-parts",
    "шины": "transport-tires-wheels",
    "диски": "transport-tires-wheels",
}

TRUCKS_ALIAS_TO_CANONICAL_SLUG: dict[str, str] = {
    "грузовик": "transport-cargo",
    "камаз": "transport-cargo",
    "газель": "transport-cargo",
    "фура": "transport-cargo",
    "спецтехника": "transport-special-equipment",
}

AI_SEARCH_TASK_LEGACY_ID_REMAP: dict[int, int] = {
    606: 681,
    609: 686,
    610: 692,
}
