"""Furniture kinds are trades, not products or sibling sections."""
from app.seeds.services_furniture_catalog import build_furniture_services_catalog


def test_furniture_kinds_are_trades() -> None:
    catalog = build_furniture_services_catalog()
    labels = [item["label"] for item in catalog["kinds"]]
    assert catalog["category_slug"] == "services-mebel-i-interer"
    assert labels[0] == "Сборка и разборка мебели"
    assert labels[-1] == "Другие работы по мебели и интерьеру"
    assert "Изготовление мебели на заказ" in labels
    assert "Ремонт и реставрация мебели" in labels
    assert "Перетяжка мягкой мебели" in labels
    assert "Услуги по шторам, карнизам и жалюзи" in labels
    for banned in (
        "Сантехника",
        "Электрика",
        "Отопление",
        "Дизайн",
        "Проектирование",
        "Химчистка",
        "Перевозка",
        "Скупка",
        "Кухня",
        "Шкаф",
        "Диван",
        "Кровать",
        "Потолки",
        "Двери",
        "Ламинат",
    ):
        assert banned not in labels
    assert [item["label"] for item in catalog["executors"]][-1] == "Другой"
    assert catalog["objects"] == []
    assert catalog["materials"] == []
