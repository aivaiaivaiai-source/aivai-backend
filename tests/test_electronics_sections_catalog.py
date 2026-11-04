"""Electronics goods stay in their own sections, with brand-owned models."""
from app.seeds.electronics_sections_catalog import ELECTRONICS_SECTIONS


def test_electronics_sections_do_not_overlap() -> None:
    assert len(ELECTRONICS_SECTIONS) == 19
    seen: dict[str, str] = {}
    for catalog in ELECTRONICS_SECTIONS.values():
        roles = [item["label"] for item in catalog["roles"]]
        assert roles[-1].startswith("Друг")
        for role in roles:
            assert role not in seen, role
            seen[role] = catalog["label"]
        brands = next(item for item in catalog["filters"] if item["label"] == "Марка")
        models = next(item for item in catalog["filters"] if item["label"] == "Модель")
        assert models["depends_on"] == "Марка"
        parents = {item["label"] for item in brands["options"]}
        for model in models["options"]:
            assert model["parent"] in parents
    assert seen["Кондиционеры"] == "Климатическая техника"
    banned = {
        "Котлы отопления",
        "Водонагреватели",
        "Генераторы",
        "Детские часы",
        "Кабель и провод",
        "Пылесосы",
    }
    assert seen["Пылесосы"] == "Бытовая техника"
    banned.remove("Пылесосы")
    assert banned.isdisjoint(seen)
    phones = ELECTRONICS_SECTIONS["phones"]
    iphone = next(
        item
        for item in next(group for group in phones["filters"] if group["label"] == "Модель")["options"]
        if item["label"] == "iPhone 15"
    )
    assert iphone["parent"] == "Apple"
    assert iphone["for_kinds"] == ["Смартфоны"]
