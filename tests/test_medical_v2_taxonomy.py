"""Medical Goods V2 taxonomy + platform coherence (pre–Package A)."""
from __future__ import annotations

from app.seeds.business_equipment_v2 import BUSINESS_EQUIPMENT_MEDICAL_BOUNDARY
from app.seeds.business_sections_catalog import BUSINESS_SECTIONS
from app.seeds.electronics_sections_catalog import ELECTRONICS_SECTIONS
from app.seeds.fashion_sections_catalog import FASHION_SECTIONS
from app.seeds.kids_sections_catalog import KIDS_SECTIONS
from app.seeds.med_sections_catalog import MED_SECTIONS
from app.seeds.medical_v2 import (
    BE_CLINIC_KINDS_NOT_IN_MEDICAL,
    KIDS_KINDS_NOT_IN_MEDICAL,
    LICENSED_MEDICINES_BANNED,
    MEDICAL_CONDITION_OPTIONS,
    MEDICAL_CREATE_FORBIDDEN,
    MEDICAL_DEVICES_CANONICAL_LABEL,
    MEDICAL_DEVICES_CANONICAL_SLUG,
    MEDICAL_KEEPS_MASSAGE_CHAIRS,
    MEDICAL_ROOT_LABEL,
    MEDICAL_ROOT_SLUG,
    MEDICAL_SELLER_TARGET,
    MEDICAL_V2_CANONICAL_LEAVES,
    MEDICAL_V2_CANONICAL_SLUGS,
    MEDICAL_V2_EXPECTED_L2_COUNT,
    MEDICAL_V2_LEGACY_RETIRED_SLUGS,
    MEDICAL_V2_RETIRED_SLUGS,
    MEDICAL_V2_RETIRED_SUPPLEMENT_KINDS,
    MEDICAL_V2_SECTION_KINDS,
    MEDICAL_V2_SUPPLEMENTS_SLUG,
    MEDICAL_V2_SUPPLEMENTS_STATUS,
    medical_v2_all_kinds,
    medical_v2_assert_cleanup_contracts,
    medical_v2_condition_decision,
    medical_v2_condition_no_kinds,
    medical_v2_condition_yes_kinds,
    medical_v2_kind_count,
)
from app.seeds.repair_sections_catalog import REPAIR_SECTIONS
from app.seeds.services_rest_catalog import SERVICE_SECTIONS


def _kinds(sections: dict) -> set[str]:
    out: set[str] = set()
    for catalog in sections.values():
        for role in catalog["roles"]:
            out.add(role["label"])
    return out


def test_medical_v2_cleanup_contracts() -> None:
    medical_v2_assert_cleanup_contracts()
    assert MEDICAL_ROOT_SLUG == "medical"
    assert MEDICAL_ROOT_LABEL == "Медтовары"
    assert MEDICAL_V2_EXPECTED_L2_COUNT == 15
    assert len(MEDICAL_V2_CANONICAL_LEAVES) == 15
    assert len(MED_SECTIONS) == 15
    assert medical_v2_kind_count() == 80
    assert MEDICAL_V2_LEGACY_RETIRED_SLUGS == {
        "medical-devices",
        "medical-care",
    }
    assert MEDICAL_V2_SUPPLEMENTS_SLUG in MEDICAL_V2_RETIRED_SLUGS
    assert MEDICAL_V2_SUPPLEMENTS_STATUS == "RETIRED_NO_CANONICAL_DESTINATION"
    assert MEDICAL_V2_LEGACY_RETIRED_SLUGS.isdisjoint(MEDICAL_V2_CANONICAL_SLUGS)
    assert MEDICAL_V2_SUPPLEMENTS_SLUG not in MEDICAL_V2_CANONICAL_SLUGS


def test_medical_dual_tree_retired_single_devices_direction() -> None:
    devices = [
        (label, slug)
        for label, slug, _sort in MEDICAL_V2_CANONICAL_LEAVES
        if label == MEDICAL_DEVICES_CANONICAL_LABEL
    ]
    assert devices == [(MEDICAL_DEVICES_CANONICAL_LABEL, MEDICAL_DEVICES_CANONICAL_SLUG)]
    assert "medical-devices" in MEDICAL_V2_LEGACY_RETIRED_SLUGS
    assert "medical-care" in MEDICAL_V2_LEGACY_RETIRED_SLUGS
    assert "БАДы и товары для здоровья" not in {
        cat["label"] for cat in MED_SECTIONS.values()
    }
    assert "supplements" not in MED_SECTIONS


def test_medical_medicines_absent() -> None:
    kinds = set(medical_v2_all_kinds())
    assert LICENSED_MEDICINES_BANNED.isdisjoint(kinds)
    assert MEDICAL_V2_RETIRED_SUPPLEMENT_KINDS.isdisjoint(kinds)


def test_medical_supplements_retired() -> None:
    assert MEDICAL_V2_SUPPLEMENTS_SLUG == "medical-bady-i-tovary-dlya-zdorovya"
    for kind in MEDICAL_V2_RETIRED_SUPPLEMENT_KINDS:
        assert kind not in medical_v2_all_kinds()


