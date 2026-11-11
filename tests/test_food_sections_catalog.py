"""Food stays in its own sections and does not take kids or animal goods."""
from app.seeds.food_agri_v2 import FOOD_AGRI_V2_EXPECTED_L2_COUNT
from app.seeds.food_sections_catalog import FOOD_SECTIONS


def test_food_sections_do_not_overlap() -> None:
    assert len(FOOD_SECTIONS) == FOOD_AGRI_V2_EXPECTED_L2_COUNT
    seen: dict[str, str] = {}
    for catalog in FOOD_SECTIONS.values():
        roles = [item["label"] for item in catalog["roles"]]
        assert catalog["question"] == "Какой товар?"
        assert roles[-1].startswith("Друг")
        for role in roles:
            assert role not in seen, role
            seen[role] = catalog["label"]
        assert [item["label"] for item in catalog["filters"]] == ["Кто продаёт"]
        seller_opts = [o["label"] for o in catalog["filters"][0]["options"]]
        assert seller_opts == [
            "Частное лицо",
            "Фермер",
            "Магазин",
            "Другой",
        ]
    assert seen["Рис"] == "Крупы, мука/макаронные изделия"
    assert seen["Пшеница"] == "Зерно и зерновые культуры"
    assert seen["Мёд"] == "Мёд и продукты пчеловодства"
    assert seen["Помидоры"] == "Овощи и фрукты"
    banned = {
        "Молочные смеси",
        "Каши для прикорма",
        "Пюре для прикорма",
        "Сено",
        "Комбикорм",
        "Корм для собак",
        "Улей",
        "Пищевое сырьё",
        "БАДы",
        "Овощи оптом",
        "Фермерские наборы",
        "Стеклянные банки",
        "Мешки",
    }
    assert banned.isdisjoint(seen)
