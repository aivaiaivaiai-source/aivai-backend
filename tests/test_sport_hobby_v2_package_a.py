"""Sport / Hobby V2 Package A — Create SoT contracts + all-96 audit."""
from __future__ import annotations

from app.seeds.shared_goods_create_contract import (
    CONTACT_METHOD_CHOICES,
    GOODS_NEGOTIABLE_CHOICES,
    GOODS_SELLER_CHOICES,
)
from app.seeds.sport_v2 import (
    SPORT_CONDITION_KEY,
    SPORT_CREATE_FORBIDDEN,
    SPORT_KIND_KEY,
    SPORT_KIND_LABEL,
    SPORT_ROOT_SLUG,
    SPORT_SELLER_KEY,
    SPORT_SELLER_OPTIONS,
    SPORT_V2_CANONICAL_SLUGS,
    SPORT_V2_EXPECTED_L2_COUNT,
    SPORT_V2_SECTION_KINDS,
    build_sport_v2_core_fields,
    sport_v2_all_kind_audit,
    sport_v2_assert_package_a_contracts,
    sport_v2_complexity_histogram,
    sport_v2_condition_decision,
    sport_v2_condition_matrix,
    sport_v2_kind_count,
)

_INDEPENDENT_CONDITION_NO = frozenset(
    {
        "Протеин",
        "Гейнеры",
        "Креатин",
        "Аминокислоты",
        "Изотоники",
        "Спортивные батончики",
        "Другое спортивное питание",
        "Блёсны и приманки",
        "Бисер",
        "Валяние",
        "Мыловарение",
    }
)


def test_package_a_contracts() -> None:
    sport_v2_assert_package_a_contracts()
    assert sport_v2_kind_count() == 96
    assert SPORT_V2_EXPECTED_L2_COUNT == 13
    assert SPORT_KIND_KEY == "sport_kind"
    assert SPORT_KIND_LABEL == "Товар"
    assert SPORT_SELLER_OPTIONS == GOODS_SELLER_CHOICES
    assert sport_v2_condition_matrix() == {"YES": 85, "NO": 11}


def test_13_l2_nonempty_cores_root_empty() -> None:
    cores = build_sport_v2_core_fields()
    assert set(cores.keys()) == SPORT_V2_CANONICAL_SLUGS
    assert len(cores) == 13
    assert SPORT_ROOT_SLUG not in cores
    for slug, fields in cores.items():
        keys = [r[0] for r in fields]
        assert SPORT_KIND_KEY in keys, slug
        assert SPORT_SELLER_KEY in keys, slug
        assert "price" in keys, slug
        assert "negotiable" in keys, slug
        assert "contact_methods" in keys, slug
        assert set(keys).isdisjoint(
            {"size", "brand", "model", "weight", "price_basis", "level"}
        )
        kind = next(r for r in fields if r[0] == SPORT_KIND_KEY)
        assert kind[1] == "Товар"
        assert kind[3] is True
        seller = next(r for r in fields if r[0] == SPORT_SELLER_KEY)
        assert [c["value"] for c in seller[5]["choices"]] == list(GOODS_SELLER_CHOICES)


def test_condition_matrix_in_cores_independent() -> None:
    cores = build_sport_v2_core_fields()
    for section_key, kinds in SPORT_V2_SECTION_KINDS.items():
        from app.seeds.sport_v2 import SPORT_V2_SECTION_META

        slug = SPORT_V2_SECTION_META[section_key][0]
        keys = [r[0] for r in cores[slug]]
        yes_kinds = [k for k in kinds if sport_v2_condition_decision(k) == "YES"]
        no_kinds = [k for k in kinds if sport_v2_condition_decision(k) == "NO"]
        if not yes_kinds:
            assert SPORT_CONDITION_KEY not in keys, slug
            assert section_key == "nutrition"
        else:
            assert SPORT_CONDITION_KEY in keys, slug
            cond = next(r for r in cores[slug] if r[0] == SPORT_CONDITION_KEY)
            assert cond[1] == "Состояние"
            assert cond[3] is False
            assert [c["value"] for c in cond[5]["choices"]] == ["Новое", "Б/у"]
            if no_kinds:
                depends = cond[5].get("depends_on") or {}
                assert depends.get("field") == SPORT_KIND_KEY
                assert set(depends.get("values") or []) == set(yes_kinds)
            else:
                assert "depends_on" not in (cond[5] or {})


def test_independent_condition_no_table() -> None:
    for kind in _INDEPENDENT_CONDITION_NO:
        assert sport_v2_condition_decision(kind) == "NO", kind
    assert len(_INDEPENDENT_CONDITION_NO) == 11
    for kind in sport_v2_all_kind_audit():
        expected = "NO" if kind["kind"] in _INDEPENDENT_CONDITION_NO else "YES"
        assert kind["condition"] == expected


def test_shared_negotiable_contacts_price() -> None:
    cores = build_sport_v2_core_fields()
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


def test_all_96_audit() -> None:
    audit = sport_v2_all_kind_audit()
    assert len(audit) == 96
    for row in audit:
        assert row["kind_valid"] is True
        assert row["condition_in_schema"] is True
        assert row["forbidden"] == []
        assert row["price"] is True
        assert row["seller"] == list(GOODS_SELLER_CHOICES)
        assert row["size"] == "NO"
        assert row["brand"] == "NO"
        assert row["tech"] == "NO"
        assert row["special_count"] <= 1
        assert row["platform_owner"] == "SPORT_HOBBY"
        assert row["weapons"] is False
        assert row["retired_resurrected"] is False


def test_complexity_histogram_simple() -> None:
    hist = sport_v2_complexity_histogram()
    assert hist["2"] == 0
    assert hist["3+"] == 0
    assert hist["0"] == 11
    assert hist["1"] == 85
    assert hist["0"] + hist["1"] == 96


def test_forbidden_and_echo_music() -> None:
    assert "size" in SPORT_CREATE_FORBIDDEN
    assert "price_basis" in SPORT_CREATE_FORBIDDEN
    audit = {r["kind"]: r for r in sport_v2_all_kind_audit()}
    assert audit["Эхолоты"]["ownership"] == "FISHING_GOOD"
    assert audit["Синтезаторы"]["ownership"] == "MUSIC_INSTRUMENT"
    assert audit["Сёдла"]["ownership"] == "HORSE_GEAR"
    assert "Охотничьи ножи" not in audit
    assert "Юрты" not in audit
