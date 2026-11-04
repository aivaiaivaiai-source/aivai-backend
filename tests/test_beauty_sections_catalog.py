"""Beauty goods stay in their own sections, with brand-owned models."""
from app.seeds.beauty_sections_catalog import BEAUTY_SECTIONS


def test_beauty_sections_do_not_overlap() -> None:
    assert len(BEAUTY_SECTIONS) == 16
    seen: dict[str, str] = {}
    for catalog in BEAUTY_SECTIONS.values():
        roles = [item["label"] for item in catalog["roles"]]
        assert catalog["question"] == "Какой товар?"
        assert roles[-1].startswith("Друг")
        for role in roles:
            assert role not in seen, role
            seen[role] = catalog["label"]
        brands = next(item for item in catalog["filters"] if item["label"] == "Марка")
        models = next(item for item in catalog["filters"] if item["label"] == "Модель")
        assert models["depends_on"] == "Марка"
        brand_kinds = {
            item["label"]: set(item.get("for_kinds") or roles) for item in brands["options"]
        }
        for model in models["options"]:
            assert model["parent"] in brand_kinds
            assert set(model["for_kinds"]).issubset(brand_kinds[model["parent"]])
    assert seen["Фены"] == "Инструменты/оборуд.е для красоты"
    assert seen["Гель-лаки"] == "Маникюр и педикюр"
    banned = {
        "Парикмахерские услуги",
        "Маникюр и педикюр",
        "Косметология",
        "Массаж",
        "Подгузники",
        "Влажные салфетки",
        "Детские маникюрные наборы",
        "БАДы и товары для здоровья",
        "Кресло барбера",
    }
    assert banned.isdisjoint(seen)
