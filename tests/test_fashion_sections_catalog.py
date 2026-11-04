"""Fashion goods stay in their own sections, with brand-owned models."""
from app.seeds.fashion_sections_catalog import FASHION_SECTIONS


def test_fashion_sections_do_not_overlap() -> None:
    assert len(FASHION_SECTIONS) == 17
    seen: dict[str, str] = {}
    for catalog in FASHION_SECTIONS.values():
        roles = [item["label"] for item in catalog["roles"]]
        assert catalog["question"] == "Какой товар?"
        assert roles[-1].startswith("Друг")
        for role in roles:
            assert role not in seen, role
            seen[role] = catalog["label"]
        labels = [item["label"] for item in catalog["filters"]]
        assert "Марка" not in labels
        assert "Модель" not in labels
        assert "Ткани и фурнитура" not in seen.values()
    assert seen["Калпаки"] == "Национальная одежда"
    assert seen["Свадебные платья"] == "Свадебная и вечерняя одежда"
    assert seen["Женские кроссовки"] == "Женская обувь"
    women_size = next(item for item in FASHION_SECTIONS["women"]["filters"] if item["label"] == "Размер")
    men_size = next(item for item in FASHION_SECTIONS["men"]["filters"] if item["label"] == "Размер")
    women_shoe = next(item for item in FASHION_SECTIONS["women-shoes"]["filters"] if item["label"] == "Размер")
    men_shoe = next(item for item in FASHION_SECTIONS["men-shoes"]["filters"] if item["label"] == "Размер")
    assert women_size["options"][-1]["label"] == "66"
    assert men_size["options"][-1]["label"] == "66"
    assert women_shoe["options"][-1]["label"] == "46"
    assert men_shoe["options"][-1]["label"] == "46"
    banned = {
        "Школьная форма",
        "Школьные рюкзаки",
        "Пинетки",
        "Умные часы",
        "Украшения для пирсинга",
        "Шырдаки",
        "Юрты",
        "Каски",
        "Строительная спецобувь",
        "Рабочие костюмы",
        "Медицинская одежда",
        "Пряжа",
        "Карнавальные костюмы",
        "Фены",
    }
    assert banned.isdisjoint(seen)
