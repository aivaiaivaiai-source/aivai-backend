"""Stationery & Books V2 taxonomy + platform coherence (pre–Package A)."""
from __future__ import annotations

from app.seeds.electronics_sections_catalog import ELECTRONICS_SECTIONS
from app.seeds.fashion_sections_catalog import FASHION_SECTIONS
from app.seeds.kids_sections_catalog import KIDS_SECTIONS
from app.seeds.kids_v2 import KIDS_V2_SCHOOL_KIND_OWNERSHIP, KIDS_V2_SCHOOL_SLUG
from app.seeds.services_rest_catalog import SERVICE_SECTIONS
from app.seeds.stationery_sections_catalog import STATIONERY_SECTIONS
from app.seeds.stationery_v2 import (
    STATIONERY_EBOOKS_LABEL,
    STATIONERY_EBOOKS_SLUG,
    STATIONERY_GRADE_TARGET,
    STATIONERY_SCHOOL_BACKPACK_KIND,
    STATIONERY_SCHOOL_DIARY_KIND,
    STATIONERY_SCHOOL_GRADE_KINDS,
    STATIONERY_SCHOOL_GRADE_OPTIONS,
    STATIONERY_SCHOOL_KIND_OWNERSHIP,
    STATIONERY_SELLER_TARGET,
    STATIONERY_SHOE_BAG_KIND,
    STATIONERY_STATIONERY_SLUG,
    STATIONERY_V2_CANONICAL_SLUGS,
    STATIONERY_V2_CONDITION_MATRIX,
    STATIONERY_V2_EXPECTED_L2_COUNT,
    STATIONERY_V2_LEGACY_RETIRED_SLUGS,
    STATIONERY_V2_RETIRED_SLUGS,
    stationery_v2_all_kinds,
    stationery_v2_assert_cleanup_contracts,
    stationery_v2_condition_yes_kinds,
    stationery_v2_kids_school_gap_report,
)


def test_stationery_v2_cleanup_contracts() -> None:
    stationery_v2_assert_cleanup_contracts()
    assert STATIONERY_V2_EXPECTED_L2_COUNT == 15
    assert len(STATIONERY_V2_CANONICAL_SLUGS) == 15
    assert STATIONERY_V2_LEGACY_RETIRED_SLUGS == {
        "books-fiction",
        "books-study",
    }
    assert STATIONERY_V2_RETIRED_SLUGS == STATIONERY_V2_LEGACY_RETIRED_SLUGS
    assert STATIONERY_V2_LEGACY_RETIRED_SLUGS.isdisjoint(STATIONERY_V2_CANONICAL_SLUGS)


def test_stationery_electronic_publications_naming() -> None:
    ebooks = STATIONERY_SECTIONS["ebooks"]
    assert ebooks["label"] == STATIONERY_EBOOKS_LABEL == "Электронные издания"
    assert ebooks["category_slug"] == STATIONERY_EBOOKS_SLUG
    assert ebooks["label"] != "Электронные книги"


def test_stationery_school_kinds_under_kantselyariya() -> None:
    kinds = [r["label"] for r in STATIONERY_SECTIONS["stationery"]["roles"]]
    assert STATIONERY_SCHOOL_DIARY_KIND in kinds
    assert STATIONERY_SCHOOL_BACKPACK_KIND in kinds
    assert STATIONERY_SHOE_BAG_KIND in kinds
    assert STATIONERY_SECTIONS["stationery"]["category_slug"] == STATIONERY_STATIONERY_SLUG
    # No broad school L2 recreation.
    assert "Другие товары для школы" not in stationery_v2_all_kinds()


