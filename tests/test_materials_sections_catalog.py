"""Raw materials are feedstock, not finished goods from other catalogs."""
from app.seeds.materials_sections_catalog import MATERIALS_SECTIONS


def test_materials_do_not_steal_finished_goods() -> None:
    assert len(MATERIALS_SECTIONS) == 19
    seen: dict[str, str] = {}
    for catalog in MATERIALS_SECTIONS.values():
        roles = [item["label"] for item in catalog["roles"]]
        assert roles[-1].startswith("Друг")
        labels = [item["label"] for item in catalog["filters"]]
        assert labels[0] == "Продавец"
        assert "Регион" not in labels
        assert "Город" not in labels
        sellers = [item["label"] for item in catalog["filters"][0]["options"]]
        assert sellers[0] in {"Оптовик", "Импортёр"}
        for role in roles:
            assert role not in seen, role
            seen[role] = catalog["label"]
    assert seen["Пряжа"] == "Нитки, пряжа и волокно"
    assert seen["Молнии"] == "Швейная фурнитура"
    assert seen["Сухое молоко"] == "Пищевое сырьё и ингредиенты"
    assert seen["Контейнерная поставка"] == "Импорт и оптовые поставки сырья"
    assert MATERIALS_SECTIONS["import"]["question"] == "Какая поставка?"
    assert [item["label"] for item in MATERIALS_SECTIONS["food"]["filters"]] == ["Продавец"]
    assert "Состояние" in [item["label"] for item in MATERIALS_SECTIONS["fabric"]["filters"]]
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
    }
    assert banned.isdisjoint(seen)
