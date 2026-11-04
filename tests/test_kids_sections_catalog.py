"""Kids World kinds do not overlap, and filters follow the product."""
from app.seeds.kids_sections_catalog import KIDS_SECTIONS


def _kinds(key: str) -> list[str]:
    return [item["label"] for item in KIDS_SECTIONS[key]["roles"]]


def _filter(key: str, label: str) -> dict:
    return next(item for item in KIDS_SECTIONS[key]["filters"] if item["label"] == label)


def test_kids_sections_do_not_overlap() -> None:
    assert len(KIDS_SECTIONS) == 18
    seen: dict[str, str] = {}
    for catalog in KIDS_SECTIONS.values():
        roles = [item["label"] for item in catalog["roles"]]
        assert roles[-1].startswith("Друг")
        assert catalog["question"]
        for role in roles:
            assert role not in seen, f"{role} in {seen.get(role)} and {catalog['label']}"
            seen[role] = catalog["label"]
    assert seen["Ходунки"] == "Товары для новорождённых"
    assert seen["Детские велосипеды"] == "Детский транспорт"
    assert seen["Кенгуру и эргорюкзаки"] == "Автокресла и переноски"
    assert seen["Пелёнки"] == "Товары для новорождённых"
    assert seen["Одноразовые пелёнки"] == "Подгузники и гигиена"
    assert KIDS_SECTIONS["education"]["question"] == "Какое предложение?"

    season = _filter("newborn", "Сезон")
    assert season["applies_to"] == ["Конверты на выписку"]
    assert "Ходунки" not in season["applies_to"]
    assert "Шезлонги и электрокачели" not in season["applies_to"]

    cloth_season = _filter("clothes", "Сезон")
    assert cloth_season["applies_to"] == ["Верхняя одежда", "Головные уборы"]
    shoe_season = _filter("shoes", "Сезон")
    assert "Пинетки" not in shoe_season["applies_to"]
    assert "Домашняя обувь" not in shoe_season["applies_to"]

    assert "Сезон" not in {item["label"] for item in KIDS_SECTIONS["strollers"]["filters"]}
    assert "Сезон" not in {item["label"] for item in KIDS_SECTIONS["food"]["filters"]}
    assert "Б/у" not in [opt["label"] for opt in _filter("food", "Упаковка")["options"]]
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
    }
    assert banned.isdisjoint(seen)
    assert _filter("seats", "Крепление")["applies_to"][0] == "Автолюльки"
    assert "Слинги" not in _filter("seats", "Крепление")["applies_to"]
    assert _filter("transport", "Диаметр колеса")["applies_to"] == ["Детские велосипеды"]
