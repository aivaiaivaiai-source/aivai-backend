"""Medical Goods V2 Package A — Create SoT contracts + all-80 audit."""
from __future__ import annotations

from app.seeds.medical_v2 import (
    MED_CONDITION_KEY,
    MED_KIND_KEY,
    MED_SELLER_KEY,
    MEDICAL_CREATE_FORBIDDEN,
    MEDICAL_ROOT_SLUG,
    MEDICAL_SELLER_TARGET,
    MEDICAL_V2_CANONICAL_SLUGS,
    MEDICAL_V2_EXPECTED_L2_COUNT,
    MEDICAL_V2_RETIRED_SUPPLEMENT_KINDS,
    MEDICAL_V2_SECTION_KINDS,
    MEDICAL_V2_SUPPLEMENTS_STATUS,
    LICENSED_MEDICINES_BANNED,
    build_medical_v2_core_fields,
    medical_v2_all_kind_audit,
    medical_v2_assert_package_a_contracts,
    medical_v2_complexity_histogram,
    medical_v2_condition_no_kinds,
    medical_v2_condition_yes_kinds,
    medical_v2_kind_count,
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
        "Подгузники для взрослых",
        "Впитывающие пелёнки",
        "Мочеприёмники",
        "Бинты и повязки",
        "Пластыри",
        "Шприцы",
        "Инфузионные системы",
        "Медицинские перчатки",
        "Другие расходные материалы",
        "Медицинские маски",
        "Медицинские шапочки",
        "Бахилы",
        "Медицинские халаты",
        "Медицинские костюмы",
        "Медицинские колпаки",
        "Медицинская обувь",
        "Другая медицинская одежда",
        "Контактные линзы",
        "Растворы для линз",
        "Батарейки для слуховых аппаратов",
        "Тест-полоски",
        "Ланцеты",
        "Автомобильные аптечки",
        "Домашние аптечки",
        "Кровоостанавливающие жгуты",
        "Шины для иммобилизации",
        "Другие товары первой помощи",
    }
)
_INDEPENDENT_SELLER = ("Частное лицо", "Магазин", "Другой")
_FORBIDDEN_SAMPLE = (
    "brand",
    "model",
    "dosage",
    "expiry",
    "quantity",
    "pack_size",
    "manufacturer",
    "country",
    "power",
    "voltage",
    "item_type",
)


def test_package_a_contracts() -> None:
    medical_v2_assert_package_a_contracts()
    assert medical_v2_kind_count() == 80
    assert MEDICAL_V2_EXPECTED_L2_COUNT == 15
    assert MEDICAL_SELLER_TARGET == GOODS_SELLER_CHOICES
    assert "Аптека" not in MEDICAL_SELLER_TARGET
    assert "Компания" not in MEDICAL_SELLER_TARGET
    assert MEDICAL_V2_SUPPLEMENTS_STATUS == "RETIRED_NO_CANONICAL_DESTINATION"


def test_15_l2_nonempty_cores_root_empty() -> None:
    cores = build_medical_v2_core_fields()
    assert set(cores.keys()) == MEDICAL_V2_CANONICAL_SLUGS
    assert len(cores) == 15
    assert MEDICAL_ROOT_SLUG not in cores
    for slug, fields in cores.items():
        keys = [r[0] for r in fields]
        assert MED_KIND_KEY in keys, slug
        assert MED_SELLER_KEY in keys, slug
        assert "price" in keys, slug
        assert "negotiable" in keys, slug
        assert "contact_methods" in keys, slug
        assert not (set(keys) & MEDICAL_CREATE_FORBIDDEN), slug
        kind_row = field_row_by_key(fields, MED_KIND_KEY)
        assert kind_row[1] == "Товар"
        opts = extract_choice_values(options_from_field_row(kind_row))
        assert opts and len(opts) > 0, f"empty picker {slug}"


