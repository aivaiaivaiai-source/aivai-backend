"""Kids V2 taxonomy foundation — dual-tree cleanup + boundaries."""
from __future__ import annotations

from app.seeds.fashion_v2 import FASHION_V2_CANONICAL_SLUGS
from app.seeds.home_garden_filters import LEGACY_L3_REMAP
from app.seeds.kids_sections_catalog import KIDS_SECTIONS
from app.seeds.kids_v2 import (
    KIDS_ROOT_SLUG,
    KIDS_V2_CANONICAL_GOODS_LEAVES,
    KIDS_V2_CANONICAL_GOODS_SLUGS,
    KIDS_V2_EDUCATION_NEAREST_SERVICES_SLUG,
    KIDS_V2_EDUCATION_SERVICE_KINDS,
    KIDS_V2_EDUCATION_SLUG,
    KIDS_V2_ELECTRONICS_SMART_WATCH_KIND,
    KIDS_V2_LEGACY_CATALOG_SLUG_MISMATCHES,
    KIDS_V2_LEGACY_RETIRED_SLUGS,
    KIDS_V2_ORDINARY_WATCH_KIND,
    KIDS_V2_POOLS_HG_SLUG,
    KIDS_V2_REMOVED_POOL_KIND,
    KIDS_V2_RETIRED_SLUGS,
    KIDS_V2_SECTION_CANONICAL_SLUGS,
)
from app.seeds.loader import _RETIRED_CATEGORY_SLUGS
from app.seeds.services_v2 import SERVICES_V2_CANONICAL_LEAVES


def test_kids_root_and_canonical_goods_counts() -> None:
    from app.seeds.kids_v2 import (
        KIDS_V2_EXPECTED_L2_COUNT,
        KIDS_V2_SCHOOL_SLUG,
    )

    assert KIDS_ROOT_SLUG == "kids"
    assert len(KIDS_V2_CANONICAL_GOODS_LEAVES) == KIDS_V2_EXPECTED_L2_COUNT
    assert len(KIDS_V2_CANONICAL_GOODS_SLUGS) == KIDS_V2_EXPECTED_L2_COUNT
    assert KIDS_V2_EDUCATION_SLUG not in KIDS_V2_CANONICAL_GOODS_SLUGS
    assert KIDS_V2_SCHOOL_SLUG not in KIDS_V2_CANONICAL_GOODS_SLUGS
    assert KIDS_V2_EDUCATION_SLUG in KIDS_V2_RETIRED_SLUGS
    assert KIDS_V2_SCHOOL_SLUG in KIDS_V2_RETIRED_SLUGS
    assert KIDS_V2_LEGACY_RETIRED_SLUGS <= KIDS_V2_RETIRED_SLUGS
    assert KIDS_V2_RETIRED_SLUGS.isdisjoint(KIDS_V2_CANONICAL_GOODS_SLUGS)


def test_kids_retired_slugs_registered_in_loader() -> None:
    from app.seeds.kids_v2 import KIDS_V2_SCHOOL_SLUG

    assert KIDS_V2_RETIRED_SLUGS <= _RETIRED_CATEGORY_SLUGS
    for slug in (
        "kids-toys",
        "kids-clothes",
        "kids-strollers",
        KIDS_V2_EDUCATION_SLUG,
        KIDS_V2_SCHOOL_SLUG,
    ):
        assert slug in _RETIRED_CATEGORY_SLUGS


def test_kids_no_dual_active_catalog_identity() -> None:
    catalog_slugs = {cat["category_slug"] for cat in KIDS_SECTIONS.values()}
    assert catalog_slugs == set(KIDS_V2_SECTION_CANONICAL_SLUGS.values())
    assert catalog_slugs == KIDS_V2_CANONICAL_GOODS_SLUGS
    assert catalog_slugs.isdisjoint(KIDS_V2_LEGACY_CATALOG_SLUG_MISMATCHES)
    assert catalog_slugs.isdisjoint(KIDS_V2_LEGACY_RETIRED_SLUGS)


def test_kids_kind_count_after_boundary_cleanup() -> None:
    from app.seeds.kids_v2 import KIDS_V2_EXPECTED_KIND_COUNT

    kinds = [
        role["label"]
        for cat in KIDS_SECTIONS.values()
        for role in cat["roles"]
    ]
    # 111 after school L2 retirement; school form moved into clothes.
    assert len(kinds) == KIDS_V2_EXPECTED_KIND_COUNT
    assert len(kinds) == len(set(kinds))
    assert KIDS_V2_REMOVED_POOL_KIND not in kinds
    for kind in KIDS_V2_EDUCATION_SERVICE_KINDS:
        assert kind not in kinds
    assert "Школьная форма" in kinds
    assert "Школьные рюкзаки" not in kinds


def test_kids_education_kinds_are_services_not_goods() -> None:
    for kind in KIDS_V2_EDUCATION_SERVICE_KINDS:
        assert kind  # exact inventory preserved for Archi decision
    services_slugs = {slug for slug, _label, _sort in SERVICES_V2_CANONICAL_LEAVES}
    assert KIDS_V2_EDUCATION_NEAREST_SERVICES_SLUG in services_slugs
    # No exact kindergarten leaf invented — nearest tutoring L2 only.


def test_kids_fashion_boundary_no_child_fashion_leaves() -> None:
    for slug in FASHION_V2_CANONICAL_SLUGS:
        assert "detsk" not in slug
        assert "kids" not in slug


def test_kids_hg_furniture_boundary_and_pools_authority() -> None:
    assert "kids-detskaya-mebel" in KIDS_V2_CANONICAL_GOODS_SLUGS
    furniture_remap = {
        src: dst
        for src, dst in LEGACY_L3_REMAP.items()
        if "detskaya-mebel" in src or src.endswith("detskie-garnitury")
    }
    assert furniture_remap
    assert set(furniture_remap.values()) == {"kids-detskaya-mebel"}
    assert KIDS_V2_POOLS_HG_SLUG.startswith("home-garden-")
    assert KIDS_V2_REMOVED_POOL_KIND not in {
        r["label"] for r in KIDS_SECTIONS["sport"]["roles"]
    }


def test_kids_watch_ordinary_kept_smart_maps_to_electronics_kind() -> None:
    other_kinds = [r["label"] for r in KIDS_SECTIONS["other"]["roles"]]
    assert KIDS_V2_ORDINARY_WATCH_KIND in other_kinds
    # Smart/GPS stay Electronics vocabulary — not invented as Kids kinds.
    assert KIDS_V2_ELECTRONICS_SMART_WATCH_KIND not in other_kinds


def test_kids_baby_transport_kinds_remain() -> None:
    stroller = [r["label"] for r in KIDS_SECTIONS["strollers"]["roles"]]
    seats = [r["label"] for r in KIDS_SECTIONS["seats"]["roles"]]
    newborn = [r["label"] for r in KIDS_SECTIONS["newborn"]["roles"]]
    assert any("Коляск" in k for k in stroller)
    assert "Автолюльки" in seats
    assert "Ходунки" in newborn
