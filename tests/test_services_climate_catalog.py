"""Climate kinds are trades, not appliance models or sibling sections."""
from app.seeds.services_climate_catalog import build_climate_services_catalog


def test_climate_kinds_are_trades() -> None:
    catalog = build_climate_services_catalog()
    labels = [item["label"] for item in catalog["kinds"]]
    assert catalog["category_slug"] == "services-otoplenie-i-klimat"
    assert labels[0] == "Услуги отопления под ключ"
    assert "Услуги газификации" in labels
    assert labels[-1] == "Другие работы по отоплению и климату"
    assert "Установка котлов" in labels
    assert "Установка тёплого пола" in labels
    assert "Установка вентиляции" in labels
    assert "Установка кондиционеров" in labels
    assert "Обслуживание и ремонт кондиционеров" in labels
    for banned in (
        "Сантехника",
        "Электрика",
        "Водоснабжение",
        "Проектирование",
        "Сплит-система",
        "Кассетный",
        "Заправка фреоном",
        "Стиральная машина",
    ):
        assert banned not in labels
    assert [item["label"] for item in catalog["executors"]][-1] == "Другой"
    assert catalog["objects"] == []
    assert catalog["materials"] == []
