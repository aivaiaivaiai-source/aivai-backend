"""Business Equipment V2 taxonomy + platform coherence (pre–Package A)."""
from __future__ import annotations

from app.seeds.business_equipment_v2 import (
    BUSINESS_EQUIPMENT_ELECTRONICS_BOUNDARY,
    BUSINESS_EQUIPMENT_MEDICAL_BOUNDARY,
    BUSINESS_EQUIPMENT_REPAIR_BOUNDARY,
    BUSINESS_EQUIPMENT_ROOT_LABEL,
    BUSINESS_EQUIPMENT_ROOT_SLUG,
    BUSINESS_EQUIPMENT_SELLER_TARGET,
    BUSINESS_EQUIPMENT_V2_CANONICAL_LEAVES,
    BUSINESS_EQUIPMENT_V2_CANONICAL_SLUGS,
    BUSINESS_EQUIPMENT_V2_EXPECTED_L2_COUNT,
    BUSINESS_EQUIPMENT_V2_LEGACY_RETIRED_SLUGS,
    BUSINESS_PACKING_IS_EQUIPMENT_NOT_TARA,
    FOOD_TARA_GOODS_NOT_BUSINESS_EQUIPMENT,
    PLOTTER_KIND,
    REPAIR_GENERIC_COMPRESSOR_KIND,
    STO_COMPRESSOR_KIND,
    TRADE_CANONICAL_LABEL,
    TRADE_CANONICAL_SLUG,
    business_equipment_v2_all_kinds,
    business_equipment_v2_assert_cleanup_contracts,
    business_equipment_v2_assert_platform_coherence,
    business_equipment_v2_condition_matrix,
    business_equipment_v2_condition_no_kinds,
    business_equipment_v2_condition_yes_kinds,
    business_equipment_v2_kind_count,
)
from app.seeds.business_sections_catalog import BUSINESS_SECTIONS
from app.seeds.electronics_sections_catalog import ELECTRONICS_SECTIONS
from app.seeds.food_agri_v2 import FOOD_AGRI_TARA_NOT_BUSINESS_EQUIPMENT_REASON
from app.seeds.med_sections_catalog import MED_SECTIONS
from app.seeds.repair_sections_catalog import REPAIR_SECTIONS


def _kinds(sections: dict) -> set[str]:
    out: set[str] = set()
    for catalog in sections.values():
        for role in catalog["roles"]:
            out.add(role["label"])
    return out


def test_business_equipment_v2_cleanup_contracts() -> None:
    business_equipment_v2_assert_cleanup_contracts()
    business_equipment_v2_assert_platform_coherence()
    assert BUSINESS_EQUIPMENT_ROOT_SLUG == "business-equipment"
    assert BUSINESS_EQUIPMENT_ROOT_LABEL == "Бизнес-оборудование"
    assert BUSINESS_EQUIPMENT_V2_EXPECTED_L2_COUNT == 20
    assert len(BUSINESS_EQUIPMENT_V2_CANONICAL_LEAVES) == 20
    assert business_equipment_v2_kind_count() == 176
    assert BUSINESS_EQUIPMENT_V2_LEGACY_RETIRED_SLUGS == {
        "business-equipment-cafe",
        "business-equipment-retail",
        "business-equipment-industrial",
    }
    assert BUSINESS_EQUIPMENT_V2_LEGACY_RETIRED_SLUGS.isdisjoint(
        BUSINESS_EQUIPMENT_V2_CANONICAL_SLUGS
    )


def test_business_equipment_single_trade_direction() -> None:
    trade_leaves = [
        (label, slug)
        for label, slug, _sort in BUSINESS_EQUIPMENT_V2_CANONICAL_LEAVES
        if label == TRADE_CANONICAL_LABEL
    ]
    assert trade_leaves == [(TRADE_CANONICAL_LABEL, TRADE_CANONICAL_SLUG)]
    assert "business-equipment-retail" in BUSINESS_EQUIPMENT_V2_LEGACY_RETIRED_SLUGS


