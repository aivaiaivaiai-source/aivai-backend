"""Home & Garden Create UI contract — 324-leaf invariants (no Package B)."""
from __future__ import annotations

from app.seeds.home_garden_catalog_final import HOME_GARDEN_LEAF_SLUGS
from app.seeds.home_garden_filters import (
    HOME_GARDEN_CREATE_TEXT_ALLOWLIST,
    build_home_garden_core_fields,
    create_field_component,
    fields_for_leaf,
)

_GOODS_BASE = {"seller_type", "price", "negotiable", "contact_methods"}
_COMMON_CONDITION = "condition"


def test_324_create_ui_components_and_no_vehicle_brand() -> None:
    cores = build_home_garden_core_fields()
    assert len(cores) == len(HOME_GARDEN_LEAF_SLUGS) == 324

    three_plus: list[tuple[str, set[str]]] = []
    for slug, fields in cores.items():
        keys = {f[0] for f in fields}
        assert "brand" not in keys, slug
        assert "model" not in keys, slug
        for f in fields:
            component = create_field_component(f)
            assert not component.startswith("forbidden"), (slug, f[0], component)
            assert component != "forbidden_brand", slug
            ft = f[2].value if hasattr(f[2], "value") else str(f[2])
            if ft == "string":
                assert f[0] in HOME_GARDEN_CREATE_TEXT_ALLOWLIST, (slug, f[0])
            if ft in {"number", "decimal"}:
                assert component == "numeric_dialog", (slug, f[0])
            if ft == "enum":
                assert component == "picker", (slug, f[0])
            if ft == "multi_select":
                assert component == "checkbox_picker", (slug, f[0])
            if f[3]:
                assert f[0] in _GOODS_BASE, (slug, f[0])
        specials = keys - _GOODS_BASE
        # condition counts as common goods-ish; report true specials beyond it
        beyond_condition = specials - {_COMMON_CONDITION}
        if len(beyond_condition) >= 3 or len(specials) > 3:
            three_plus.append((slug, specials))
        assert len(specials) <= 3, (slug, specials)

    # Only justified leaves may have 3 specials including condition.
    justified = {
        "home-garden-sadovaya-tehnika-gazonokosilki": {
            "condition",
            "power_type",
            "self_propelled",
        },
        "home-garden-gazovye-ballony": {
            "condition",
            "capacity",
            "fill_state",
        },
    }
    for slug, specials in three_plus:
        assert slug in justified and specials == justified[slug], (slug, specials)


def test_create_text_characteristics_empty() -> None:
    assert HOME_GARDEN_CREATE_TEXT_ALLOWLIST == frozenset()
    for slug in HOME_GARDEN_LEAF_SLUGS:
        for f in fields_for_leaf(slug):
            ft = f[2].value if hasattr(f[2], "value") else str(f[2])
            assert ft != "string", (slug, f[0])
            assert f[0] != "plant_name"


def test_garden_machinery_no_tech_specs() -> None:
    forbidden = {
        "brand",
        "power",
        "power_rating",
        "engine_power",
        "engine_volume",
        "cutting_width",
        "bar_length",
        "displacement",
        "voltage",
        "battery_capacity",
        "working_width",
        "throughput",
        "pressure",
    }
    for slug in HOME_GARDEN_LEAF_SLUGS:
        if not slug.startswith("home-garden-sadovaya-tehnika-"):
            continue
        keys = {f[0] for f in fields_for_leaf(slug)}
        assert not (keys & forbidden), slug
        assert "condition" in keys
        assert "power_type" in keys
        if "gazonokosilki" in slug:
            assert "self_propelled" in keys
        else:
            assert "self_propelled" not in keys
