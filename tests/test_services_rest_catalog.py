"""Remaining service sections — Package A merged catalogs stay coherent."""
from app.seeds.services_climate_catalog import build_climate_services_catalog
from app.seeds.services_construction_catalog import build_construction_services_catalog
from app.seeds.services_electrical_catalog import build_electrical_services_catalog
from app.seeds.services_furniture_catalog import build_furniture_services_catalog
from app.seeds.services_household_catalog import build_household_services_catalog
from app.seeds.services_plumbing_catalog import build_plumbing_services_catalog
from app.seeds.services_rest_catalog import SERVICE_SECTIONS

# Retired L2 section keys kept for API compat; kinds intentionally overlap parents.
_RETIRED_SECTION_KEYS = frozenset(
    {
        "dry-cleaning",
        "sanitary",
        "appliance-install",
        "equipment-rental",
        "lockout",
        "scrap",
        "print",
        "atelier",
    }
)

_ACTIVE_SECTIONS = {
    k: v for k, v in SERVICE_SECTIONS.items() if k not in _RETIRED_SECTION_KEYS
}


def test_service_kinds_are_unique_across_active_sections() -> None:
    catalogs = [
        build_construction_services_catalog(),
        build_plumbing_services_catalog(),
        build_electrical_services_catalog(),
        build_climate_services_catalog(),
        build_furniture_services_catalog(),
        build_household_services_catalog(),
        *_ACTIVE_SECTIONS.values(),
    ]
    seen: dict[str, str] = {}
    # Household already includes lock/atelier kinds; rest active must not collide.
    dedicated = [
        build_construction_services_catalog(),
        build_plumbing_services_catalog(),
        build_electrical_services_catalog(),
        build_climate_services_catalog(),
        build_furniture_services_catalog(),
        build_household_services_catalog(),
    ]
    # Skip household vs rest uniqueness for kinds that were merged into household.
    for catalog in dedicated[:-1] + list(_ACTIVE_SECTIONS.values()):
        kinds = [item["label"] for item in catalog["kinds"]]
        assert kinds
        assert kinds[-1].startswith("Друг")
        assert [item["label"] for item in catalog["executors"]][-1] == "Другой"
        for kind in kinds:
            assert kind not in seen, f"{kind} is in {seen.get(kind)} and {catalog['label']}"
            seen[kind] = catalog["label"]
    household_kinds = {
        item["label"] for item in build_household_services_catalog()["kinds"]
    }
    assert "Пошив одежды" in household_kinds
    assert "Вскрытие дверных замков" in household_kinds
    assert "realtor" in SERVICE_SECTIONS
    assert SERVICE_SECTIONS["cleaning"]["label"] == "Клининг"
    assert SERVICE_SECTIONS["it"]["label"] == "IT-услуги"
    assert "Химчистка одежды и текстиля" in [
        i["label"] for i in SERVICE_SECTIONS["cleaning"]["kinds"]
    ]
    assert "Риелторские услуги" not in [
        i["label"] for i in SERVICE_SECTIONS["other"]["kinds"]
    ]
    assert seen["Услуги садовника"] == "Сельскохозяйственные услуги"
    assert seen["Оцифровка фото и видео"] == "Фото и видеосъёмка"
    assert seen["Установка кондиционеров"] == "Отопление и климат"
    assert seen["Ремонт компьютеров и ноутбуков"] == "IT-услуги"
    assert seen["Печать полиграфии"] == "Реклама и маркетинг"
    medical = [item["label"] for item in SERVICE_SECTIONS["medical"]["executors"]]
    moving = [item["label"] for item in SERVICE_SECTIONS["moving"]["executors"]]
    assert SERVICE_SECTIONS["medical"]["executor_label"] == "Специалист"
    assert medical == ["Частный специалист", "Клиника", "Другой"]
    assert SERVICE_SECTIONS["moving"]["executor_label"] == "Перевозчик"
    assert moving == ["Частный перевозчик", "Транспортная компания", "Другой"]
    assert "Бригада" not in moving
    assert len(SERVICE_SECTIONS) == 33  # 32 historical keys + realtor
