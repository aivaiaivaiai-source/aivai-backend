"""Animals sell the animal or the supply, not food or licensed drugs."""
from app.seeds.animals_sections_catalog import ANIMALS_SECTIONS


def test_animals_sections_keep_their_own_goods() -> None:
    assert len(ANIMALS_SECTIONS) == 16
    seen: dict[str, str] = {}
    for catalog in ANIMALS_SECTIONS.values():
        roles = [item["label"] for item in catalog["roles"]]
        assert roles[-1].startswith("Друг")
        labels = [item["label"] for item in catalog["filters"]]
        assert "Регион" not in labels
        assert "Город" not in labels
        for role in roles:
            assert role not in seen, role
            seen[role] = catalog["label"]
    assert seen["Алабаи"] == "Собаки"
    assert seen["Пчелосемьи"] == "Пчеловодство"
    assert seen["Инкубационные яйца"] == "Птицеводство"
    assert seen["Сено"] == "Сено, Корма и кормовые добавки"
    assert seen["Груминг"] == "Ветеринарные услуги"
    assert ANIMALS_SECTIONS["dogs"]["question"] == "Какое животное?"
    assert ANIMALS_SECTIONS["vetservices"]["question"] == "Какая услуга?"
    assert ANIMALS_SECTIONS["feed"]["filters"][0]["options"][0]["label"] == "Частное лицо"
    assert [item["label"] for item in ANIMALS_SECTIONS["feed"]["filters"]] == ["Продавец"]
    assert [item["label"] for item in ANIMALS_SECTIONS["dogs"]["filters"]] == ["Продавец", "Пол"]
    assert "Состояние" not in [item["label"] for item in ANIMALS_SECTIONS["dogs"]["filters"]]
    assert [item["label"] for item in ANIMALS_SECTIONS["accessories"]["filters"]] == [
        "Продавец",
        "Состояние",
    ]
    vet_sellers = [
        item["label"] for item in ANIMALS_SECTIONS["vetgoods"]["filters"][0]["options"]
    ]
    assert vet_sellers[0] == "Ветаптека"
    milk = next(
        item
        for item in ANIMALS_SECTIONS["sheep"]["filters"]
        if item["label"] == "Назначение"
        for item in item["options"]
        if item["label"] == "Для молока"
    )
    assert milk["for_kinds"] == ["Козы"]
    banned = {
        "Мёд",
        "Соты",
        "Перга",
        "Прополис",
        "Пыльца",
        "Яйца",
        "Молоко",
        "Пшеница",
        "Ячмень",
        "Ветеринарные услуги",
        "Уход за животными",
        "Антибиотики",
        "Вакцины",
        "Лекарства",
        "Таблетки",
        "Сёдла",
    }
    assert banned.isdisjoint(seen)
