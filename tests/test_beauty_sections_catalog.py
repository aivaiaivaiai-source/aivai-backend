"""Beauty V2 section catalog — simple seller + semantic Condition only."""
from app.seeds.beauty_sections_catalog import BEAUTY_SECTIONS
from app.seeds.beauty_v2 import beauty_v2_assert_cleanup_contracts, beauty_v2_kind_count


def test_beauty_sections_v2_simple() -> None:
    beauty_v2_assert_cleanup_contracts()
    assert len(BEAUTY_SECTIONS) == 16
    seen: dict[str, str] = {}
    for catalog in BEAUTY_SECTIONS.values():
        roles = [item["label"] for item in catalog["roles"]]
        assert catalog["question"] == "Какой товар?"
        assert roles[-1].startswith("Друг")
        for role in roles:
            assert role not in seen, role
            seen[role] = catalog["label"]
        labels = [item["label"] for item in catalog["filters"]]
        assert labels[0] == "Продавец"
        assert "Марка" not in labels
        assert "Модель" not in labels
        assert "Упаковка" not in labels
    assert seen["Фены"] == "Инструменты/оборуд.е для красоты"
    assert seen["Гель-лаки"] == "Товары для маникюра и педикюра"
    assert seen["Парики и шиньоны"] == "Прочее для красоты и ухода"
    assert "Косметички" not in seen
    assert "Украшения для пирсинга" not in seen
    banned = {
        "Парикмахерские услуги",
        "Косметология",
        "Массаж",
        "Подгузники",
        "Влажные салфетки",
        "Детские маникюрные наборы",
        "БАДы и товары для здоровья",
        "Кресло барбера",
        "Другое оборудование для красоты",
    }
    assert banned.isdisjoint(seen)
    assert len(seen) == beauty_v2_kind_count()
