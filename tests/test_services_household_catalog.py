"""Household kinds are workshop trades, not sibling sections."""
from app.seeds.services_household_catalog import build_household_services_catalog


def test_household_kinds_are_trades() -> None:
    catalog = build_household_services_catalog()
    labels = [item["label"] for item in catalog["kinds"]]
    assert catalog["category_slug"] == "services-bytovye-uslugi"
    assert labels[0] == "Ремонт обуви, сумок и чемоданов"
    assert labels[-1] == "Другие бытовые услуги"
    assert "Изготовление ключей и ремонт замков" in labels
    assert "Заточка ножей и инструмента" in labels
    assert "Ремонт часов" in labels
    assert "Ремонт ювелирных изделий" in labels
    for banned in (
        "Уборка",
        "Химчистка",
        "Стирка",
        "Ателье",
        "Одежда",
        "Вскрытие",
        "Сантехника",
        "Электрика",
        "Мебель",
        "Телефон",
        "Няня",
        "Кроссовки",
        "Домофон",
        "Гравировка",
        "Оцифровка фото и видео",
        "Садовник",
    ):
        assert banned not in labels
    assert [item["label"] for item in catalog["executors"]][-1] == "Другой"
    assert catalog["objects"] == []
    assert catalog["materials"] == []