def test_medical_seller_target_canonical_goods() -> None:
    assert MEDICAL_SELLER_TARGET == ("Частное лицо", "Магазин", "Другой")
    assert "Аптека" not in MEDICAL_SELLER_TARGET
    assert "Компания" not in MEDICAL_SELLER_TARGET
    for catalog in MED_SECTIONS.values():
        seller = next(g for g in catalog["filters"] if g["label"] == "Продавец")
        assert [o["label"] for o in seller["options"]] == list(MEDICAL_SELLER_TARGET)


def test_medical_condition_independent_matrix() -> None:
    kinds = medical_v2_all_kinds()
    yes = medical_v2_condition_yes_kinds()
    no = medical_v2_condition_no_kinds()
    assert yes | no == set(kinds)
    assert not (yes & no)
    # Independent expectations — do not derive from production helper alone.
    independent_no = {
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
    assert no == independent_no
    assert medical_v2_condition_decision("Тонометры") == "YES"
    assert medical_v2_condition_decision("Очки для зрения") == "YES"
    assert medical_v2_condition_decision("Оправы") == "YES"
    assert medical_v2_condition_decision("Шприцы") == "NO"
    assert medical_v2_condition_decision("Медицинские халаты") == "NO"
    assert medical_v2_condition_decision("Домашние аптечки") == "NO"
    assert MEDICAL_CONDITION_OPTIONS == ("Новое", "Б/у")
    # Clothing / firstaid / consumables omit Condition (all kinds NO).
    for key in ("clothing", "firstaid", "consumables"):
        labels = [g["label"] for g in MED_SECTIONS[key]["filters"]]
        assert labels == ["Продавец"]
        assert all(
            medical_v2_condition_decision(k) == "NO"
            for k in MEDICAL_V2_SECTION_KINDS[key]
        )


def test_medical_simple_field_target() -> None:
    assert MEDICAL_CREATE_FORBIDDEN >= {
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
    }


def test_medical_business_equipment_boundary() -> None:
    med = set(medical_v2_all_kinds())
    be = _kinds(BUSINESS_SECTIONS)
    assert BE_CLINIC_KINDS_NOT_IN_MEDICAL.isdisjoint(med)
    for kind in BE_CLINIC_KINDS_NOT_IN_MEDICAL:
        assert kind in be
    for kind, owner in BUSINESS_EQUIPMENT_MEDICAL_BOUNDARY.items():
        if owner == "BUSINESS_EQUIPMENT":
            assert kind in be
            assert kind not in med
        if owner == "MEDICAL":
            assert kind in med
            assert kind not in be


def test_medical_electronics_boundary() -> None:
    med = set(medical_v2_all_kinds())
    el = _kinds(ELECTRONICS_SECTIONS)
    medical_devices = {
        "Тонометры",
        "Глюкометры",
        "Пульсоксиметры",
        "Небулайзеры",
        "Градусники",
        "Слуховые аппараты",
    }
    assert medical_devices <= med
    assert medical_devices.isdisjoint(el)


def test_medical_beauty_massage_boundary() -> None:
    assert MEDICAL_KEEPS_MASSAGE_CHAIRS is True
    assert "Массажные кресла" in medical_v2_all_kinds()
    # Personal beauty cosmetics stay Beauty — not asserted by inventing moves.


def test_medical_services_kids_vet_boundaries() -> None:
    med = set(medical_v2_all_kinds())
    kids = _kinds(KIDS_SECTIONS)
    assert KIDS_KINDS_NOT_IN_MEDICAL.isdisjoint(med)
    # Kids owns generic diapers; Medical owns adult diapers.
    assert "Подгузники для взрослых" in med
    assert "Подгузники" not in med
    # No medical procedure/service kinds in Medical goods catalog.
    for banned in ("Массаж", "Реабилитация", "Уход за больными", "Медсестра"):
        assert banned not in med
    # Fashion/Repair PPE — medical clinical PPE stays Medical.
    fashion = _kinds(FASHION_SECTIONS)
    repair = _kinds(REPAIR_SECTIONS)
    assert "Медицинские маски" in med
    assert "Медицинские маски" not in fashion
    assert "Медицинские перчатки" in med
    assert "Медицинские перчатки" not in repair
    # Services remain Services (rest catalog present; goods kinds stay Medical-only).
    assert "Медицинские кушетки" not in med
    assert SERVICE_SECTIONS
    service_labels = {
        str(k)
        for sec in SERVICE_SECTIONS.values()
        for k in (sec.get("kinds") or [])
    }
    assert "Тонометры" not in service_labels
    assert "Медицинские кровати" not in service_labels


def test_medical_root_picker_and_catalog_shape() -> None:
    assert MEDICAL_ROOT_SLUG == "medical"
    for key, catalog in MED_SECTIONS.items():
        assert catalog["category_slug"] in MEDICAL_V2_CANONICAL_SLUGS
        assert catalog["question"] == "Какой товар?"
        roles = [r["label"] for r in catalog["roles"]]
        assert roles == list(MEDICAL_V2_SECTION_KINDS[key])
        assert roles[-1].startswith("Друг")
        seller = catalog["filters"][0]
        assert seller["label"] == "Продавец"
