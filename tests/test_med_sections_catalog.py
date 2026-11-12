"""Medical goods are devices and care products, not licensed medicines."""
from app.seeds.med_sections_catalog import MED_SECTIONS
from app.seeds.medical_v2 import (
    LICENSED_MEDICINES_BANNED,
    MEDICAL_SELLER_TARGET,
    MEDICAL_V2_RETIRED_SUPPLEMENT_KINDS,
    medical_v2_condition_decision,
)


def test_med_sections_exclude_licensed_medicines() -> None:
    assert len(MED_SECTIONS) == 15
    seen: dict[str, str] = {}
    for catalog in MED_SECTIONS.values():
        roles = [item["label"] for item in catalog["roles"]]
        assert catalog["question"] == "Какой товар?"
        assert roles[-1].startswith("Друг")
        for role in roles:
            assert role not in seen, role
            seen[role] = catalog["label"]
        labels = [item["label"] for item in catalog["filters"]]
        assert labels[0] == "Продавец"
        sellers = catalog["filters"][0]["options"]
        assert [item["label"] for item in sellers] == list(MEDICAL_SELLER_TARGET)
        yes_kinds = [r for r in roles if medical_v2_condition_decision(r) == "YES"]
        if yes_kinds:
            assert "Состояние" in labels
            condition = next(g for g in catalog["filters"] if g["label"] == "Состояние")
            assert condition.get("applies_to") == yes_kinds
            assert [o["label"] for o in condition["options"]] == ["Новое", "Б/у"]
        else:
            assert "Состояние" not in labels
    assert seen["Глюкометры"] == "Товары для диабетиков"
    assert seen["Небулайзеры"] == "Ингаляторы/товары для дыхания"
    assert seen["Очки для зрения"] == "Оптика и товары для зрения"
    assert "Витаминные комплексы" not in seen
    assert MEDICAL_V2_RETIRED_SUPPLEMENT_KINDS.isdisjoint(seen)
    banned = set(LICENSED_MEDICINES_BANNED) | {
        "Солнцезащитные очки",
        "Подгузники",
        "Ходунки",
        "Матрасы",
        "Перчатки",
        "Медицинские кушетки",
        "Стерилизаторы",
        "Аппараты УЗИ",
        "Стоматологические установки",
        "Маски для лица",
        "Респираторы и очки",
    }
    assert banned.isdisjoint(seen)
