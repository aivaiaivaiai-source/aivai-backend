"""Materials V2 taxonomy + platform coherence (pre–Package A)."""
from __future__ import annotations

from app.seeds.animals_sections_catalog import ANIMALS_SECTIONS
from app.seeds.business_sections_catalog import BUSINESS_SECTIONS
from app.seeds.fashion_sections_catalog import FASHION_SECTIONS
from app.seeds.food_agri_v2 import FOOD_AGRI_TARA_KIND_OWNERSHIP
from app.seeds.food_sections_catalog import FOOD_SECTIONS
from app.seeds.materials_sections_catalog import MATERIALS_SECTIONS
from app.seeds.materials_v2 import (
    FOOD_TARA_GAP_STATUS,
    MATERIALS_CONDITION_POLICY,
    MATERIALS_CREATE_FORBIDDEN,
    MATERIALS_FEED_BANNED,
    MATERIALS_FOOD_GRAIN_BANNED,
    MATERIALS_HAZARDOUS_MATRIX,
    MATERIALS_METAL_LABEL_NOTE,
    MATERIALS_PACKAGING_SLUG,
    MATERIALS_PRICE_BASIS_OPTIONS,
    MATERIALS_PRICE_BASIS_REQUIRED,
    MATERIALS_REPAIR_FINISHED_BANNED,
    MATERIALS_ROOT_LABEL,
    MATERIALS_ROOT_SLUG,
    MATERIALS_SCRAP_KINDS,
    MATERIALS_SELLER_TARGET,
    MATERIALS_V2_CANONICAL_LEAVES,
    MATERIALS_V2_CANONICAL_SLUGS,
    MATERIALS_V2_EXPECTED_L2_COUNT,
    MATERIALS_V2_IMPORT_SLUG,
    MATERIALS_V2_IMPORT_STATUS,
    MATERIALS_V2_LEGACY_TRIAD_SLUGS,
    MATERIALS_V2_RETIRED_SLUGS,
    MATERIALS_V2_SECTION_KINDS,
    materials_v2_all_kinds,
    materials_v2_assert_cleanup_contracts,
    materials_v2_condition_decision,
    materials_v2_kind_count,
    materials_v2_package_a_field_target,
)
from app.seeds.repair_sections_catalog import REPAIR_SECTIONS
from app.seeds.stationery_sections_catalog import STATIONERY_SECTIONS


def _kinds(sections: dict) -> set[str]:
    out: set[str] = set()
    for catalog in sections.values():
        for role in catalog["roles"]:
            out.add(role["label"])
    return out


def test_materials_v2_cleanup_contracts() -> None:
    materials_v2_assert_cleanup_contracts()
    assert MATERIALS_ROOT_SLUG == "materials"
    assert MATERIALS_ROOT_LABEL == "Материалы, сырьё и товары для производства"
    assert MATERIALS_V2_EXPECTED_L2_COUNT == 18
    assert len(MATERIALS_V2_CANONICAL_LEAVES) == 18
    assert len(MATERIALS_SECTIONS) == 18
    assert materials_v2_kind_count() == 117
    assert MATERIALS_V2_LEGACY_TRIAD_SLUGS == {
        "materials-textile",
        "materials-metal",
        "materials-chemical",
    }
    assert MATERIALS_V2_IMPORT_SLUG in MATERIALS_V2_RETIRED_SLUGS
    assert MATERIALS_V2_IMPORT_STATUS == "RETIRED_SALES_MODE_NOT_PRODUCT_IDENTITY"
    assert "import" not in MATERIALS_SECTIONS
    assert MATERIALS_V2_LEGACY_TRIAD_SLUGS.isdisjoint(MATERIALS_V2_CANONICAL_SLUGS)


def test_materials_no_dual_tree_in_active_catalog() -> None:
    active_slugs = {cat["category_slug"] for cat in MATERIALS_SECTIONS.values()}
    assert active_slugs == MATERIALS_V2_CANONICAL_SLUGS
    assert MATERIALS_V2_LEGACY_TRIAD_SLUGS.isdisjoint(active_slugs)
    assert MATERIALS_V2_IMPORT_SLUG not in active_slugs


def test_materials_seller_target_canonical_goods() -> None:
    assert MATERIALS_SELLER_TARGET == ("Частное лицо", "Магазин", "Другой")
    for banned in ("Оптовик", "Компания", "Импортёр", "Производитель", "Поставщик", "База"):
        assert banned not in MATERIALS_SELLER_TARGET
    for catalog in MATERIALS_SECTIONS.values():
        labels = [g["label"] for g in catalog["filters"]]
        assert labels == ["Продавец", "Цена за"]
        seller = catalog["filters"][0]
        assert [o["label"] for o in seller["options"]] == list(MATERIALS_SELLER_TARGET)


