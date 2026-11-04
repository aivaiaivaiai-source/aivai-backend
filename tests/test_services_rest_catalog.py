"""Remaining service sections do not repeat each other or earlier sections."""
from app.seeds.services_climate_catalog import build_climate_services_catalog
from app.seeds.services_construction_catalog import build_construction_services_catalog
from app.seeds.services_electrical_catalog import build_electrical_services_catalog
from app.seeds.services_furniture_catalog import build_furniture_services_catalog
from app.seeds.services_household_catalog import build_household_services_catalog
from app.seeds.services_plumbing_catalog import build_plumbing_services_catalog
from app.seeds.services_rest_catalog import SERVICE_SECTIONS


def test_service_kinds_are_unique_across_sections() -> None:
    catalogs = [
        build_construction_services_catalog(),
        build_plumbing_services_catalog(),
        build_electrical_services_catalog(),
        build_climate_services_catalog(),
        build_furniture_services_catalog(),
        build_household_services_catalog(),
        *SERVICE_SECTIONS.values(),
    ]
    seen: dict[str, str] = {}
    labels = {item["label"] for item in catalogs}
    assert len(labels) == len(catalogs)
    assert len(SERVICE_SECTIONS) == 32
    for catalog in catalogs:
        kinds = [item["label"] for item in catalog["kinds"]]
        assert kinds
        assert kinds[-1].startswith("Друг")
        assert [item["label"] for item in catalog["executors"]][-1] == "Другой"
        for kind in kinds:
            assert kind not in seen, f"{kind} is in {seen.get(kind)} and {catalog['label']}"
            seen[kind] = catalog["label"]
    for catalog in SERVICE_SECTIONS.values():
        assert catalog["objects"] == []
        assert catalog["materials"] == []
    assert seen["Услуги садовника"] == "Сельскохозяйственные услуги"
    assert seen["Гравировка"] == "Полиграфия и печатные услуги"
    assert seen["Оцифровка фото и видео"] == "Фото и видеосъёмка"
    assert seen["Установка кондиционеров"] == "Отопление и климат"
    assert seen["Ремонт компьютеров и ноутбуков"] == "Компьютеры и IT-услуги"
    medical = [item["label"] for item in SERVICE_SECTIONS["medical"]["executors"]]
    moving = [item["label"] for item in SERVICE_SECTIONS["moving"]["executors"]]
    assert SERVICE_SECTIONS["medical"]["executor_label"] == "Специалист"
    assert medical == ["Частный специалист", "Клиника", "Другой"]
    assert SERVICE_SECTIONS["moving"]["executor_label"] == "Перевозчик"
    assert moving == ["Частный перевозчик", "Транспортная компания", "Другой"]
    assert "Бригада" not in moving
