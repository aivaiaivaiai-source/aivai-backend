"""Home & garden L3/L4 under mobile L2 — TARGET final catalog."""
from __future__ import annotations

from app.models.category_enums import CategoryEntityType
from app.seeds.home_garden_catalog_final import HOME_GARDEN_NODES


def build_home_garden_l3_skeleton() -> list[tuple[str, str, str, CategoryEntityType, int]]:
    """Rows for MOBILE_CATEGORY_SKELETON: depth 3 and 4 only (L2 already seeded)."""
    rows: list[tuple[str, str, str, CategoryEntityType, int]] = []
    for parent, slug, name, sort_order, depth in HOME_GARDEN_NODES:
        if depth < 3:
            continue
        rows.append((parent, slug, name, CategoryEntityType.object, sort_order))
    return rows


HOME_GARDEN_L3_SKELETON = build_home_garden_l3_skeleton()

# Back-compat for tests that inspect the old dict shape.
_HOME_GARDEN_L3: dict[str, list[str]] = {}
for parent, slug, name, sort_order, depth in HOME_GARDEN_NODES:
    if depth != 3:
        continue
    _HOME_GARDEN_L3.setdefault(parent, []).append(name)
