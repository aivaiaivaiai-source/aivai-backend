"""Food/Agri V2 Package A — Create SoT + independent expectations."""
from __future__ import annotations

from app.models.category_enums import CategoryFieldType
from app.seeds.food_agri_v2 import (
    FOOD_AGRI_CONDITION_APPROVED_KINDS,
    FOOD_AGRI_CREATE_FORBIDDEN,
    FOOD_AGRI_KIND_KEY,
    FOOD_AGRI_PRICE_BASIS_FIELD_KEY,
    FOOD_AGRI_PRICE_BASIS_OPTIONS,
    FOOD_AGRI_SELLER_CHOICES,
    FOOD_AGRI_SELLER_DROP_SECTION_ROLES,
    FOOD_AGRI_SELLER_KEY,
    FOOD_AGRI_V2_CANONICAL_SLUGS,
    FOOD_AGRI_V2_EXPECTED_KIND_COUNT,
    FOOD_AGRI_V2_EXPECTED_L2_COUNT,
    FOOD_AGRI_V2_SEARCH_POLICY_PREP,
    build_food_agri_v2_core_fields,
    food_agri_v2_all_kind_audit,
    food_agri_v2_assert_contracts,
    food_agri_v2_complexity_histogram,
    food_agri_v2_kind_count,
    food_agri_v2_search_policy_prep,
)
from app.seeds.food_sections_catalog import FOOD_SECTIONS
from app.seeds.shared_goods_create_contract import (
    APPROVED_SHARED_FIELD_OVERRIDES,
    CONTACT_METHOD_CHOICES,
    GOODS_NEGOTIABLE_CHOICES,
    assert_field_matches_canonical,
    extract_choice_values,
    field_row_by_key,
    options_from_field_row,
)

# Independent approved expectations (do not derive from builder under test alone).
_INDEPENDENT_SELLER = ("Частное лицо", "Фермер", "Магазин", "Другой")
_INDEPENDENT_PRICE_BASIS = (
    "кг",
    "г",
    "л",
    "мл",
    "шт.",
    "упаковку",
    "мешок",
    "ящик",
    "тонну",
    "Другое",
)
_INDEPENDENT_CONTACT = CONTACT_METHOD_CHOICES
_INDEPENDENT_NEGOTIABLE = GOODS_NEGOTIABLE_CHOICES
_BANNED_SELLERS = frozenset({"Пекарня", "Кафе", "Оптовик", "Производитель"})


def test_food_agri_package_a_contracts() -> None:
    food_agri_v2_assert_contracts()
    assert food_agri_v2_kind_count() == FOOD_AGRI_V2_EXPECTED_KIND_COUNT
    assert len(FOOD_SECTIONS) == FOOD_AGRI_V2_EXPECTED_L2_COUNT
    assert len(FOOD_AGRI_V2_CANONICAL_SLUGS) == FOOD_AGRI_V2_EXPECTED_L2_COUNT


def test_food_agri_independent_seller_contract() -> None:
    assert FOOD_AGRI_SELLER_CHOICES == _INDEPENDENT_SELLER
    assert FOOD_AGRI_SELLER_DROP_SECTION_ROLES == _BANNED_SELLERS
    assert ("food_agri", "seller_type") in APPROVED_SHARED_FIELD_OVERRIDES
    cores = build_food_agri_v2_core_fields()
    for slug, fields in cores.items():
        row = field_row_by_key(fields, FOOD_AGRI_SELLER_KEY)
        assert row is not None
        assert row[1] == "Кто продаёт"
        assert extract_choice_values(options_from_field_row(row)) == _INDEPENDENT_SELLER
        assert_field_matches_canonical(
            domain="food_agri", field_key="seller_type", row=row
        )


def test_food_agri_independent_price_basis_contract() -> None:
    assert FOOD_AGRI_PRICE_BASIS_OPTIONS == _INDEPENDENT_PRICE_BASIS
    cores = build_food_agri_v2_core_fields()
    for slug, fields in cores.items():
        row = field_row_by_key(fields, FOOD_AGRI_PRICE_BASIS_FIELD_KEY)
        assert row is not None
        assert row[1] == "Цена за"
        assert row[2] == CategoryFieldType.enum
        assert row[3] is False
        assert extract_choice_values(options_from_field_row(row)) == (
            _INDEPENDENT_PRICE_BASIS
        )


def test_food_agri_condition_absent_all_kinds() -> None:
    assert FOOD_AGRI_CONDITION_APPROVED_KINDS == frozenset()
    cores = build_food_agri_v2_core_fields()
    for slug, fields in cores.items():
        keys = {r[0] for r in fields}
        assert "condition" not in keys
        assert keys.isdisjoint(FOOD_AGRI_CREATE_FORBIDDEN)


def test_food_agri_shared_price_negotiable_contacts() -> None:
    cores = build_food_agri_v2_core_fields()
    for slug, fields in cores.items():
        for key in ("price", "negotiable", "contact_methods"):
            assert_field_matches_canonical(
                domain="food_agri",
                field_key=key,
                row=field_row_by_key(fields, key),
            )
        contact = extract_choice_values(
            options_from_field_row(field_row_by_key(fields, "contact_methods"))
        )
        negotiable = extract_choice_values(
            options_from_field_row(field_row_by_key(fields, "negotiable"))
        )
        assert contact == _INDEPENDENT_CONTACT
        assert negotiable == _INDEPENDENT_NEGOTIABLE


def test_food_agri_all_158_kind_audit() -> None:
    audit = food_agri_v2_all_kind_audit()
    assert len(audit) == FOOD_AGRI_V2_EXPECTED_KIND_COUNT
    for row in audit:
        assert row["food_kind_valid"] is True
        assert row["seller"] == list(_INDEPENDENT_SELLER)
        assert row["price"] is True
        assert row["price_basis"] is True
        assert row["price_basis_options"] == list(_INDEPENDENT_PRICE_BASIS)
        assert row["condition"] is False
        assert row["forbidden"] == []
        assert row["components"][FOOD_AGRI_KIND_KEY] == "enum"
        assert row["components"]["price"] == "price"


def test_food_agri_create_complexity_simple() -> None:
    hist = food_agri_v2_complexity_histogram()
    assert hist["2"] == FOOD_AGRI_V2_EXPECTED_KIND_COUNT
    assert hist["5+"] == 0


def test_food_agri_search_policy_prep_no_price_basis() -> None:
    policy = food_agri_v2_search_policy_prep()
    allow = set(policy["allow"])
    assert FOOD_AGRI_KIND_KEY in allow
    assert FOOD_AGRI_SELLER_KEY in allow
    assert "region" in allow and "city" in allow
    assert FOOD_AGRI_PRICE_BASIS_FIELD_KEY not in allow
    assert "condition" not in allow
    assert "quantity" not in allow
    assert set(policy["legacy_prep"]) == FOOD_AGRI_V2_SEARCH_POLICY_PREP


def test_food_agri_23_schemas_nonempty_same_keys() -> None:
    cores = build_food_agri_v2_core_fields()
    assert set(cores) == FOOD_AGRI_V2_CANONICAL_SLUGS
    expected_keys = {
        FOOD_AGRI_KIND_KEY,
        FOOD_AGRI_SELLER_KEY,
        "price",
        FOOD_AGRI_PRICE_BASIS_FIELD_KEY,
        "negotiable",
        "contact_methods",
    }
    for slug, fields in cores.items():
        assert {r[0] for r in fields} == expected_keys
        kind_count = len(field_row_by_key(fields, FOOD_AGRI_KIND_KEY)[5]["choices"])
        assert kind_count > 0
