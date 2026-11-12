"""Business equipment stays out of household, repair and transport goods."""
from app.seeds.business_sections_catalog import BUSINESS_SECTIONS


def test_business_sections_do_not_overlap() -> None:
    assert len(BUSINESS_SECTIONS) == 20
    seen: dict[str, str] = {}
    for catalog in BUSINESS_SECTIONS.values():
        roles = [item["label"] for item in catalog["roles"]]
        assert catalog["question"] == "Какой товар?"
        assert roles[-1].startswith("Друг")
        for role in roles:
            assert role not in seen, role
            seen[role] = catalog["label"]
        labels = [item["label"] for item in catalog["filters"]]
        assert labels == ["Продавец", "Состояние"]
        sellers = [item["label"] for item in catalog["filters"][0]["options"]]
        assert sellers == ["Частное лицо", "Магазин", "Другой"]
        assert "Компания" not in sellers
    assert seen["Экономпанели"] == "Торговое оборудование"
    assert seen["Плоттеры"] == "Полиграфическое оборудование"
    assert seen["Компрессоры для СТО"] == "Оборудование для автомоек и СТО"
    assert "Компрессоры" not in seen
    assert seen["Кассовые боксы"] == "Кассовое и POS-оборудование"
    assert seen["Пароконвектоматы"] == "Оборудование для общепита"
    assert seen["Токарные станки"] == "Производственное оборудование"
    assert seen["Промышленные прямострочки"] == "Швейное оборудование"
    assert seen["Холодильные витрины"] == "Холодильное оборудование"
    assert seen["Станки для профнастила"] == "Производственное оборудование"
    banned = {
        "Холодильники",
        "Бытовые швейные машины",
        "Принтеры",
        "ИБП",
        "Генераторы",
        "Бетономешалки",
        "Сварочные аппараты",
        "Фены",
        "Стеклянные банки",
        "Готовый бизнес",
        "Компрессоры",
        "Мясорубки",
        "Вентиляторы",
        "Казаны",
        "Контейнеры",
    }
    assert banned.isdisjoint(seen)
