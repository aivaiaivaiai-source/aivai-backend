"""Business Equipment V2 Package A — Create SoT contracts + all-176 audit."""
from __future__ import annotations

from app.seeds.business_equipment_v2 import (
    BUSINESS_CONDITION_KEY,
    BUSINESS_EQUIPMENT_CREATE_FORBIDDEN,
    BUSINESS_EQUIPMENT_ROOT_SLUG,
    BUSINESS_EQUIPMENT_SELLER_TARGET,
    BUSINESS_EQUIPMENT_V2_CANONICAL_SLUGS,
    BUSINESS_EQUIPMENT_V2_EXPECTED_L2_COUNT,
    BUSINESS_KIND_KEY,
    BUSINESS_SELLER_KEY,
    build_business_equipment_v2_core_fields,
    business_equipment_v2_all_kind_audit,
    business_equipment_v2_assert_package_a_contracts,
    business_equipment_v2_complexity_histogram,
    business_equipment_v2_condition_no_kinds,
    business_equipment_v2_condition_yes_kinds,
    business_equipment_v2_kind_count,
)
from app.seeds.shared_goods_create_contract import (
    CONTACT_METHOD_CHOICES,
    GOODS_NEGOTIABLE_CHOICES,
    GOODS_SELLER_CHOICES,
    assert_field_matches_canonical,
    extract_choice_values,
    field_row_by_key,
    options_from_field_row,
)

# Independent expectations — do NOT derive from production allowlist alone.
_INDEPENDENT_NO = frozenset(
    {
        "Ценникодержатели",
        "Крючки для торгового оборудования",
        "Подставки для украшений",
        "Иглы промышленные",
    }
)
_INDEPENDENT_SELLER = ("Частное лицо", "Магазин", "Другой")
_FORBIDDEN_SAMPLE = ("brand", "model", "power", "voltage", "warranty", "year")


def test_package_a_contracts() -> None:
    business_equipment_v2_assert_package_a_contracts()
    assert business_equipment_v2_kind_count() == 176
    assert BUSINESS_EQUIPMENT_V2_EXPECTED_L2_COUNT == 20
    assert BUSINESS_EQUIPMENT_SELLER_TARGET == GOODS_SELLER_CHOICES
    assert "Компания" not in BUSINESS_EQUIPMENT_SELLER_TARGET


def test_20_l2_nonempty_cores_root_empty() -> None:
    cores = build_business_equipment_v2_core_fields()
    assert set(cores.keys()) == BUSINESS_EQUIPMENT_V2_CANONICAL_SLUGS
    assert len(cores) == 20
    assert BUSINESS_EQUIPMENT_ROOT_SLUG not in cores
    for slug, fields in cores.items():
        keys = [r[0] for r in fields]
        assert BUSINESS_KIND_KEY in keys, slug
        assert BUSINESS_SELLER_KEY in keys, slug
        assert "price" in keys, slug
        assert "negotiable" in keys, slug
        assert "contact_methods" in keys, slug
        assert not (set(keys) & BUSINESS_EQUIPMENT_CREATE_FORBIDDEN), slug
        kind_row = field_row_by_key(fields, BUSINESS_KIND_KEY)
        opts = extract_choice_values(options_from_field_row(kind_row))
        assert opts and len(opts) > 0, f"empty picker {slug}"


def test_shared_goods_contract_parity() -> None:
    cores = build_business_equipment_v2_core_fields()
    sample = cores["business-equipment-torgovoe-oborudovanie"]
    for key in ("seller_type", "price", "negotiable", "contact_methods"):
        assert_field_matches_canonical(
            domain="business_equipment",
            field_key=key,
            row=field_row_by_key(sample, key),
        )
    contact = extract_choice_values(
        options_from_field_row(field_row_by_key(sample, "contact_methods"))
    )
    assert contact == CONTACT_METHOD_CHOICES
    assert extract_choice_values(
        options_from_field_row(field_row_by_key(sample, "negotiable"))
    ) == GOODS_NEGOTIABLE_CHOICES
    assert extract_choice_values(
        options_from_field_row(field_row_by_key(sample, BUSINESS_SELLER_KEY))
    ) == _INDEPENDENT_SELLER


def test_condition_independent_matrix_172_4() -> None:
    yes = business_equipment_v2_condition_yes_kinds()
    no = business_equipment_v2_condition_no_kinds()
    assert no == _INDEPENDENT_NO
    assert len(yes) == 172
    assert len(no) == 4
    assert yes.isdisjoint(no)


def test_condition_depends_on_for_mixed_sections() -> None:
    cores = build_business_equipment_v2_core_fields()
    trade = cores["business-equipment-torgovoe-oborudovanie"]
    cond = field_row_by_key(trade, BUSINESS_CONDITION_KEY)
    assert cond is not None
    opts = options_from_field_row(cond)
    assert opts is not None
    dep = opts.get("depends_on") or {}
    assert dep.get("field") == BUSINESS_KIND_KEY
    values = set(dep.get("values") or [])
    assert "Торговые витрины" in values
    assert "Ценникодержатели" not in values
    assert "Подставки для украшений" not in values
    assert "Крючки для торгового оборудования" not in values

    parts = cores["business-equipment-zapchasti-i-komplektuyuschie"]
    parts_cond = field_row_by_key(parts, BUSINESS_CONDITION_KEY)
    assert parts_cond is not None
    parts_dep = (options_from_field_row(parts_cond) or {}).get("depends_on") or {}
    parts_values = set(parts_dep.get("values") or [])
    assert "Иглы промышленные" not in parts_values
    assert "Запчасти для станков" in parts_values


def test_all_176_audit_independent() -> None:
    rows = business_equipment_v2_all_kind_audit()
    assert len(rows) == 176
    for row in rows:
        assert row["business_kind_valid"] is True
        assert row["price"] is True
        assert tuple(row["seller"]) == _INDEPENDENT_SELLER
        assert row["forbidden"] == []
        assert row["condition_in_schema"] is True
        if row["kind"] in _INDEPENDENT_NO:
            assert row["condition"] == "NO"
            assert row["special_count"] == 0
        else:
            assert row["condition"] == "YES"
            assert row["special_count"] == 1
        for tech in _FORBIDDEN_SAMPLE:
            assert tech not in row["components"]
        assert row["ownership"] == "BUSINESS_EQUIPMENT"


def test_complexity_histogram_simple() -> None:
    hist = business_equipment_v2_complexity_histogram()
    assert hist["0"] == 4  # Condition-NO
    assert hist["1"] == 172  # Condition-YES only special
    assert hist["2"] == 0
    assert hist["3+"] == 0


def test_builder_idempotent() -> None:
    a = build_business_equipment_v2_core_fields()
    b = build_business_equipment_v2_core_fields()
    assert a.keys() == b.keys()
    for slug in a:
        assert [r[0] for r in a[slug]] == [r[0] for r in b[slug]]