def test_shared_goods_contract_parity() -> None:
    cores = build_medical_v2_core_fields()
    sample = cores["medical-meditsinskie-pribory"]
    for key in ("seller_type", "price", "negotiable", "contact_methods"):
        assert_field_matches_canonical(
            domain="medical",
            field_key=key,
            row=field_row_by_key(sample, key),
        )
    assert extract_choice_values(
        options_from_field_row(field_row_by_key(sample, "contact_methods"))
    ) == CONTACT_METHOD_CHOICES
    assert extract_choice_values(
        options_from_field_row(field_row_by_key(sample, "negotiable"))
    ) == GOODS_NEGOTIABLE_CHOICES
    assert extract_choice_values(
        options_from_field_row(field_row_by_key(sample, MED_SELLER_KEY))
    ) == _INDEPENDENT_SELLER


def test_condition_independent_matrix_53_27() -> None:
    yes = medical_v2_condition_yes_kinds()
    no = medical_v2_condition_no_kinds()
    assert no == _INDEPENDENT_NO
    assert len(yes) == 53
    assert len(no) == 27
    assert yes.isdisjoint(no)


def test_condition_absent_for_clothing_firstaid_consumables() -> None:
    cores = build_medical_v2_core_fields()
    for slug in (
        "medical-meditsinskaya-odezhda",
        "medical-aptechki-i-pervaya-pomosch",
        "medical-rashodnye-med-materialy",
    ):
        keys = [r[0] for r in cores[slug]]
        assert MED_CONDITION_KEY not in keys, slug


def test_condition_depends_on_for_mixed_sections() -> None:
    cores = build_medical_v2_core_fields()
    optics = cores["medical-optika-i-tovary-dlya-zreniya"]
    cond = field_row_by_key(optics, MED_CONDITION_KEY)
    assert cond is not None
    dep = (options_from_field_row(cond) or {}).get("depends_on") or {}
    assert dep.get("field") == MED_KIND_KEY
    values = set(dep.get("values") or [])
    assert "Очки для зрения" in values
    assert "Оправы" in values
    assert "Футляры для очков" in values
    assert "Контактные линзы" not in values
    assert "Растворы для линз" not in values

    care = cores["medical-tovary-dlya-uhoda-za-bolnymi"]
    care_cond = field_row_by_key(care, MED_CONDITION_KEY)
    care_values = set(
        ((options_from_field_row(care_cond) or {}).get("depends_on") or {}).get(
            "values"
        )
        or []
    )
    assert "Противопролежневые матрасы" in care_values
    assert "Подгузники для взрослых" not in care_values


def test_all_80_audit_independent() -> None:
    rows = medical_v2_all_kind_audit()
    assert len(rows) == 80
    for row in rows:
        assert row["med_kind_valid"] is True
        assert row["price"] is True
        assert tuple(row["seller"]) == _INDEPENDENT_SELLER
        assert row["forbidden"] == []
        assert row["condition_in_schema"] is True
        assert row["ownership"] == "MEDICAL"
        if row["kind"] in _INDEPENDENT_NO:
            assert row["condition"] == "NO"
            assert row["special_count"] == 0
        else:
            assert row["condition"] == "YES"
            assert row["special_count"] == 1
        for tech in _FORBIDDEN_SAMPLE:
            assert tech not in row["components"]
        assert row["kind"] not in LICENSED_MEDICINES_BANNED
        assert row["kind"] not in MEDICAL_V2_RETIRED_SUPPLEMENT_KINDS


def test_complexity_histogram_simple() -> None:
    hist = medical_v2_complexity_histogram()
    assert hist["0"] == 27
    assert hist["1"] == 53
    assert hist["2"] == 0
    assert hist["3+"] == 0


def test_kind_catalog_exact_section_authority() -> None:
    cores = build_medical_v2_core_fields()
    for section_key, kinds in MEDICAL_V2_SECTION_KINDS.items():
        from app.seeds.medical_v2 import MEDICAL_V2_SECTION_SLUGS

        slug = MEDICAL_V2_SECTION_SLUGS[section_key]
        kind_row = field_row_by_key(cores[slug], MED_KIND_KEY)
        opts = extract_choice_values(options_from_field_row(kind_row))
        assert opts == tuple(kinds)