def test_materials_condition_absent_for_all_kinds() -> None:
    assert MATERIALS_CONDITION_POLICY == "ABSENT"
    kinds = materials_v2_all_kinds()
    assert kinds
    for kind in kinds:
        assert materials_v2_condition_decision(kind) == "NO"
    for catalog in MATERIALS_SECTIONS.values():
        assert "Состояние" not in [g["label"] for g in catalog["filters"]]


def test_materials_price_basis_target() -> None:
    assert MATERIALS_PRICE_BASIS_REQUIRED is False
    assert MATERIALS_PRICE_BASIS_OPTIONS == (
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
    target = materials_v2_package_a_field_target()
    assert "price_basis" in target["optional"]
    assert "quantity" in target["absent"]
    assert "moq" in target["absent"]
    assert "condition" in target["absent"]


def test_materials_simple_field_target() -> None:
    assert MATERIALS_CREATE_FORBIDDEN >= {
        "condition",
        "brand",
        "model",
        "manufacturer",
        "country",
        "grade",
        "standard",
        "color",
        "dimensions",
        "weight",
        "quantity",
        "moq",
        "material_type",
    }


def test_materials_repair_boundary() -> None:
    mats = set(materials_v2_all_kinds())
    repair = _kinds(REPAIR_SECTIONS)
    assert MATERIALS_REPAIR_FINISHED_BANNED.isdisjoint(mats)
    for kind in (
        "Цемент",
        "Кирпич",
        "Фанера",
        "Арматура",
        "Интерьерные краски",
        "Гипсокартон",
    ):
        assert kind in repair
        assert kind not in mats
    assert "Листовой прокат" in mats
    assert "Листовой металл" in repair
    assert "Листовой прокат" != "Листовой металл"
    assert "прокат" in MATERIALS_METAL_LABEL_NOTE.lower() or "прокат" in MATERIALS_METAL_LABEL_NOTE


def test_materials_food_agri_and_animals_boundary() -> None:
    mats = set(materials_v2_all_kinds())
    food = _kinds(FOOD_SECTIONS)
    animals = _kinds(ANIMALS_SECTIONS)
    assert MATERIALS_FOOD_GRAIN_BANNED.isdisjoint(mats)
    assert MATERIALS_FEED_BANNED.isdisjoint(mats)
    for grain in ("Пшеница", "Ячмень", "Кукуруза"):
        assert grain in food
        assert grain not in mats
    assert "Сухое молоко" in mats
    assert "Желатин" in mats
    assert MATERIALS_FEED_BANNED.isdisjoint(mats)
    _ = animals  # Animals owns feed; Materials must not duplicate.


def test_materials_fashion_boundary_no_resurrection() -> None:
    fashion_labels = {cat["label"] for cat in FASHION_SECTIONS.values()}
    assert "Ткани и фурнитура" not in fashion_labels
    assert "Ткани и текстильное сырьё" in {
        cat["label"] for cat in MATERIALS_SECTIONS.values()
    }
    assert "Швейная фурнитура" in {
        cat["label"] for cat in MATERIALS_SECTIONS.values()
    }


def test_materials_business_equipment_packaging_boundary() -> None:
    assert MATERIALS_PACKAGING_SLUG in MATERIALS_V2_CANONICAL_SLUGS
    be_labels = {cat["label"] for cat in BUSINESS_SECTIONS.values()}
    assert "Упаковка и маркировка" in be_labels
    pack_kinds = set(MATERIALS_V2_SECTION_KINDS["pack"])
    assert "Стретч-плёнка" in pack_kinds
    assert "Запайщики" not in pack_kinds


def test_materials_stationery_paper_boundary() -> None:
    mats = set(materials_v2_all_kinds())
    stationery = _kinds(STATIONERY_SECTIONS)
    assert "Бумага в рулонах" in mats
    assert "Бумага для рисования" in stationery
    assert "Бумага для рисования" not in mats


def test_materials_food_tara_gap_still_open() -> None:
    assert FOOD_TARA_GAP_STATUS == "STILL_OPEN"
    pack = set(MATERIALS_V2_SECTION_KINDS["pack"])
    for kind, (status, dest, _note) in FOOD_AGRI_TARA_KIND_OWNERSHIP.items():
        assert status == "GAP"
        assert dest == MATERIALS_PACKAGING_SLUG
        assert kind not in pack
    assert "Стеклянные банки" not in pack
    assert "Крышки" not in pack
    assert "Пластиковые бутылки" not in pack
    # Стеклотара is partial nearest under glass — not full tara resolution.
    assert "Стеклотара" in MATERIALS_V2_SECTION_KINDS["glass"]


def test_materials_scrap_kinds_documented() -> None:
    mats = set(materials_v2_all_kinds())
    assert MATERIALS_SCRAP_KINDS <= mats


def test_materials_hazardous_matrix_documented() -> None:
    mats = set(materials_v2_all_kinds())
    assert MATERIALS_HAZARDOUS_MATRIX
    for kind, cls in MATERIALS_HAZARDOUS_MATRIX.items():
        assert kind in mats
        assert cls in {"KEEP_CURRENT", "POLICY_REVIEW", "PRODUCT_DECISION"}
