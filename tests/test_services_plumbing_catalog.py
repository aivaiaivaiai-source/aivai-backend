"""Plumbing kinds are trades, not rooms, fixtures, or sibling sections."""
from app.seeds.services_plumbing_catalog import build_plumbing_services_catalog


def test_plumbing_kinds_are_trades() -> None:
    catalog = build_plumbing_services_catalog()
    labels = [item["label"] for item in catalog["kinds"]]
    assert catalog["category_slug"] == "services-santehnika"
    assert labels[0] == "Водоснабжение и разводка труб"
    assert labels[-1] == "Другие сантехнические работы"
    assert "Прочистка засоров" in labels
    assert "Установка и замена сантехники" in labels
    assert "Септики и откачка" in labels
    for banned in (
        "Электрика",
        "Отопление",
        "Радиаторы",
        "Тёплый пол",
        "Котлы",
        "Стиральная машина",
        "Посудомоечная машина",
        "Унитаз",
        "Раковина",
        "Ванна",
        "Смеситель",
        "Аварийный вызов",
    ):
        assert banned not in labels
    assert [item["label"] for item in catalog["executors"]][-1] == "Другой"
    objects = [item["label"] for item in catalog["objects"]]
    assert objects[-1] == "Другое"
    assert "Участок" in objects
    assert "Баня" in objects
    assert "Балкон" not in objects
    assert "Баня и гараж" not in objects
    assert "С материалом" in [item["label"] for item in catalog["materials"]]
