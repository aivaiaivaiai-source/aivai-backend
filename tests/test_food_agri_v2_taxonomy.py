"""Food/Agri V2 taxonomy foundation — dual-tree cleanup + ownership."""
from __future__ import annotations

from app.seeds.animals_sections_catalog import ANIMALS_SECTIONS
from app.seeds.business_sections_catalog import BUSINESS_SECTIONS
from app.seeds.food_agri_v2 import (
    FOOD_AGRI_CONDITION_APPROVED_KINDS,
    FOOD_AGRI_CONDITION_DEFAULT,
    FOOD_AGRI_ECO_RETIRED_SLUGS,
    FOOD_AGRI_FEED_CANONICAL_ANIMALS_SLUG,
    FOOD_AGRI_GRAIN_KIND_OWNERSHIP,
    FOOD_AGRI_LEGACY_RETIRED_SLUGS,
    FOOD_AGRI_PRICE_SEMANTICS,
    FOOD_AGRI_RECOMMENDED_PRICE_MODEL,
    FOOD_AGRI_ROOT_SLUG,
    FOOD_AGRI_SALES_MODE_RETIRED_SLUGS,
    FOOD_AGRI_SELLER_DROP_SECTION_ROLES,
    FOOD_AGRI_SELLER_RECOMMENDATION,
    FOOD_AGRI_TARA_KIND_OWNERSHIP,
    FOOD_AGRI_TARA_RETIRED_SLUGS,
    FOOD_AGRI_V2_CANONICAL_LEAVES,
    FOOD_AGRI_V2_CANONICAL_SLUGS,
    FOOD_AGRI_V2_EXPECTED_L2_COUNT,
    FOOD_AGRI_V2_RETIRED_SLUGS,
    FOOD_AGRI_V2_SECTION_SLUGS,
)
from app.seeds.food_sections_catalog import FOOD_SECTIONS
from app.seeds.loader import _RETIRED_CATEGORY_SLUGS
from app.seeds.materials_sections_catalog import MATERIALS_SECTIONS


def test_food_agri_canonical_counts_and_retired_sets() -> None:
    assert FOOD_AGRI_ROOT_SLUG == "food-agri"
    assert len(FOOD_AGRI_V2_CANONICAL_LEAVES) == FOOD_AGRI_V2_EXPECTED_L2_COUNT
    assert len(FOOD_AGRI_V2_CANONICAL_SLUGS) == FOOD_AGRI_V2_EXPECTED_L2_COUNT
    assert FOOD_AGRI_V2_EXPECTED_L2_COUNT == 23
    assert FOOD_AGRI_LEGACY_RETIRED_SLUGS <= FOOD_AGRI_V2_RETIRED_SLUGS
    assert FOOD_AGRI_SALES_MODE_RETIRED_SLUGS <= FOOD_AGRI_V2_RETIRED_SLUGS
    assert FOOD_AGRI_ECO_RETIRED_SLUGS <= FOOD_AGRI_V2_RETIRED_SLUGS
    assert FOOD_AGRI_TARA_RETIRED_SLUGS <= FOOD_AGRI_V2_RETIRED_SLUGS
    assert FOOD_AGRI_V2_RETIRED_SLUGS.isdisjoint(FOOD_AGRI_V2_CANONICAL_SLUGS)
    assert "food-agri-feed" in FOOD_AGRI_V2_RETIRED_SLUGS
    assert "food-agri-optovyy-otdel" in FOOD_AGRI_V2_RETIRED_SLUGS
    assert "food-agri-ekoprodukty-i-fermerskie-tovary" in FOOD_AGRI_V2_RETIRED_SLUGS
    assert "food-agri-tara-upakovka-dlya-produktsii" in FOOD_AGRI_V2_RETIRED_SLUGS


def test_food_agri_retired_registered_in_loader() -> None:
    assert FOOD_AGRI_V2_RETIRED_SLUGS <= _RETIRED_CATEGORY_SLUGS


def test_food_agri_no_dual_active_catalog_identity() -> None:
    catalog_slugs = {cat["category_slug"] for cat in FOOD_SECTIONS.values()}
    assert catalog_slugs == set(FOOD_AGRI_V2_SECTION_SLUGS.values())
    assert catalog_slugs == FOOD_AGRI_V2_CANONICAL_SLUGS
    assert catalog_slugs.isdisjoint(FOOD_AGRI_V2_RETIRED_SLUGS)
    assert len(FOOD_SECTIONS) == FOOD_AGRI_V2_EXPECTED_L2_COUNT


def test_food_agri_kind_count_after_cleanup() -> None:
    kinds = [role["label"] for cat in FOOD_SECTIONS.values() for role in cat["roles"]]
    assert len(kinds) == len(set(kinds))
    # 175 - wholesale(7) - eco(3) - packaging(7) = 158
    assert len(kinds) == 158
    banned = {
        "Сено",
        "Комбикорм",
        "Овощи оптом",
        "Фермерские наборы",
        "Стеклянные банки",
        "Мешки",
        "Молочные смеси",
        "БАДы",
        "Улей",
        "Пищевое сырьё",
    }
    assert banned.isdisjoint(set(kinds))


