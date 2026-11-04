"""Stationery and books sell the item, not a device or a kids book."""
from app.seeds.stationery_sections_catalog import STATIONERY_SECTIONS


def test_stationery_sections_are_products() -> None:
    assert len(STATIONERY_SECTIONS) == 15
    seen: dict[str, str] = {}
    for catalog in STATIONERY_SECTIONS.values():
        roles = [item["label"] for item in catalog["roles"]]
        assert catalog["question"] == "Какой товар?"
        assert roles[-1].startswith("Друг")
        labels = [item["label"] for item in catalog["filters"]]
        assert labels[:2] == ["Продавец", "Состояние"]
        assert "Регион" not in labels
        assert "Город" not in labels
        sellers = [item["label"] for item in catalog["filters"][0]["options"]]
        assert sellers == ["Частное лицо", "Магазин", "Компания"]
        for role in roles:
            assert role not in seen, role
            seen[role] = catalog["label"]
    assert seen["Тетради"] == "Канцелярские товары"
    assert seen["Математика"] == "Учебники и учебные пособия"
    assert seen["Романы"] == "Художественная литература"
    assert seen["Аудиокниги"] == "Электронные книги"
    assert seen["CD и DVD"] == "Прочие книги и канцтовары"
    textbooks = STATIONERY_SECTIONS["textbooks"]
    grade = next(item for item in textbooks["filters"] if item["label"] == "Класс")
    assert grade["applies_to"][0] == "Математика"
    assert "Подготовка к ОРТ" not in grade["applies_to"]
    assert "Вузские учебники" not in grade["applies_to"]
    assert [item["label"] for item in grade["options"]][0] == "1 класс"
    assert [item["label"] for item in grade["options"]][-1] == "11 класс"
    language = next(item for item in textbooks["filters"] if item["label"] == "Язык")
    assert [item["label"] for item in language["options"]][:2] == [
        "Кыргызский",
        "Русский",
    ]
    banned = {
        "Книги для малышей",
        "Сказки",
        "Детские энциклопедии",
        "Другие детские книги",
        "Электронные книги",
        "Планшеты",
        "Принтеры",
        "Краски для волос",
        "Краски для тату",
        "Пряжа",
        "Шырдаки",
        "Ножницы",
        "Музыкальные инструменты",
    }
    assert banned.isdisjoint(seen)
