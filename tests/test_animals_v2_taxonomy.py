"""Animals V2 taxonomy + vet-services ownership (Package A)."""
from __future__ import annotations

from app.seeds.animals_sections_catalog import ANIMALS_SECTIONS
from app.seeds.animals_v2 import (
    ANIMALS_FEED_SLUG,
    ANIMALS_V2_AGE_TARGET,
    ANIMALS_V2_BREED_TARGET,
    ANIMALS_V2_CANONICAL_SLUGS,
    ANIMALS_V2_EXPECTED_L2_COUNT,
    ANIMALS_V2_LEGACY_RETIRED_SLUGS,
    ANIMALS_V2_RETIRED_SLUGS,
    ANIMALS_VET_GOODS_SLUG,
    ANIMALS_VET_SERVICE_KIND_MAPPING,
    ANIMALS_VET_SERVICES_RETIRE_BLOCKED,
    ANIMALS_VET_SERVICES_SLUG,
    SERVICES_OTHER_SLUG,
    SERVICES_VET_EXPANDED_KINDS,
    animals_v2_assert_package_a_contracts,
    animals_vet_service_mapping_report,
)
from app.seeds.food_agri_v2 import FOOD_AGRI_FEED_CANONICAL_ANIMALS_SLUG
from app.seeds.services_rest_catalog import SERVICE_SECTIONS
from app.seeds.services_v2 import build_services_v2_catalogs


def test_animals_v2_contracts() -> None:
    animals_v2_assert_package_a_contracts()
    assert ANIMALS_V2_EXPECTED_L2_COUNT == 15
    assert len(ANIMALS_V2_CANONICAL_SLUGS) == 15
    assert ANIMALS_V2_LEGACY_RETIRED_SLUGS == {
        "animals-pets",
        "animals-livestock",
        "animals-birds",
    }
    assert ANIMALS_VET_SERVICES_SLUG in ANIMALS_V2_RETIRED_SLUGS
    assert ANIMALS_VET_SERVICES_SLUG not in ANIMALS_V2_CANONICAL_SLUGS
    assert ANIMALS_V2_LEGACY_RETIRED_SLUGS.isdisjoint(ANIMALS_V2_CANONICAL_SLUGS)
    assert ANIMALS_VET_SERVICES_RETIRE_BLOCKED is False


def test_animals_feed_ownership() -> None:
    assert ANIMALS_FEED_SLUG == FOOD_AGRI_FEED_CANONICAL_ANIMALS_SLUG
    assert ANIMALS_FEED_SLUG in ANIMALS_V2_CANONICAL_SLUGS
    assert ANIMALS_SECTIONS["feed"]["category_slug"] == ANIMALS_FEED_SLUG


def test_animals_vet_goods_boundary() -> None:
    assert ANIMALS_VET_GOODS_SLUG in ANIMALS_V2_CANONICAL_SLUGS
    kinds = {r["label"] for r in ANIMALS_SECTIONS["vetgoods"]["roles"]}
    assert "Антибиотики" not in kinds
    assert "Вакцины" not in kinds
    assert "Лекарства" not in kinds
    assert "vetservices" not in ANIMALS_SECTIONS


def test_animals_vet_service_mapping_option_b() -> None:
    other = SERVICE_SECTIONS["other"]
    service_kinds = {r["label"] for r in other["kinds"]}
    assert other["category_slug"] == SERVICES_OTHER_SLUG
    for kind in SERVICES_VET_EXPANDED_KINDS:
        assert kind in service_kinds
    assert "Ветеринарные услуги" not in service_kinds  # replaced by subtypes

    catalogs = build_services_v2_catalogs()
    other_cat_kinds = set(catalogs[SERVICES_OTHER_SLUG]["kinds"])
    for kind in SERVICES_VET_EXPANDED_KINDS:
        assert kind in other_cat_kinds

    report = animals_vet_service_mapping_report()
    assert len(report) == 7
    for row in report:
        assert row["decision"] == "EXACT_DESTINATION"
        assert row["services_slug"] == SERVICES_OTHER_SLUG
        assert row["services_kind"] in service_kinds
    assert ANIMALS_VET_SERVICE_KIND_MAPPING["Груминг"][2] == "Груминг"


def test_animals_breed_as_kind_normalized() -> None:
    dogs = [r["label"] for r in ANIMALS_SECTIONS["dogs"]["roles"]]
    cats = [r["label"] for r in ANIMALS_SECTIONS["cats"]["roles"]]
    rabbits = [r["label"] for r in ANIMALS_SECTIONS["rabbits"]["roles"]]
    assert dogs == ["Собаки", "Щенки", "Другие собаки", "Вязка собак"]
    assert cats == ["Кошки", "Котята", "Другие кошки", "Вязка кошек"]
    assert rabbits == ["Кролики", "Декоративные кролики", "Другие кролики"]
    banned_breeds = {
        "Алабаи",
        "Хаски",
        "Мейн-куны",
        "Британские",
        "Калифорнийские",
        "Новозеландские",
        "Голштин",
        "Гиссарские",
    }
    all_kinds = {
        r["label"] for cat in ANIMALS_SECTIONS.values() for r in cat["roles"]
    }
    assert banned_breeds.isdisjoint(all_kinds)
    for cat in ANIMALS_SECTIONS.values():
        filter_labels = [g["label"] for g in cat["filters"]]
        assert "Порода" not in filter_labels


def test_animals_age_and_breed_targets() -> None:
    assert ANIMALS_V2_AGE_TARGET == "DESCRIPTION"
    assert ANIMALS_V2_BREED_TARGET == "DESCRIPTION"


def test_animals_sections_match_canonical_slugs() -> None:
    catalog_slugs = {c["category_slug"] for c in ANIMALS_SECTIONS.values()}
    assert catalog_slugs == ANIMALS_V2_CANONICAL_SLUGS
    assert len(ANIMALS_SECTIONS) == ANIMALS_V2_EXPECTED_L2_COUNT
