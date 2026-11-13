"""Raw materials are feedstock, not finished goods from other catalogs."""
from app.seeds.materials_sections_catalog import MATERIALS_SECTIONS
from app.seeds.materials_v2 import (
    MATERIALS_SELLER_TARGET,
    MATERIALS_V2_SECTION_KINDS,
    materials_v2_kind_count,
)


def test_materials_do_not_steal_finished_goods() -> None:
    assert len(MATERIALS_SECTIONS) == 18
    assert set(MATERIALS_SECTIONS) == set(MATERIALS_V2_SECTION_KINDS)
    assert materials_v2_kind_count() == 117
    seen: dict[str, str] = {}
    for catalog in MATERIALS_SECTIONS.values():
        roles = [item["label"] for item in catalog["roles"]]
        assert roles[-1].startswith("Друг")
        labels = [item["label"] for item in catalog["filters"]]
        assert labels == ["Продавец", "Цена за"]
        assert "Состояние" not in labels
        assert "Регион" not in labels
        assert "Город" not in labels
        sellers = [item["label"] for item in catalog["filters"][0]["options"]]
        assert sellers == list(MATERIALS_SELLER_TARGET)
        basis = [item["label"] for item in catalog["filters"][1]["options"]]
        assert len(basis) == 11
        assert "кг" in basis and "Другое" in basis
        for role in roles:
            assert role not in seen, role
            seen[role] = catalog["label"]
    assert seen["Пряжа"] == "Нитки, пряжа и волокно"
    assert seen["Молнии"] == "Швейная фурнитура"
    assert seen["Сухое молоко"] == "Пищевое сырьё и ингредиенты"
    assert "Контейнерная поставка" not in seen
    assert "import" not in MATERIALS_SECTIONS
    banned = {
        "Доска",
        "Брус",
        "Фанера",
        "Вагонка",
        "Цемент",
        "Кирпич",
        "Арматура",
        "Трубы стальные",
        "Интерьерные краски",
        "Фасадные краски",
        "Эмали",
        "Лаки",
        "Грунтовки",
        "Мука",
        "Сахар",
        "Дрожжи",
        "Крахмал",
        "Какао",
        "Пшеница",
        "Мёд",
        "Молоко",
        "Бумага",
        "Бумага для рисования",
        "Кольца",
        "Серьги",
        "Шампуни",
        "Мыло",
        "Масла для волос",
        "Спицы и крючки",
        "Пенопласт и пеноплекс",
        "Плёнки и мембраны",
        "Партия под заказ",
        "Контейнерная поставка",
        "Регулярные поставки",
    }
    assert banned.isdisjoint(seen)
