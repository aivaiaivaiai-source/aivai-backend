"""Medical goods are devices and care products, not licensed medicines."""
from app.seeds.med_sections_catalog import MED_SECTIONS


def test_med_sections_exclude_licensed_medicines() -> None:
    assert len(MED_SECTIONS) == 16
    seen: dict[str, str] = {}
    for catalog in MED_SECTIONS.values():
        roles = [item["label"] for item in catalog["roles"]]
        assert catalog["question"] == "Какой товар?"
        assert roles[-1].startswith("Друг")
        for role in roles:
            assert role not in seen, role
            seen[role] = catalog["label"]
        labels = [item["label"] for item in catalog["filters"]]
        assert labels == ["Продавец", "Состояние"]
        sellers = catalog["filters"][0]["options"]
        assert [item["label"] for item in sellers] == [
            "Аптека",
            "Частное лицо",
            "Магазин",
            "Компания",
        ]
    assert seen["Глюкометры"] == "Товары для диабетиков"
    assert seen["Небулайзеры"] == "Ингаляторы/товары для дыхания"
    assert seen["Очки для зрения"] == "Оптика и товары для зрения"
    assert seen["Витаминные комплексы"] == "БАДы и товары для здоровья"
    banned = {
        "Инсулин",
        "Антибиотики",
        "Лекарства",
        "Таблетки",
        "Обезболивающие",
        "Средства для похудения",
        "Антисептики",
        "Солнцезащитные очки",
        "Подгузники",
        "Ходунки",
        "Матрасы",
        "Перчатки",
        "Медицинские кушетки",
        "Стерилизаторы",
        "Аппараты УЗИ",
        "Стоматологические установки",
        "Маски для лица",
        "Респираторы и очки",
    }
    assert banned.isdisjoint(seen)
