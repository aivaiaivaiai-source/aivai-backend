"""Kids World kinds do not overlap; school retired; clothes owns school form."""
from app.seeds.kids_sections_catalog import KIDS_SECTIONS
from app.seeds.kids_v2 import (
    KIDS_V2_EXPECTED_KIND_COUNT,
    KIDS_V2_EXPECTED_L2_COUNT,
    KIDS_V2_LEGACY_CATALOG_SLUG_MISMATCHES,
    KIDS_V2_REMOVED_POOL_KIND,
    KIDS_V2_SECTION_CANONICAL_SLUGS,
    KIDS_V2_SCHOOL_SLUG,
)


def _kinds(key: str) -> list[str]:
    return [item["label"] for item in KIDS_SECTIONS[key]["roles"]]


def _filter(key: str, label: str) -> dict:
    return next(item for item in KIDS_SECTIONS[key]["filters"] if item["label"] == label)


def test_kids_sections_do_not_overlap() -> None:
    assert len(KIDS_SECTIONS) == KIDS_V2_EXPECTED_L2_COUNT
    assert "education" not in KIDS_SECTIONS
    assert "school" not in KIDS_SECTIONS
    seen: dict[str, str] = {}
    for catalog in KIDS_SECTIONS.values():
        roles = [item["label"] for item in catalog["roles"]]
        assert roles[-1].startswith("Друг")
        assert catalog["question"]
        for role in roles:
            assert role not in seen, f"{role} in {seen.get(role)} and {catalog['label']}"
            seen[role] = catalog["label"]
    assert len(seen) == KIDS_V2_EXPECTED_KIND_COUNT
    assert seen["Ходунки"] == "Товары для новорождённых"
    assert seen["Детские велосипеды"] == "Детский транспорт"
    assert seen["Кенгуру и эргорюкзаки"] == "Автокресла и переноски"
    assert seen["Пелёнки"] == "Товары для новорождённых"
    assert seen["Одноразовые пелёнки"] == "Подгузники и гигиена"
    assert seen["Школьная форма"] == "Детская одежда"
    assert KIDS_V2_REMOVED_POOL_KIND not in seen
    assert "Школьные рюкзаки" not in seen

    food_kinds = set(_kinds("food"))
    assert food_kinds == {
        "Молочные смеси",
        "Каши для прикорма",
        "Пюре для прикорма",
        "Другое детское питание",
    }
    banned = {
        "Соки и вода",
        "Детский чай",
        "Детское печенье",
        "Канцелярия",
        "Тетради",
        "Пеналы",
        "Учебники",
        "Настольные игры",
        "Рисование и лепка",
        "Наборы для творчества",
        "Электромобили",
        "Самокаты",
        KIDS_V2_REMOVED_POOL_KIND,
        "Школьные рюкзаки",
        "Школьные дневники",
        "Мешки для сменной обуви",
        "Другие товары для школы",
    }
    assert banned.isdisjoint(seen)
    assert _filter("seats", "Крепление")["applies_to"][0] == "Автолюльки"
    assert "Слинги" not in _filter("seats", "Крепление")["applies_to"]


def test_kids_section_slugs_match_canonical_db_skeleton() -> None:
    for key, expected in KIDS_V2_SECTION_CANONICAL_SLUGS.items():
        assert KIDS_SECTIONS[key]["category_slug"] == expected
        assert expected not in KIDS_V2_LEGACY_CATALOG_SLUG_MISMATCHES
    assert KIDS_V2_SCHOOL_SLUG not in {
        cat["category_slug"] for cat in KIDS_SECTIONS.values()
    }