def test_business_equipment_plotter_and_sto_compressor_ownership() -> None:
    assert PLOTTER_KIND in _kinds({"print": BUSINESS_SECTIONS["print"]})
    assert BUSINESS_EQUIPMENT_ELECTRONICS_BOUNDARY[PLOTTER_KIND] == "BUSINESS_EQUIPMENT"
    assert STO_COMPRESSOR_KIND in business_equipment_v2_all_kinds()
    assert REPAIR_GENERIC_COMPRESSOR_KIND not in business_equipment_v2_all_kinds()
    assert BUSINESS_EQUIPMENT_REPAIR_BOUNDARY[STO_COMPRESSOR_KIND] == "BUSINESS_EQUIPMENT"
    assert (
        BUSINESS_EQUIPMENT_REPAIR_BOUNDARY[REPAIR_GENERIC_COMPRESSOR_KIND] == "REPAIR"
    )
    assert REPAIR_GENERIC_COMPRESSOR_KIND in _kinds(REPAIR_SECTIONS)


def test_business_equipment_electronics_boundary_no_consumer_dupes() -> None:
    be = set(business_equipment_v2_all_kinds())
    el = _kinds(ELECTRONICS_SECTIONS)
    banned_in_be = {
        "Принтеры",
        "Сканеры",
        "МФУ",
        "Холодильники",
        "Бытовые швейные машины",
        "ИБП",
    }
    assert banned_in_be.isdisjoint(be)
    assert "Чековые принтеры" in be
    assert "Принтеры этикеток" in be
    assert "Сканеры штрихкода" in be
    for kind in banned_in_be:
        if kind in el:
            assert BUSINESS_EQUIPMENT_ELECTRONICS_BOUNDARY[kind] == "ELECTRONICS"


def test_business_equipment_medical_boundary_matrix() -> None:
    be = set(business_equipment_v2_all_kinds())
    med = _kinds(MED_SECTIONS)
    for kind, owner in BUSINESS_EQUIPMENT_MEDICAL_BOUNDARY.items():
        if owner == "BUSINESS_EQUIPMENT":
            assert kind in be
            assert kind not in med
        if owner == "MEDICAL":
            assert kind in med
            assert kind not in be


def test_business_equipment_food_tara_gap_still_open() -> None:
    be = set(business_equipment_v2_all_kinds())
    assert FOOD_TARA_GOODS_NOT_BUSINESS_EQUIPMENT.isdisjoint(be)
    packing = {r["label"] for r in BUSINESS_SECTIONS["packing"]["roles"]}
    assert packing.isdisjoint(FOOD_TARA_GOODS_NOT_BUSINESS_EQUIPMENT)
    assert "machines" in BUSINESS_PACKING_IS_EQUIPMENT_NOT_TARA
    assert "not jars/bags" in FOOD_AGRI_TARA_NOT_BUSINESS_EQUIPMENT_REASON


def test_business_equipment_seller_target_canonical_goods() -> None:
    assert BUSINESS_EQUIPMENT_SELLER_TARGET == (
        "Частное лицо",
        "Магазин",
        "Другой",
    )
    assert "Компания" not in BUSINESS_EQUIPMENT_SELLER_TARGET


def test_business_equipment_condition_independent_matrix() -> None:
    matrix = business_equipment_v2_condition_matrix()
    assert len(matrix) == 176
    yes = business_equipment_v2_condition_yes_kinds()
    no = business_equipment_v2_condition_no_kinds()
    assert len(yes) == 172
    assert len(no) == 4
    assert no == {
        "Ценникодержатели",
        "Крючки для торгового оборудования",
        "Подставки для украшений",
        "Иглы промышленные",
    }
    # Independent expectations — do not derive from a production allowlist helper alone.
    independent_no = {
        "Ценникодержатели",
        "Крючки для торгового оборудования",
        "Подставки для украшений",
        "Иглы промышленные",
    }
    for kind in independent_no:
        assert matrix[kind] == "NO"
    for kind in ("Плоттеры", "Компрессоры для СТО", "Токарные станки", "Онлайн-кассы"):
        assert matrix[kind] == "YES"


def test_business_equipment_tech_spec_target_is_description() -> None:
    forbidden_future_keys = {
        "brand",
        "model",
        "power",
        "voltage",
        "capacity",
        "productivity",
        "dimensions",
        "weight",
        "material",
        "year",
        "manufacturer",
        "warranty",
        "power_kw",
    }
    for catalog in BUSINESS_SECTIONS.values():
        filter_labels = {f["label"] for f in catalog["filters"]}
        assert filter_labels == {"Продавец", "Состояние"}
        for key in forbidden_future_keys:
            assert key not in filter_labels
