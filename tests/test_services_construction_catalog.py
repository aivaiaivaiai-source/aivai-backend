"""Construction services catalog stays clear of sibling service sections."""
from app.seeds.services_construction_catalog import build_construction_services_catalog


def test_construction_kinds_skip_sibling_sections() -> None:
    catalog = build_construction_services_catalog()
    labels = [item["label"] for item in catalog["kinds"]]
    assert labels[0] == "Строительство под ключ"
    assert labels[-1] == "Другие строительные работы"
    assert "Алмазное сверление и резка" in labels
    assert "Установка окон и дверей" in labels
    assert "Лестницы и перила" in labels
    assert "Гипсокартон, стены и перегородки" in labels
    assert "Гидроизоляция и шумоизоляция" in labels
    for banned in (
        "Сантехника",
        "Электрика",
        "Отопление",
        "Мебель",
        "Спецтехника",
        "Проектирование",
        "Газификация",
        "Вентиляция",
        "Бани, гаражи и веранды",
        "Коммерческое строительство",
        "Заборы, ворота и навесы",
        "Капитальный ремонт",
        "Косметический ремонт",
        "Двери",
        "Окна и балконы",
        "Лестницы",
        "Гипсокартон",
        "Гидроизоляция",
    ):
        assert banned not in labels
    assert [item["label"] for item in catalog["executors"]][-1] == "Другой"
    assert [item["label"] for item in catalog["objects"]][-1] == "Другое"
    assert "С материалом" in [item["label"] for item in catalog["materials"]]