def test_kids_school_gaps_closed() -> None:
    assert KIDS_V2_SCHOOL_SLUG not in {
        STATIONERY_SECTIONS[k]["category_slug"] for k in STATIONERY_SECTIONS
    }
    assert KIDS_V2_SCHOOL_KIND_OWNERSHIP["Школьная форма"][0] == "MOVED"
    assert KIDS_V2_SCHOOL_KIND_OWNERSHIP["Школьные дневники"][0] == "EXACT_DESTINATION"
    assert KIDS_V2_SCHOOL_KIND_OWNERSHIP["Школьные рюкзаки"][0] == "EXACT_DESTINATION"
    assert (
        KIDS_V2_SCHOOL_KIND_OWNERSHIP["Мешки для сменной обуви"][0]
        == "EXACT_DESTINATION"
    )
    assert (
        KIDS_V2_SCHOOL_KIND_OWNERSHIP["Другие товары для школы"][0]
        == "NEAREST_DESTINATION"
    )
    report = stationery_v2_kids_school_gap_report()
    assert all(r["decision"] != "GAP" for r in report if r["kind"] != "Школьная форма")
    clothes = {r["label"] for r in KIDS_SECTIONS["clothes"]["roles"]}
    assert "Школьная форма" in clothes
    assert STATIONERY_SCHOOL_BACKPACK_KIND not in clothes


def test_fashion_no_school_backpack_duplicate() -> None:
    fashion_kinds: set[str] = set()
    for sec in FASHION_SECTIONS.values():
        for role in sec.get("roles") or []:
            fashion_kinds.add(role["label"] if isinstance(role, dict) else str(role))
    assert STATIONERY_SCHOOL_BACKPACK_KIND not in fashion_kinds
    assert STATIONERY_SHOE_BAG_KIND not in fashion_kinds


def test_electronics_boundary_devices_not_in_stationery() -> None:
    stationery_kinds = set(stationery_v2_all_kinds())
    banned = {"Планшеты", "Принтеры", "Сканеры", "МФУ"}
    assert banned.isdisjoint(stationery_kinds)
    tablets = ELECTRONICS_SECTIONS["tablets"]
    assert tablets["category_slug"] == "electronics-planshety-i-elektronnye-knigi"
    elec_kinds = {r["label"] for r in tablets["roles"]}
    assert "Электронные книги" in elec_kinds
    assert "Планшеты" in elec_kinds
    assert "Калькуляторы" in stationery_kinds
    assert "Калькуляторы" not in elec_kinds


def test_services_education_not_in_stationery() -> None:
    stationery_kinds = set(stationery_v2_all_kinds())
    assert "Репетитор" not in stationery_kinds
    assert "Частный преподаватель" not in stationery_kinds
    edu = SERVICE_SECTIONS["education"]
    assert edu["category_slug"] == "services-obuchenie-i-repetitorstvo"


def test_seller_target_no_company() -> None:
    assert STATIONERY_SELLER_TARGET == ("Частное лицо", "Магазин", "Другой")
    for sec in STATIONERY_SECTIONS.values():
        sellers = [o["label"] for o in sec["filters"][0]["options"]]
        assert sellers == list(STATIONERY_SELLER_TARGET)
        assert "Компания" not in sellers


def test_condition_matrix_covers_every_kind() -> None:
    kinds = stationery_v2_all_kinds()
    assert set(kinds) == set(STATIONERY_V2_CONDITION_MATRIX)
    assert all(
        d in ("YES", "NO") for d, _ in STATIONERY_V2_CONDITION_MATRIX.values()
    )
    yes = stationery_v2_condition_yes_kinds()
    assert STATIONERY_SCHOOL_BACKPACK_KIND in yes
    assert "Ручки" not in yes
    assert "Романы" in yes
    assert "Аудиокниги" not in yes


def test_grade_target_school_subjects_only() -> None:
    assert STATIONERY_GRADE_TARGET == "RETAIN_STRUCTURED"
    assert STATIONERY_SCHOOL_GRADE_OPTIONS[0] == "1 класс"
    assert "Подготовка к ОРТ" not in STATIONERY_SCHOOL_GRADE_KINDS
    assert "Вузские учебники" not in STATIONERY_SCHOOL_GRADE_KINDS
    textbooks = STATIONERY_SECTIONS["textbooks"]
    grade = next(f for f in textbooks["filters"] if f["label"] == "Класс")
    assert set(grade["applies_to"]) == set(STATIONERY_SCHOOL_GRADE_KINDS)


def test_kids_books_not_duplicated_in_stationery() -> None:
    stationery_kinds = set(stationery_v2_all_kinds())
    kids_books = {r["label"] for r in KIDS_SECTIONS["books"]["roles"]}
    assert kids_books.isdisjoint(stationery_kinds)
