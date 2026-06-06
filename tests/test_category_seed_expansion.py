from __future__ import annotations

import re

import pytest

from app.seeds.category_data import (
    AI_DIALOGUE_HINTS,
    CATEGORY_ALIASES,
    CORE_FIELDS,
    MODERATION_RULES,
    ROOT_CATEGORIES,
    ROUTING_RULES,
    SUBCATEGORIES,
    all_category_slugs,
    seed_inventory_counts,
)
from app.seeds.vehicle_data import (
    BRAND_ALIASES,
    BRANDS,
    MODEL_ALIASES,
    MODELS,
    vehicle_seed_counts,
)
from app.services.category_text import normalize_alias_compact


def test_seed_inventory_minimums() -> None:
    inv = seed_inventory_counts()
    assert inv["root_categories"] == 19
    assert inv["subcategories"] >= 50
    assert inv["category_aliases"] >= 80
    assert inv["core_field_definitions"] >= 45
    assert inv["routing_rules"] >= 12
    assert inv["moderation_rules"] >= 10


def test_vehicle_seed_minimums() -> None:
    v = vehicle_seed_counts()
    assert v["brands"] >= 55
    assert v["model_definitions"] >= 80
    assert v["brand_aliases"] >= 40
    assert v["model_aliases"] >= 35


def test_routing_rules_target_slugs_exist() -> None:
    slugs = all_category_slugs()
    for _name, _pattern, _desc, config in ROUTING_RULES:
        target = config["target_category_slug"]
        assert target in slugs, f"Unknown routing target: {target}"


def test_all_roots_have_dialogue_hint_or_subcategory_core() -> None:
    root_slugs = {r[0] for r in ROOT_CATEGORIES}
    roots_with_hint = set(AI_DIALOGUE_HINTS.keys())
    subs_with_core = set()
    for sub_slug in CORE_FIELDS:
        for root, subs in SUBCATEGORIES.items():
            if any(s[0] == sub_slug for s in subs):
                subs_with_core.add(root)
                break
    for root in root_slugs:
        assert root in roots_with_hint or root in subs_with_core


def test_every_subcategory_has_core_fields() -> None:
    all_subs = [s[0] for subs in SUBCATEGORIES.values() for s in subs]
    missing = [s for s in all_subs if s not in CORE_FIELDS]
    assert not missing, f"Subcategories without CORE_FIELDS: {missing}"


def test_core_fields_always_include_city() -> None:
    for slug, fields in CORE_FIELDS.items():
        keys = [f[0] for f in fields]
        assert "city" in keys, f"{slug} missing city core field"


@pytest.mark.parametrize(
    "phrase,expected_compact_substr",
    [
        ("лх570", "lx570"),
        ("LX 570", "lx570"),
        ("хавал", "haval"),
        ("джили", "geely"),
        ("jetour", "jetour"),
        ("омода", "omoda"),
        ("ешка", "eclass"),
        ("джеили", "geely"),
    ],
)
def test_vehicle_colloquial_compact(phrase: str, expected_compact_substr: str) -> None:
    compact = normalize_alias_compact(phrase)
    assert expected_compact_substr in compact or compact == expected_compact_substr


def test_moderation_covers_medical_and_trust() -> None:
    names = {r[2] for r in MODERATION_RULES}
    assert any("MEDICAL" in n for n in names)
    assert any("TRUST" in n for n in names)
    assert any("BUSINESS" in n for n in names)


def test_routing_phrases_have_patterns() -> None:
    for _name, pattern, _desc, _config in ROUTING_RULES:
        assert pattern
        re.compile(pattern, re.IGNORECASE)


def test_category_aliases_map_to_valid_subcategories() -> None:
    slugs = all_category_slugs()
    for cat_slug in CATEGORY_ALIASES:
        assert cat_slug in slugs


def test_no_duplicate_brand_alias_compact_collisions_in_seed() -> None:
    """Same compact key must not map to two different brands in seed file."""
    seen: dict[str, str] = {}
    for alias, brand_slug, _ in BRAND_ALIASES:
        compact = normalize_alias_compact(alias)
        if compact in seen and seen[compact] != brand_slug:
            pytest.fail(f"Alias collision: {compact} -> {seen[compact]} and {brand_slug}")
        seen[compact] = brand_slug
