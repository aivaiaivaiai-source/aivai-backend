"""Beauty & Personal Care V2 Package A — Create SoT contracts + all-99 audit."""
from __future__ import annotations

from app.seeds.shared_goods_create_contract import (
    CONTACT_METHOD_CHOICES,
    GOODS_NEGOTIABLE_CHOICES,
    GOODS_SELLER_CHOICES,
)
from app.seeds.beauty_v2 import (
    BEAUTY_CONDITION_KEY,
    BEAUTY_CREATE_FORBIDDEN,
    BEAUTY_KIND_KEY,
    BEAUTY_KIND_LABEL,
    BEAUTY_ROOT_SLUG,
    BEAUTY_SELLER_KEY,
    BEAUTY_SELLER_OPTIONS,
    BEAUTY_V2_CANONICAL_SLUGS,
    BEAUTY_V2_EXPECTED_L2_COUNT,
    BEAUTY_V2_SECTION_KINDS,
    BEAUTY_V2_SECTION_META,
    build_beauty_v2_core_fields,
    beauty_v2_all_kind_audit,
    beauty_v2_assert_package_a_contracts,
    beauty_v2_assert_package_b_prep,
    beauty_v2_complexity_histogram,
    beauty_v2_condition_decision,
    beauty_v2_condition_matrix,
    beauty_v2_kind_count,
)

# Independent 99-kind Condition expectation — cannot certify production allowlist
# from itself. YES = durable reusable devices/tools only.
_INDEPENDENT_CONDITION_YES = frozenset(
    {
        "Фены",
        "Плойки и выпрямители",
        "Домашние машинки для стрижки",
        "Электробритвы",
        "Эпиляторы",
        "Лампы для маникюра",
        "Аппараты для маникюра",
        "Воскоплавы",
        "Другие персональные устройства для красоты",
        "Машинки для барберов",
        "Ножницы для барберов",
        "Опасные бритвы",
        "Другие товары для барбершопов",
        "Машинки для тату",
        "Другие товары для тату",
        "Парики и шиньоны",
        "Косметические зеркала",
        "Другие товары для красоты",
    }
)


def test_package_a_contracts() -> None:
    beauty_v2_assert_package_a_contracts()
    beauty_v2_assert_package_b_prep()
    assert beauty_v2_kind_count() == 99
    assert BEAUTY_V2_EXPECTED_L2_COUNT == 16
    assert BEAUTY_KIND_KEY == "beauty_kind"
    assert BEAUTY_KIND_LABEL == "Товар"
    assert BEAUTY_SELLER_OPTIONS == GOODS_SELLER_CHOICES
    assert beauty_v2_condition_matrix() == {"YES": 18, "NO": 81}


def test_16_l2_nonempty_cores_root_empty() -> None:
    cores = build_beauty_v2_core_fields()
    assert set(cores.keys()) == BEAUTY_V2_CANONICAL_SLUGS
    assert len(cores) == 16
    assert BEAUTY_ROOT_SLUG not in cores
    for slug, fields in cores.items():
        keys = [r[0] for r in fields]
        assert BEAUTY_KIND_KEY in keys, slug
        assert BEAUTY_SELLER_KEY in keys, slug
        assert "price" in keys, slug
        assert "negotiable" in keys, slug
        assert "contact_methods" in keys, slug
        assert set(keys).isdisjoint(
            {
                "beauty_brand",
                "beauty_model",
                "volume",
                "package_state",
                "price_basis",
                "spf",
                "shade",
                "size",
            }
        )
        kind = next(r for r in fields if r[0] == BEAUTY_KIND_KEY)
        assert kind[1] == "Товар"
        assert kind[3] is True
        seller = next(r for r in fields if r[0] == BEAUTY_SELLER_KEY)
        assert [c["value"] for c in seller[5]["choices"]] == list(GOODS_SELLER_CHOICES)


