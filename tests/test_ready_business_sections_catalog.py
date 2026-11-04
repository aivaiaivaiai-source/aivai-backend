"""Ready business is the going concern, not the machines or the medicines."""
from app.seeds.ready_business_sections_catalog import READY_BUSINESS_SECTIONS


def test_ready_business_sections_are_businesses() -> None:
    assert len(READY_BUSINESS_SECTIONS) == 19
    seen: dict[str, str] = {}
    for catalog in READY_BUSINESS_SECTIONS.values():
        roles = [item["label"] for item in catalog["roles"]]
        assert catalog["question"] == "Какой бизнес?"
        assert roles[-1].startswith("Друг")
        for role in roles:
            assert role not in seen, role
            seen[role] = catalog["label"]
        labels = [item["label"] for item in catalog["filters"]]
        assert labels[0] == "Продавец"
        sellers = [item["label"] for item in catalog["filters"][0]["options"]]
        assert "Посредник" not in sellers
        if catalog["label"] != "Доля в бизнесе и инвестиции":
            assert sellers[-1] == "Агентство"
        assert "Состояние" not in labels
        assert "Регион" not in labels
        assert "Город" not in labels
    assert seen["Магазины"] == "Магазины и торговые точки"
    assert seen["Бутики"] == "Магазины и торговые точки"
    assert seen["Островки"] == "Магазины и торговые точки"
    assert seen["Фудтраки"] == "Кафе, рестораны и общепит"
    assert seen["Аптеки"] == "Медицинские центры и аптеки"
    assert seen["Готовые ОсОО"] == "Прочий готовый бизнес"
    assert seen["Майнинг-фермы"] == "Криптобизнес и цифровые активы"
    franchise = READY_BUSINESS_SECTIONS["franchise"]["filters"][0]["options"]
    assert franchise[0]["label"] == "Франчайзер"
    banned = {
        "Игровые автоматы",
        "Бильярдные столы",
        "Частный детский сад",
        "Место в детском саду",
        "Ходунки",
        "Инсулин",
        "Генераторы",
        "Промышленные прямострочки",
        "Холодильные витрины",
        "Готовый бизнес",
        "Продуктовые магазины",
        "Фермы",
        "Пекарни",
        "Пасеки",
    }
    assert banned.isdisjoint(seen)
