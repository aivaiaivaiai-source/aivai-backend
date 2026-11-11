"""Animals sell the animal or the supply, not food or licensed drugs."""
from app.seeds.animals_sections_catalog import ANIMALS_SECTIONS
from app.seeds.animals_v2 import (
    ANIMALS_SELLER_CHOICES,
    ANIMALS_V2_BANNED_KIND_LABELS,
    ANIMALS_V2_EXPECTED_L2_COUNT,
)


def test_animals_sections_keep_their_own_goods() -> None:
    assert len(ANIMALS_SECTIONS) == ANIMALS_V2_EXPECTED_L2_COUNT
    assert "vetservices" not in ANIMALS_SECTIONS
    seen: dict[str, str] = {}
    for catalog in ANIMALS_SECTIONS.values():
        roles = [item["label"] for item in catalog["roles"]]
        assert roles[-1].startswith("Друг") or roles[-1].startswith("Вязка")
        labels = [item["label"] for item in catalog["filters"]]
        assert "Регион" not in labels
        assert "Город" not in labels
        assert "Порода" not in labels
        assert "Назначение" not in labels
        seller = catalog["filters"][0]
        assert seller["label"] == "Кто продаёт"
        assert [o["label"] for o in seller["options"]] == list(ANIMALS_SELLER_CHOICES)
        for role in roles:
            assert role not in seen, role
            seen[role] = catalog["label"]
    assert seen["Собаки"] == "Собаки"
    assert seen["Щенки"] == "Собаки"
    assert seen["Пчелосемьи"] == "Пчеловодство"
    assert seen["Инкубационные яйца"] == "Птицеводство"
    assert seen["Сено"] == "Сено, Корма и кормовые добавки"
    assert "Груминг" not in seen
    assert ANIMALS_SECTIONS["dogs"]["question"] == "Какое животное?"
    assert [item["label"] for item in ANIMALS_SECTIONS["dogs"]["filters"]] == [
        "Кто продаёт",
        "Пол",
    ]
    assert "Состояние" not in [
        item["label"] for item in ANIMALS_SECTIONS["dogs"]["filters"]
    ]
    assert [item["label"] for item in ANIMALS_SECTIONS["accessories"]["filters"]] == [
        "Кто продаёт",
        "Состояние",
    ]
    assert [item["label"] for item in ANIMALS_SECTIONS["vetgoods"]["filters"]] == [
        "Кто продаёт"
    ]
    assert [item["label"] for item in ANIMALS_SECTIONS["feed"]["filters"]] == [
        "Кто продаёт"
    ]
    assert ANIMALS_V2_BANNED_KIND_LABELS.isdisjoint(seen)