def test_condition_matrix_in_cores_independent() -> None:
    cores = build_beauty_v2_core_fields()
    for section_key, kinds in BEAUTY_V2_SECTION_KINDS.items():
        slug = BEAUTY_V2_SECTION_META[section_key][0]
        keys = [r[0] for r in cores[slug]]
        yes_kinds = [k for k in kinds if beauty_v2_condition_decision(k) == "YES"]
        no_kinds = [k for k in kinds if beauty_v2_condition_decision(k) == "NO"]
        if not yes_kinds:
            assert BEAUTY_CONDITION_KEY not in keys, slug
        else:
            assert BEAUTY_CONDITION_KEY in keys, slug
            cond = next(r for r in cores[slug] if r[0] == BEAUTY_CONDITION_KEY)
            assert cond[1] == "Состояние"
            assert cond[3] is False
            assert [c["value"] for c in cond[5]["choices"]] == ["Новое", "Б/у"]
            if no_kinds:
                depends = cond[5].get("depends_on") or {}
                assert depends.get("field") == BEAUTY_KIND_KEY
                assert set(depends.get("values") or []) == set(yes_kinds)
            else:
                assert "depends_on" not in (cond[5] or {})


def test_independent_condition_yes_table() -> None:
    assert len(_INDEPENDENT_CONDITION_YES) == 18
    for kind in _INDEPENDENT_CONDITION_YES:
        assert beauty_v2_condition_decision(kind) == "YES", kind
    for row in beauty_v2_all_kind_audit():
        expected = "YES" if row["kind"] in _INDEPENDENT_CONDITION_YES else "NO"
        assert row["condition"] == expected, row["kind"]


def test_shared_negotiable_contacts_price() -> None:
    cores = build_beauty_v2_core_fields()
    for slug, fields in cores.items():
        neg = next(r for r in fields if r[0] == "negotiable")
        assert [c["value"] for c in neg[5]["choices"]] == list(GOODS_NEGOTIABLE_CHOICES)
        contacts = next(r for r in fields if r[0] == "contact_methods")
        assert [c["value"] for c in contacts[5]["choices"]] == list(
            CONTACT_METHOD_CHOICES
        )
        price = next(r for r in fields if r[0] == "price")
        assert price[2].value == "price" or str(price[2]) == "price"
        assert price[3] is True


def test_all_99_audit() -> None:
    audit = beauty_v2_all_kind_audit()
    assert len(audit) == 99
    for row in audit:
        assert row["kind_valid"] is True
        assert row["condition_in_schema"] is True
        assert row["forbidden"] == []
        assert row["price"] is True
        assert row["seller"] == list(GOODS_SELLER_CHOICES)
        assert row["package_state"] == "ABSENT"
        assert row["brand"] == "NO"
        assert row["model"] == "NO"
        assert row["volume"] == "NO"
        assert row["special_count"] <= 1
        assert row["platform_owner"] == "BEAUTY"
        assert "Косметички" != row["kind"]
        assert "Украшения для пирсинга" != row["kind"]


def test_complexity_histogram_simple() -> None:
    hist = beauty_v2_complexity_histogram()
    assert hist["2"] == 0
    assert hist["3+"] == 0
    assert hist["0"] == 81
    assert hist["1"] == 18
    assert hist["0"] + hist["1"] == 99


def test_forbidden_and_ownership_locks() -> None:
    assert "package_state" in BEAUTY_CREATE_FORBIDDEN
    assert "beauty_brand" in BEAUTY_CREATE_FORBIDDEN
    assert "volume" in BEAUTY_CREATE_FORBIDDEN
    audit = {r["kind"]: r for r in beauty_v2_all_kind_audit()}
    assert audit["Фены"]["ownership"] == "DURABLE_BEAUTY_DEVICE"
    assert audit["Парики и шиньоны"]["ownership"] == "WIG_BEAUTY"
    assert audit["Духи"]["condition"] == "NO"
    assert audit["Машинки для тату"]["condition"] == "YES"
    assert "Кресло барбера" not in audit
    assert "Косметички" not in audit
