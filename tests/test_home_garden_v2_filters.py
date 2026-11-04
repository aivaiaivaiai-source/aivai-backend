"""Home & Garden V2 search filters + intelligence contract."""
from __future__ import annotations

from app.seeds.home_garden_filters import (
    build_home_garden_search_filters,
    search_filters_for_leaf,
)


def test_safes_have_search_filters() -> None:
    keys = [k for k, *_ in search_filters_for_leaf("home-garden-mebel-dlya-doma-seyfy")]
    assert keys == ["safe_purpose", "lock_type", "condition"]


def test_barrels_have_capacity_material_condition() -> None:
    keys = [
        k
        for k, *_ in search_filters_for_leaf(
            "home-garden-emkosti-i-rezervuary-bochki"
        )
    ]
    assert keys == ["capacity", "material", "condition"]


def test_coal_has_no_condition_filter() -> None:
    keys = [k for k, *_ in search_filters_for_leaf("home-garden-drova-i-ugol-ugol")]
    assert "condition" not in keys
    assert keys


def test_gas_cylinders_filters() -> None:
    keys = [k for k, *_ in search_filters_for_leaf("home-garden-gazovye-ballony")]
    assert "gas_cylinder_purpose" in keys
    assert "capacity" in keys
    assert "condition" in keys


def test_mower_filters() -> None:
    keys = [
        k
        for k, *_ in search_filters_for_leaf(
            "home-garden-sadovaya-tehnika-gazonokosilki"
        )
    ]
    assert keys == ["brand", "power_type", "condition", "self_propelled"]


def test_enum_filter_has_choices_config() -> None:
    filters = search_filters_for_leaf("home-garden-mebel-dlya-doma-seyfy")
    purpose = next(f for f in filters if f[0] == "safe_purpose")
    assert purpose[2] == "select"
    assert purpose[3] and purpose[3].get("choices")


def test_build_map_covers_all_leaves() -> None:
    m = build_home_garden_search_filters()
    assert "home-garden-mebel-dlya-doma-seyfy" in m
    assert "home-garden-prochee-dlya-doma-i-sada" in m
    # prochee may have empty filters — still present
    assert isinstance(m["home-garden-prochee-dlya-doma-i-sada"], list)
