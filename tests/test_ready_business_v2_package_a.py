"""Ready Business V2 Package A — Create SoT contracts + all-70 audit."""
from __future__ import annotations

from app.seeds.ready_business_v2 import (
    READY_BUSINESS_CREATE_FORBIDDEN,
    READY_BUSINESS_FRANCHISE_SLUG,
    READY_BUSINESS_KIND_KEY,
    READY_BUSINESS_KIND_LABEL,
    READY_BUSINESS_POSTER_KEY,
    READY_BUSINESS_POSTER_OPTIONS,
    READY_BUSINESS_PREMISES_KEY,
    READY_BUSINESS_PREMISES_OPTIONS,
    READY_BUSINESS_ROOT_SLUG,
    READY_BUSINESS_V2_CANONICAL_SLUGS,
    READY_BUSINESS_V2_EXPECTED_L2_COUNT,
    READY_BUSINESS_V2_SECTION_KINDS,
    build_ready_business_v2_core_fields,
    ready_business_v2_all_kind_audit,
    ready_business_v2_assert_package_a_contracts,
    ready_business_v2_complexity_histogram,
    ready_business_v2_kind_count,
    ready_business_v2_premises_decision,
)
from app.seeds.shared_goods_create_contract import (
    CONTACT_METHOD_CHOICES,
    GOODS_NEGOTIABLE_CHOICES,
)

_FORBIDDEN_SAMPLE = (
    "condition",
    "business_type",
    "seller_type",
    "revenue",
    "profit",
    "payback",
    "royalty",
    "investment",
    "staff_count",
    "area",
    "rent_amount",
)


def test_package_a_contracts() -> None:
    ready_business_v2_assert_package_a_contracts()
    assert ready_business_v2_kind_count() == 70
    assert READY_BUSINESS_V2_EXPECTED_L2_COUNT == 16
    assert READY_BUSINESS_KIND_KEY == "ready_business_kind"
    assert READY_BUSINESS_KIND_LABEL == "Вид бизнеса"
    assert READY_BUSINESS_POSTER_OPTIONS == ("Владелец", "Представитель", "Другой")
    assert READY_BUSINESS_PREMISES_OPTIONS == (
        "В собственности",
        "В аренде",
        "Без помещения",
    )


def test_16_l2_nonempty_cores_root_empty() -> None:
    cores = build_ready_business_v2_core_fields()
    assert set(cores.keys()) == READY_BUSINESS_V2_CANONICAL_SLUGS
    assert len(cores) == 16
    assert READY_BUSINESS_ROOT_SLUG not in cores
    for slug, fields in cores.items():
        keys = [r[0] for r in fields]
        assert READY_BUSINESS_KIND_KEY in keys, slug
        assert READY_BUSINESS_POSTER_KEY in keys, slug
        assert "price" in keys, slug
        assert "negotiable" in keys, slug
        assert "contact_methods" in keys, slug
        assert "condition" not in keys, slug
        assert "seller_type" not in keys, slug
        assert set(keys).isdisjoint(_FORBIDDEN_SAMPLE)
        kind = next(r for r in fields if r[0] == READY_BUSINESS_KIND_KEY)
        assert kind[1] == "Вид бизнеса"
        assert kind[3] is True
        poster = next(r for r in fields if r[0] == READY_BUSINESS_POSTER_KEY)
        assert poster[1] == "Кто разместил"
        assert [c["value"] for c in poster[5]["choices"]] == list(
            READY_BUSINESS_POSTER_OPTIONS
        )


def test_premises_matrix_in_cores() -> None:
    from app.seeds.ready_business_v2 import _SECTION_SPECS

    cores = build_ready_business_v2_core_fields()
    for section_key, kinds in READY_BUSINESS_V2_SECTION_KINDS.items():
        slug = _SECTION_SPECS[section_key][0]
        keys = [r[0] for r in cores[slug]]
        decisions = {ready_business_v2_premises_decision(k) for k in kinds}
        if decisions == {"YES"}:
            assert READY_BUSINESS_PREMISES_KEY in keys, slug
            premises = next(
                r for r in cores[slug] if r[0] == READY_BUSINESS_PREMISES_KEY
            )
            assert premises[1] == "Помещение"
            assert premises[3] is False
            assert [c["value"] for c in premises[5]["choices"]] == list(
                READY_BUSINESS_PREMISES_OPTIONS
            )
        elif decisions == {"NO"}:
            assert READY_BUSINESS_PREMISES_KEY not in keys, slug
        else:
            raise AssertionError(f"mixed premises in {section_key}: {decisions}")


def test_franchise_no_finance_and_entry_price_hint() -> None:
    cores = build_ready_business_v2_core_fields()
    fields = cores[READY_BUSINESS_FRANCHISE_SLUG]
    keys = [r[0] for r in fields]
    assert READY_BUSINESS_PREMISES_KEY not in keys
    assert set(keys).isdisjoint(
        {"royalty", "investment", "payback", "franchise_support", "condition"}
    )
    price = next(r for r in fields if r[0] == "price")
    assert "франшиз" in (price[6] or "").lower()


def test_shared_negotiable_contacts_price() -> None:
    cores = build_ready_business_v2_core_fields()
    for slug, fields in cores.items():
        neg = next(r for r in fields if r[0] == "negotiable")
        assert [c["value"] for c in neg[5]["choices"]] == list(
            GOODS_NEGOTIABLE_CHOICES
        )
        contacts = next(r for r in fields if r[0] == "contact_methods")
        assert [c["value"] for c in contacts[5]["choices"]] == list(
            CONTACT_METHOD_CHOICES
        )
        price = next(r for r in fields if r[0] == "price")
        assert price[2].value == "price" or str(price[2]) == "price"
        assert price[3] is True


def test_all_70_audit() -> None:
    audit = ready_business_v2_all_kind_audit()
    assert len(audit) == 70
    for row in audit:
        assert row["kind_valid"] is True
        assert row["condition"] == "NO"
        assert row["condition_in_schema"] is True
        assert row["forbidden"] == []
        assert row["price"] is True
        assert row["poster"] == list(READY_BUSINESS_POSTER_OPTIONS)
        assert row["ownership"] in ("READY_BUSINESS", "FRANCHISE")
        if row["premises"] == "YES":
            assert row["premises_in_schema"] is True
        else:
            assert row["premises_in_schema"] is False
        assert row["special_count"] <= 1


def test_complexity_histogram_simple() -> None:
    hist = ready_business_v2_complexity_histogram()
    assert hist["2"] == 0
    assert hist["3+"] == 0
    assert hist["0"] + hist["1"] == 70


def test_section_kind_scopes_unique() -> None:
    seen: set[str] = set()
    for section, kinds in READY_BUSINESS_V2_SECTION_KINDS.items():
        for kind in kinds:
            assert kind not in seen, f"duplicate kind {kind} in {section}"
            seen.add(kind)
    assert len(seen) == 70
    assert "condition" in READY_BUSINESS_CREATE_FORBIDDEN
    assert "revenue" in READY_BUSINESS_CREATE_FORBIDDEN