def test_food_agri_feed_ownership_animals() -> None:
    assert FOOD_AGRI_FEED_CANONICAL_ANIMALS_SLUG == (
        "animals-seno-korma-i-kormovye-dobavki"
    )
    animals_slugs = {cat["category_slug"] for cat in ANIMALS_SECTIONS.values()}
    assert FOOD_AGRI_FEED_CANONICAL_ANIMALS_SLUG in animals_slugs
    feed_kinds = {
        r["label"] for r in ANIMALS_SECTIONS["feed"]["roles"]
    }
    assert {"Сено", "Комбикорм"} <= feed_kinds
    food_kinds = {
        r["label"] for cat in FOOD_SECTIONS.values() for r in cat["roles"]
    }
    assert "Сено" not in food_kinds
    assert "Комбикорм" not in food_kinds


def test_food_agri_tara_ownership_matrix_all_gap() -> None:
    assert set(FOOD_AGRI_TARA_KIND_OWNERSHIP) == {
        "Стеклянные банки",
        "Крышки",
        "Пластиковые бутылки",
        "Ящики",
        "Мешки",
        "Контейнеры",
        "Другая тара",
    }
    materials_slugs = {cat["category_slug"] for cat in MATERIALS_SECTIONS.values()}
    assert "materials-upakovochnye-materialy" in materials_slugs
    packing = BUSINESS_SECTIONS["packing"]
    packing_kinds = {r["label"] for r in packing["roles"]}
    # Equipment, not goods tara.
    assert "Запайщики" in packing_kinds
    assert "Мешки" not in packing_kinds
    for kind, (decision, dest, _reason) in FOOD_AGRI_TARA_KIND_OWNERSHIP.items():
        assert decision == "GAP", kind
        assert dest == "materials-upakovochnye-materialy"


def test_food_agri_grain_ownership_all_agri_commodity() -> None:
    crops = {r["label"] for r in FOOD_SECTIONS["crops"]["roles"]}
    assert set(FOOD_AGRI_GRAIN_KIND_OWNERSHIP) == crops
    for kind, (klass, dest, _reason) in FOOD_AGRI_GRAIN_KIND_OWNERSHIP.items():
        assert klass == "AGRICULTURAL_COMMODITY", kind
        assert dest == "food-agri-zerno-i-zernovye-kultury"


def test_food_agri_condition_default_off() -> None:
    assert FOOD_AGRI_CONDITION_DEFAULT == "OFF"
    assert FOOD_AGRI_CONDITION_APPROVED_KINDS == frozenset()
    kinds = [role["label"] for cat in FOOD_SECTIONS.values() for role in cat["roles"]]
    for kind in kinds:
        assert kind not in FOOD_AGRI_CONDITION_APPROVED_KINDS


def test_food_agri_price_semantics_covers_all_kinds() -> None:
    kinds = [role["label"] for cat in FOOD_SECTIONS.values() for role in cat["roles"]]
    assert set(kinds) == set(FOOD_AGRI_PRICE_SEMANTICS)
    assert FOOD_AGRI_RECOMMENDED_PRICE_MODEL == "B"
    classes = {row[0] for row in FOOD_AGRI_PRICE_SEMANTICS.values()}
    assert classes <= {"ITEM_PRICE", "UNIT_PRICE_REQUIRED", "PRODUCT_DECISION"}
    assert "UNIT_PRICE_REQUIRED" in classes


def test_food_agri_seller_recommendation() -> None:
    from app.seeds.food_agri_v2 import FOOD_AGRI_SELLER_CHOICES

    assert FOOD_AGRI_SELLER_RECOMMENDATION == "FOOD_DOMAIN_OVERRIDE"
    assert FOOD_AGRI_SELLER_CHOICES == (
        "Частное лицо",
        "Фермер",
        "Магазин",
        "Другой",
    )
    assert "Пекарня" in FOOD_AGRI_SELLER_DROP_SECTION_ROLES
    assert "Оптовик" in FOOD_AGRI_SELLER_DROP_SECTION_ROLES


def test_food_sections_do_not_overlap_after_cleanup() -> None:
    seen: dict[str, str] = {}
    for catalog in FOOD_SECTIONS.values():
        roles = [item["label"] for item in catalog["roles"]]
        assert catalog["question"] == "Какой товар?"
        assert roles[-1].startswith("Друг")
        for role in roles:
            assert role not in seen, role
            seen[role] = catalog["label"]
        assert [item["label"] for item in catalog["filters"]] == ["Кто продаёт"]
    assert seen["Рис"] == "Крупы, мука/макаронные изделия"
    assert seen["Пшеница"] == "Зерно и зерновые культуры"
    assert "Овощи оптом" not in seen
