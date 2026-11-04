"""Electrical kinds are trades, not fixtures or sibling sections."""
from app.seeds.services_electrical_catalog import build_electrical_services_catalog


def test_electrical_kinds_are_trades() -> None:
    catalog = build_electrical_services_catalog()
    labels = [item["label"] for item in catalog["kinds"]]
    assert catalog["category_slug"] == "services-elektrika"
    assert labels[0] == "Электрика под ключ"
    assert labels[-1] == "Другие электромонтажные работы"
    assert "Прокладка и замена проводки" in labels
    assert "Розетки и выключатели" in labels
    assert "Освещение" in labels
    assert "Заземление и молниезащита" in labels
    for banned in (
        "Сантехника",
        "Отопление",
        "Стиральная машина",
        "Котёл",
        "Тёплый пол",
        "Видеонаблюдение",
        "Сигнализация",
        "Люстра",
        "Розетка",
        "Аварийный вызов",
    ):
        assert banned not in labels
    assert [item["label"] for item in catalog["executors"]][-1] == "Другой"
    assert catalog["objects"] == []
    assert catalog["materials"] == []
