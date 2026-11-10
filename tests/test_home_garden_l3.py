"""Home & garden L3 coverage tests (FINAL catalog)."""
from __future__ import annotations

from app.seeds.home_garden_catalog_final import HOME_GARDEN_L2_SLUGS
from app.seeds.home_garden_l3 import HOME_GARDEN_L3_SKELETON, _HOME_GARDEN_L3
from app.seeds.mobile_category_skeleton import MOBILE_CATEGORY_SKELETON


def test_home_garden_l3_covers_all_l2_except_direct_leaves() -> None:
    # Direct L2 publishable leaves have no nested L3 map entries.
    direct_leaf_l2 = {
        "home-garden-prochee-dlya-doma-i-sada",
        "home-garden-gazovye-ballony",
    }
    l2 = set(HOME_GARDEN_L2_SLUGS) - direct_leaf_l2
    assert set(_HOME_GARDEN_L3) == l2


def test_home_garden_l3_skeleton_nonempty() -> None:
    assert len(HOME_GARDEN_L3_SKELETON) >= 200
    parents = {row[0] for row in HOME_GARDEN_L3_SKELETON}
    assert "home-garden-mebel-dlya-doma" in parents
    names = {row[2] for row in HOME_GARDEN_L3_SKELETON}
    assert "Диваны" in names
    assert "Кухонные гарнитуры" in names
    assert "Матрасы" in names


def test_mobile_skeleton_includes_home_garden_l4() -> None:
    slugs = {row[1] for row in MOBILE_CATEGORY_SKELETON}
    assert "home-garden-mebel-dlya-doma-mebelnye-garnitury-kuhonnye-garnitury" in slugs
    assert "home-garden-mebel-dlya-doma-komplekty-mebeli-stol-i-stulya" in slugs
