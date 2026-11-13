"""Ready business catalog mirrors V2 cleaned product identity."""
from app.seeds.ready_business_sections_catalog import READY_BUSINESS_SECTIONS
from app.seeds.ready_business_v2 import (
    READY_BUSINESS_POSTER_OPTIONS,
    READY_BUSINESS_V2_EXPECTED_L2_COUNT,
    ready_business_v2_kind_count,
)


def test_ready_business_sections_are_businesses() -> None:
    assert len(READY_BUSINESS_SECTIONS) == READY_BUSINESS_V2_EXPECTED_L2_COUNT
    assert ready_business_v2_kind_count() == 70
    seen: dict[str, str] = {}
    for catalog in READY_BUSINESS_SECTIONS.values():
        roles = [item["label"] for item in catalog["roles"]]
        assert catalog["question"] == "Какой бизнес?"
        assert roles[-1].startswith("Друг")
        for role in roles:
            assert role not in seen, role
            seen[role] = catalog["label"]
        labels = [item["label"] for item in catalog["filters"]]
        assert labels[0] == "Кто разместил"
        posters = [item["label"] for item in catalog["filters"][0]["options"]]
        assert posters == list(READY_BUSINESS_POSTER_OPTIONS)
        assert "Посредник" not in posters
        assert "Франчайзер" not in posters
        assert "Состояние" not in labels
        assert "Регион" not in labels
        assert "Город" not in labels
    assert seen["Магазины"] == "Магазины и торговые точки"
    assert seen["Фудтраки"] == "Кафе, рестораны и общепит"
    assert seen["Аптеки"] == "Медицинские центры и аптеки"
    assert seen["Вендинг"] == "Прочий готовый бизнес"
    assert "Готовые ОсОО" not in seen
    assert "Линии" not in seen
    assert "Офисы" not in seen
    assert "Доля" not in seen
    assert "Майнинг-фермы" not in seen
    franchise = READY_BUSINESS_SECTIONS["franchise"]
    assert franchise["label"] == "Франшизы"
    assert "Помещение" not in [f["label"] for f in franchise["filters"]]
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
    assert "shares" not in READY_BUSINESS_SECTIONS
    assert "crypto" not in READY_BUSINESS_SECTIONS
    assert "turnkey" not in READY_BUSINESS_SECTIONS
