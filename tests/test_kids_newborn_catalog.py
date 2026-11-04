"""Newborn goods stay out of sibling Kids World sections."""
from app.seeds.kids_newborn_catalog import build_newborn_goods_catalog


def test_newborn_goods_are_products() -> None:
    catalog = build_newborn_goods_catalog()
    kinds = [item["label"] for item in catalog["roles"]]
    filters = {item["label"]: [opt["label"] for opt in item["options"]] for item in catalog["filters"]}
    assert catalog["label"] == "Товары для новорождённых"
    assert catalog["question"] == "Какой товар?"
    assert kinds[0] == "Конверты на выписку"
    assert kinds[-1] == "Другие товары для новорождённых"
    assert len(kinds) == len(set(kinds))
    for banned in (
        "Коляска",
        "Автокресло",
        "Кенгуру",
        "Слинг",
        "Боди",
        "Комбинезон",
        "Пинетки",
        "Подгузники",
        "Смесь",
        "Кроватка",
        "Манеж",
        "Погремушка",
        "Радионяня",
        "Велосипед",
    ):
        assert banned not in kinds
    assert filters["Продавец"] == ["Частное лицо", "Магазин", "Другой"]
    assert filters["Состояние"] == ["Новое", "Б/у"]
    assert "Для мальчика" in filters["Пол"]
    assert "0-3 месяца" in filters["Возраст"]
    assert filters["Сезон"] == ["Лето", "Демисезон", "Зима"]
    season = next(item for item in catalog["filters"] if item["label"] == "Сезон")
    assert season["applies_to"] == ["Конверты на выписку"]
    for item in catalog["filters"]:
        if item["label"] != "Сезон":
            assert "applies_to" not in item
