"""Construction goods are sales, and filters stay with the product."""
from app.seeds.repair_sections_catalog import REPAIR_SECTIONS


def _labels(key: str) -> set[str]:
    return {item["label"] for item in REPAIR_SECTIONS[key]["filters"]}


def _filter(key: str, label: str) -> dict:
    return next(item for item in REPAIR_SECTIONS[key]["filters"] if item["label"] == label)


def test_repair_goods_do_not_overlap() -> None:
    assert len(REPAIR_SECTIONS) == 28
    seen: dict[str, str] = {}
    for catalog in REPAIR_SECTIONS.values():
        roles = [item["label"] for item in catalog["roles"]]
        assert roles[-1].startswith("Друг")
        assert catalog["question"] == "Какой товар?"
        for role in roles:
            assert role not in seen, role
            seen[role] = catalog["label"]
    banned = {
        "Камин",
        "Беседка",
        "Лопата",
        "Бензопила",
        "Газонокосилка",
        "Ковёр",
        "Установка окон",
        "Экскаватор",
    }
    assert banned.isdisjoint(seen)
    assert seen["Профнастил"] == "Кровля и водостоки"
    assert seen["Вагонка"] == "Пиломатериалы"
    assert seen["Водонагреватели"] == "Сантехника и водоснабжение"
    assert "Состояние" not in _labels("mixes")
    assert "Состояние" not in _labels("paint")
    assert "Б/у" not in [opt["label"] for opt in _filter("paint", "Упаковка")["options"]]
    assert "Питание" in _labels("power-tools")
    assert "Питание" not in _labels("hand-tools")
    assert "Кондиционеры" not in seen
    assert "Тип кондиционера" not in _labels("climate")
    assert _filter("equipment", "Топливо")["applies_to"] == ["Генераторы"]
    assert _filter("lumber", "Влажность")["applies_to"] == ["Доска", "Брус", "Вагонка"]
    assert "Фанера" not in _filter("lumber", "Влажность")["applies_to"]
