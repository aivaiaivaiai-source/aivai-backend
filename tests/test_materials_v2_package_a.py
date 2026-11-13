"""Materials V2 Package A — Create SoT contracts + all-117 audit."""
from __future__ import annotations

from app.seeds.materials_v2 import (
    FOOD_TARA_GAP_STATUS,
    MATERIALS_CREATE_FORBIDDEN,
    MATERIALS_KIND_KEY,
    MATERIALS_KIND_LABEL,
    MATERIALS_PRICE_BASIS_KEY,
    MATERIALS_PRICE_BASIS_OPTIONS,
    MATERIALS_ROOT_SLUG,
    MATERIALS_SELLER_KEY,
    MATERIALS_SELLER_TARGET,
    MATERIALS_V2_CANONICAL_SLUGS,
    MATERIALS_V2_EXPECTED_L2_COUNT,
    MATERIALS_V2_SEARCH_ALLOWLIST,
    MATERIALS_V2_SEARCH_EXCLUDE,
    MATERIALS_V2_SECTION_KINDS,
    build_materials_v2_core_fields,
    materials_v2_all_kind_audit,
    materials_v2_assert_package_a_contracts,
    materials_v2_complexity_histogram,
    materials_v2_kind_count,
)
from app.seeds.shared_goods_create_contract import (
    CONTACT_METHOD_CHOICES,
    GOODS_NEGOTIABLE_CHOICES,
    GOODS_SELLER_CHOICES,
)

_INDEPENDENT_SELLER = ("Частное лицо", "Магазин", "Другой")
_INDEPENDENT_BASIS = (
    "кг",
    "г",
    "тонна",
    "м",
    "м²",
    "м³",
    "л",
    "шт.",
    "рулон",
    "упаковка",
    "Другое",
)
_FORBIDDEN_SAMPLE = (
    "condition",
    "brand",
    "model",
    "manufacturer",
    "country",
    "grade",
    "quantity",
    "moq",
    "material_type",
    "wholesale_price",
)


def test_package_a_contracts() -> None:
    materials_v2_assert_package_a_contracts()
    assert materials_v2_kind_count() == 117
    assert MATERIALS_V2_EXPECTED_L2_COUNT == 18
    assert MATERIALS_SELLER_TARGET == GOODS_SELLER_CHOICES
    assert MATERIALS_KIND_KEY == "materials_kind"
    assert MATERIALS_KIND_LABEL == "Товар"
    assert FOOD_TARA_GAP_STATUS == "STILL_OPEN"
    assert MATERIALS_V2_SEARCH_ALLOWLIST == {
        MATERIALS_KIND_KEY,
        MATERIALS_SELLER_KEY,
        "geo",
    }
    assert MATERIALS_PRICE_BASIS_KEY in MATERIALS_V2_SEARCH_EXCLUDE
    assert "condition" in MATERIALS_V2_SEARCH_EXCLUDE


def test_18_l2_nonempty_cores_root_empty() -> None:
    cores = build_materials_v2_core_fields()
    assert set(cores.keys()) == MATERIALS_V2_CANONICAL_SLUGS
    assert len(cores) == 18
    assert MATERIALS_ROOT_SLUG not in cores
    for slug, fields in cores.items():
        keys = [r[0] for r in fields]
        assert MATERIALS_KIND_KEY in keys, slug
        assert MATERIALS_SELLER_KEY in keys, slug
        assert MATERIALS_PRICE_BASIS_KEY in keys, slug
        assert "price" in keys, slug
        assert "negotiable" in keys, slug
        assert "contact_methods" in keys, slug
        assert "condition" not in keys, slug
        assert set(keys).isdisjoint(_FORBIDDEN_SAMPLE)


def test_seller_and_shared_contract() -> None:
    cores = build_materials_v2_core_fields()
    for slug, fields in cores.items():
        seller = next(r for r in fields if r[0] == MATERIALS_SELLER_KEY)
        opts = [c["value"] for c in seller[5]["choices"]]
        assert opts == list(_INDEPENDENT_SELLER), slug
        assert seller[3] is True
        neg = next(r for r in fields if r[0] == "negotiable")
        assert [c["value"] for c in neg[5]["choices"]] == list(GOODS_NEGOTIABLE_CHOICES)
        contacts = next(r for r in fields if r[0] == "contact_methods")
        assert [c["value"] for c in contacts[5]["choices"]] == list(
            CONTACT_METHOD_CHOICES
        )
        price = next(r for r in fields if r[0] == "price")
        assert price[2].value == "price" or str(price[2]) == "price"
        assert price[3] is True


def test_price_basis_optional_11_all_kinds() -> None:
    assert MATERIALS_PRICE_BASIS_OPTIONS == _INDEPENDENT_BASIS
    cores = build_materials_v2_core_fields()
    for slug, fields in cores.items():
        basis = next(r for r in fields if r[0] == MATERIALS_PRICE_BASIS_KEY)
        assert basis[1] == "Цена за"
        assert basis[3] is False
        opts = [c["value"] for c in basis[5]["choices"]]
        assert opts == list(_INDEPENDENT_BASIS), slug


def test_condition_absent_117() -> None:
    audit = materials_v2_all_kind_audit()
    assert len(audit) == 117
    for row in audit:
        assert row["condition"] == "NO"
        assert row["condition_in_schema"] is True
        assert row["forbidden"] == []
        assert row["materials_kind_valid"] is True
        assert row["ownership"] == "MATERIALS"


def test_complexity_histogram_simple() -> None:
    hist = materials_v2_complexity_histogram()
    assert hist == {"0": 0, "1": 117, "2": 0, "3+": 0}


def test_section_kind_scopes_unique() -> None:
    seen: set[str] = set()
    for section, kinds in MATERIALS_V2_SECTION_KINDS.items():
        for kind in kinds:
            assert kind not in seen, f"duplicate kind {kind} in {section}"
            seen.add(kind)
    assert len(seen) == 117


def test_no_food_tara_kinds_invented() -> None:
    kinds = {row["kind"] for row in materials_v2_all_kind_audit()}
    for banned in (
        "Стеклянные банки",
        "Крышки",
        "Пластиковые бутылки",
        "Ящики",
        "Мешки",
        "Контейнеры",
        "Другая тара",
    ):
        assert banned not in kinds
