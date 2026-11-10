"""Home & Garden V2 Package B — simple Search filters + allowlist invariants."""
from __future__ import annotations

from app.seeds.home_garden_catalog_final import HOME_GARDEN_LEAF_SLUGS
from app.seeds.home_garden_filters import (
    HOME_GARDEN_SEARCH_KEY_ALLOWLIST,
    HOME_GARDEN_SEARCH_KEY_EXCLUDE,
    build_home_garden_search_filters,
    search_filters_for_leaf,
)

_FORBIDDEN = {
    "plant_name",
    "material",
    "brand",
    "model",
    "width_cm",
    "height_cm",
    "length_cm",
    "depth_cm",
    "diameter_cm",
    "size",
    "length_or_diameter",
    "capacity",
    "volume",
    "weight",
    "quantity",
    "power",
    "cutting_width",
    "bar_length",
    "throughput",
    "pressure",
    "price",
    "negotiable",
    "contact_methods",
}


def test_safes_search() -> None:
    keys = [k for k, *_ in search_filters_for_leaf("home-garden-mebel-dlya-doma-seyfy")]
    assert keys == ["safe_purpose", "seller_type", "condition"]


def test_divan_search() -> None:
    keys = [k for k, *_ in search_filters_for_leaf("home-garden-mebel-dlya-doma-divany")]
    assert keys == ["foldable", "seller_type", "condition"]
    assert not (_FORBIDDEN & set(keys))


def test_mattress_search() -> None:
    keys = [k for k, *_ in search_filters_for_leaf("home-garden-mebel-dlya-doma-matrasy")]
    assert keys == ["sleeping_place_size", "seller_type", "condition"]


def test_mower_search() -> None:
    keys = [
        k
        for k, *_ in search_filters_for_leaf(
            "home-garden-sadovaya-tehnika-gazonokosilki"
        )
    ]
    assert keys == ["power_type", "self_propelled", "seller_type", "condition"]
    assert "brand" not in keys


def test_plants_seeds_seller_only() -> None:
    for slug in (
        "home-garden-sazhentsy-i-rassada-plodovye-derevya",
        "home-garden-semena-i-posadochnyy-material-semena-ovoschey",
        "home-garden-komnatnye-rasteniya-i-tsvety-orhidei",
    ):
        keys = [k for k, *_ in search_filters_for_leaf(slug)]
        assert keys == ["seller_type"], slug


def test_gas_no_capacity_search() -> None:
    keys = [k for k, *_ in search_filters_for_leaf("home-garden-gazovye-ballony")]
    assert keys == ["fill_state", "seller_type", "condition"]
    assert "capacity" not in keys


def test_fertilizer_form() -> None:
    keys = [
        k
        for k, *_ in search_filters_for_leaf(
            "home-garden-udobreniya-dlya-rasteniy-organicheskie-udobreniya"
        )
    ]
    assert keys == ["form", "seller_type"]
    assert "condition" not in keys


def test_enum_filter_is_multi_select() -> None:
    filters = search_filters_for_leaf("home-garden-mebel-dlya-doma-seyfy")
    purpose = next(f for f in filters if f[0] == "safe_purpose")
    assert purpose[2] == "multi_select"
    assert purpose[3] and purpose[3].get("choices")


def test_build_map_covers_all_leaves_with_seller() -> None:
    m = build_home_garden_search_filters()
    assert len(m) == 324
    for slug, filters in m.items():
        keys = [k for k, *_ in filters]
        assert "seller_type" in keys, slug
        assert not (_FORBIDDEN & set(keys)), (slug, keys)
        for key in keys:
            assert key in HOME_GARDEN_SEARCH_KEY_ALLOWLIST, (slug, key)
            assert key not in HOME_GARDEN_SEARCH_KEY_EXCLUDE, (slug, key)


def test_search_allowlist_contains_seller() -> None:
    assert "seller_type" in HOME_GARDEN_SEARCH_KEY_ALLOWLIST
    assert "plant_name" in HOME_GARDEN_SEARCH_KEY_EXCLUDE
    assert "capacity" in HOME_GARDEN_SEARCH_KEY_EXCLUDE
