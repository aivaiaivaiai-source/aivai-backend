# -*- coding: utf-8 -*-
"""Services V2 Package A — canonical taxonomy + Create field SoT.

31 active L2 leaves under root ``services``. Shared base:
service_kind + executor + price («Цена от», optional) + negotiable
(«По договорённости») + contact_methods
(+ multi_select service_object where catalogs already had objects).
No service_materials in Create SoT.

Search filters / facets: build_services_v2_search_filters (Package B).
"""
from __future__ import annotations

from typing import Any

from app.models.category_enums import (
    CategoryEntityType,
    CategoryFieldType,
    CategoryFilterType,
)
from app.seeds.services_climate_catalog import build_climate_services_catalog
from app.seeds.services_construction_catalog import (
    build_construction_services_catalog,
)
from app.seeds.services_electrical_catalog import (
    build_electrical_services_catalog,
)
from app.seeds.services_furniture_catalog import build_furniture_services_catalog
from app.seeds.services_household_catalog import build_household_services_catalog
from app.seeds.services_plumbing_catalog import build_plumbing_services_catalog
from app.seeds.services_rest_catalog import SERVICE_SECTIONS

SERVICES_ROOT_SLUG = "services"
SERVICES_ROOT_LABEL = "Услуги"

# Canonical L2 in final picker order: (slug, label, sort_order)
SERVICES_V2_CANONICAL_LEAVES: tuple[tuple[str, str, int], ...] = (
    ("services-stroitelnye-i-remontnye-uslugi", "Строительные и ремонтные услуги", 10),
    ("services-santehnika", "Сантехника", 20),
    ("services-elektrika", "Электрика", 30),
    ("services-otoplenie-i-klimat", "Отопление и климат", 40),
    ("services-mebel-i-interer", "Мебель и интерьер", 50),
    ("services-remont-tehniki", "Ремонт техники", 60),
    ("services-bytovye-uslugi", "Бытовые услуги", 70),
    ("services-uborka-i-klining", "Клининг", 80),
    ("services-uslugi-krasoty-i-stilya", "Услуги красоты и стиля", 90),
    ("services-meditsinskie-uslugi", "Медицинские услуги", 100),
    ("services-kompyutery-i-it-uslugi", "IT-услуги", 110),
    ("services-reklama-i-marketing", "Реклама и маркетинг", 120),
    ("services-foto-i-videosemka", "Фото и видеосъёмка", 130),
    ("services-uslugi-dizayna-i-proektirovaniya", "Услуги дизайна и проектирования", 140),
    ("services-organizatsiya-meropriyatiy", "Организация мероприятий", 150),
    ("services-muzykalnye-uslugi", "Музыкальные услуги", 160),
    ("services-obuchenie-i-repetitorstvo", "Обучение и репетиторство", 170),
    ("services-perevody-i-rabota-s-tekstom", "Переводы и работа с текстом", 180),
    ("services-yuridicheskie-uslugi", "Юридические услуги", 190),
    ("services-buhgalterskie-uslugi", "Бухгалтерские услуги", 200),
    ("services-finansovye-uslugi", "Финансовые услуги", 210),
    ("services-rieltorskie-uslugi", "Риелторские услуги", 220),
    ("services-uslugi-spetstehniki", "Услуги спецтехники", 230),
    ("services-gruzoperevozki-i-pereezdy", "Грузоперевозки и переезды", 240),
    ("services-kurerskie-uslugi", "Курьерские услуги", 250),
    ("services-turizm-i-vizovaya-podderzhka", "Туризм и визовая поддержка", 260),
    ("services-domashniy-personal", "Домашний персонал", 270),
    ("services-selskohozyaystvennye-uslugi", "Сельскохозяйственные услуги", 280),
    ("services-ohrana-i-bezopasnost", "Охрана и безопасность", 290),
    ("services-ritualnye-uslugi", "Ритуальные услуги", 300),
    ("services-prochie-uslugi", "Прочие услуги", 310),
)

SERVICES_V2_CANONICAL_SLUGS: frozenset[str] = frozenset(
    slug for slug, _label, _sort in SERVICES_V2_CANONICAL_LEAVES
)

# Merged narrow skeleton → canonical target (deterministic remap when listings=0).
SERVICES_V2_MERGE_TARGETS: dict[str, str] = {
    "services-himchistka-i-prachechnye-uslugi": "services-uborka-i-klining",
    "services-dezinfektsiya-i-sanitarnye-uslugi": "services-uborka-i-klining",
    "services-ustanovka-i-podklyuchenie-tehniki": "services-remont-tehniki",
    "services-avariynoe-vskrytie-zamkov": "services-bytovye-uslugi",
    "services-atele-i-poshiv-odezhdy": "services-bytovye-uslugi",
    "services-poligrafiya-i-pechatnye-uslugi": "services-reklama-i-marketing",
}

# Legacy 7 → canonical (except transport: ambiguous draft stays on retired node).
SERVICES_V2_LEGACY_TARGETS: dict[str, str | None] = {
    "services-repair": "services-remont-tehniki",
    "services-beauty": "services-uslugi-krasoty-i-stilya",
    "services-cleaning": "services-uborka-i-klining",
    "services-tutoring": "services-obuchenie-i-repetitorstvo",
    "services-legal": "services-yuridicheskie-uslugi",
    "services-it": "services-kompyutery-i-it-uslugi",
    "services-transport": None,
}

# Retire without Services remap (future other roots / preserve drafts).
SERVICES_V2_RETIRE_NO_TARGET: frozenset[str] = frozenset(
    {
        "services-skupka-i-pererabotka-vtorsyrya",
        "services-arenda-instrumentov-oborud-niya",
        "services-transport",
    }
)

SERVICES_V2_RETIRED_SLUGS: frozenset[str] = frozenset(
    set(SERVICES_V2_MERGE_TARGETS)
    | set(SERVICES_V2_LEGACY_TARGETS)
    | set(SERVICES_V2_RETIRE_NO_TARGET)
)

# Alias text → canonical slug (safe navigation remaps).
SERVICES_V2_ALIAS_REMAP: dict[str, str] = {
    "перевозка": "services-gruzoperevozki-i-pereezdy",
    "доставка": "services-kurerskie-uslugi",
    "грузоперевозки": "services-gruzoperevozki-i-pereezdy",
    "привезти": "services-gruzoperevozki-i-pereezdy",
    "ремонт телефона": "services-remont-tehniki",
    "ремонт айфона": "services-remont-tehniki",
    "ремонт iphone": "services-remont-tehniki",
    "ремонт ноутбука": "services-remont-tehniki",
    "ремонт стиральной": "services-remont-tehniki",
    "маникюр": "services-uslugi-krasoty-i-stilya",
    "педикюр": "services-uslugi-krasoty-i-stilya",
    "наращивание": "services-uslugi-krasoty-i-stilya",
    "стрижка": "services-uslugi-krasoty-i-stilya",
    "брови": "services-uslugi-krasoty-i-stilya",
    "ресницы": "services-uslugi-krasoty-i-stilya",
    "уборка": "services-uborka-i-klining",
    "клининг": "services-uborka-i-klining",
    "химчистка": "services-uborka-i-klining",
    "репетитор": "services-obuchenie-i-repetitorstvo",
    "обучение": "services-obuchenie-i-repetitorstvo",
    "курсы": "services-obuchenie-i-repetitorstvo",
    "юрист": "services-yuridicheskie-uslugi",
    "адвокат": "services-yuridicheskie-uslugi",
    "нотариус": "services-yuridicheskie-uslugi",
    "разработка сайта": "services-kompyutery-i-it-uslugi",
    "smm": "services-reklama-i-marketing",
    "таргет": "services-reklama-i-marketing",
    "риелтор": "services-rieltorskie-uslugi",
    "риэлтор": "services-rieltorskie-uslugi",
}

_CONTACT_METHODS = (
    "Только чат",
    "Только телефон",
    "Чат + телефон",
    "Чат + Wapp",
    "Телефон + Wapp",
    "Чат + Тел. + Wapp",
)

# Services price mode B — not product «торг».
SERVICES_NEGOTIATED_VALUE = "По договорённости"
_NEGOTIABLE = (SERVICES_NEGOTIATED_VALUE,)

_REALTOR_KINDS = ("Риелторские услуги", "Другие риелторские услуги")
_REALTOR_EXECUTORS = ("Частный риелтор", "Агентство", "Другой")


def _choices(*labels: str) -> dict[str, Any]:
    return {"choices": [{"value": label, "label": label} for label in labels]}


def _field(
    key: str,
    label: str,
    ftype: CategoryFieldType,
    required: bool,
    sort: int,
    options: dict[str, Any] | None = None,
    *,
    hint: str | None = None,
) -> tuple:
    return (key, label, ftype, required, sort, options, hint)


def _uniq(*groups: tuple[str, ...]) -> tuple[str, ...]:
    seen: set[str] = set()
    out: list[str] = []
    for group in groups:
        for item in group:
            if item in seen:
                continue
            seen.add(item)
            out.append(item)
    return tuple(out)


def _labels_from_opts(items: list[dict[str, str]]) -> tuple[str, ...]:
    return tuple(str(i["label"]) for i in items)


def _section_kinds(key: str) -> tuple[str, ...]:
    return _labels_from_opts(SERVICE_SECTIONS[key]["kinds"])


def _section_executors(key: str) -> tuple[str, ...]:
    return _labels_from_opts(SERVICE_SECTIONS[key]["executors"])


def _section_executor_label(key: str) -> str:
    return str(SERVICE_SECTIONS[key].get("executor_label") or "Исполнитель")


def build_services_v2_catalogs() -> dict[str, dict[str, Any]]:
    """Canonical leaf → catalog payload (kinds/executors/objects/materials)."""
    construction = build_construction_services_catalog()
    plumbing = build_plumbing_services_catalog()
    electrical = build_electrical_services_catalog()
    climate = build_climate_services_catalog()
    furniture = build_furniture_services_catalog()
    household = build_household_services_catalog()

    cleaning_kinds = _uniq(
        _section_kinds("cleaning"),
        _section_kinds("dry-cleaning"),
        _section_kinds("sanitary"),
    )
    repair_kinds = _uniq(
        _section_kinds("appliance-repair"),
        _section_kinds("appliance-install"),
    )
    household_kinds = _uniq(
        _labels_from_opts(household["kinds"]),
        _section_kinds("lockout"),
        _section_kinds("atelier"),
    )
    marketing_kinds = _uniq(
        _section_kinds("marketing"),
        _section_kinds("print"),
    )
    other_kinds = tuple(
        k
        for k in _section_kinds("other")
        if k != "Риелторские услуги"
    )

    catalogs: dict[str, dict[str, Any]] = {
        "services-stroitelnye-i-remontnye-uslugi": {
            "label": "Строительные и ремонтные услуги",
            "kinds": _labels_from_opts(construction["kinds"]),
            "executor_label": "Исполнитель",
            "executors": _labels_from_opts(construction["executors"]),
            "objects": _labels_from_opts(construction["objects"]),
            "materials": _labels_from_opts(construction["materials"]),
        },
        "services-santehnika": {
            "label": "Сантехника",
            "kinds": _labels_from_opts(plumbing["kinds"]),
            "executor_label": "Исполнитель",
            "executors": _labels_from_opts(plumbing["executors"]),
            "objects": _labels_from_opts(plumbing["objects"]),
            "materials": _labels_from_opts(plumbing["materials"]),
        },
        "services-elektrika": {
            "label": "Электрика",
            "kinds": _labels_from_opts(electrical["kinds"]),
            "executor_label": "Исполнитель",
            "executors": _labels_from_opts(electrical["executors"]),
            "objects": (),
            "materials": (),
        },
        "services-otoplenie-i-klimat": {
            "label": "Отопление и климат",
            "kinds": _labels_from_opts(climate["kinds"]),
            "executor_label": "Исполнитель",
            "executors": _labels_from_opts(climate["executors"]),
            "objects": (),
            "materials": (),
        },
        "services-mebel-i-interer": {
            "label": "Мебель и интерьер",
            "kinds": _labels_from_opts(furniture["kinds"]),
            "executor_label": "Исполнитель",
            "executors": _labels_from_opts(furniture["executors"]),
            "objects": (),
            "materials": (),
        },
        "services-remont-tehniki": {
            "label": "Ремонт техники",
            "kinds": repair_kinds,
            "executor_label": _section_executor_label("appliance-repair"),
            "executors": _section_executors("appliance-repair"),
            "objects": (),
            "materials": (),
        },
        "services-bytovye-uslugi": {
            "label": "Бытовые услуги",
            "kinds": household_kinds,
            "executor_label": "Исполнитель",
            "executors": _labels_from_opts(household["executors"]),
            "objects": (),
            "materials": (),
        },
        "services-uborka-i-klining": {
            "label": "Клининг",
            "kinds": cleaning_kinds,
            "executor_label": _section_executor_label("cleaning"),
            "executors": _section_executors("cleaning"),
            "objects": (),
            "materials": (),
        },
        "services-rieltorskie-uslugi": {
            "label": "Риелторские услуги",
            "kinds": _REALTOR_KINDS,
            "executor_label": "Исполнитель",
            "executors": _REALTOR_EXECUTORS,
            "objects": (),
            "materials": (),
        },
        "services-prochie-uslugi": {
            "label": "Прочие услуги",
            "kinds": other_kinds,
            "executor_label": _section_executor_label("other"),
            "executors": _section_executors("other"),
            "objects": (),
            "materials": (),
        },
    }

    rest_map = {
        "services-uslugi-krasoty-i-stilya": "beauty",
        "services-meditsinskie-uslugi": "medical",
        "services-kompyutery-i-it-uslugi": "it",
        "services-reklama-i-marketing": "marketing",
        "services-foto-i-videosemka": "photo",
        "services-uslugi-dizayna-i-proektirovaniya": "design",
        "services-organizatsiya-meropriyatiy": "events",
        "services-muzykalnye-uslugi": "music",
        "services-obuchenie-i-repetitorstvo": "education",
        "services-perevody-i-rabota-s-tekstom": "translation",
        "services-yuridicheskie-uslugi": "legal",
        "services-buhgalterskie-uslugi": "accounting",
        "services-finansovye-uslugi": "finance",
        "services-uslugi-spetstehniki": "machinery",
        "services-gruzoperevozki-i-pereezdy": "moving",
        "services-kurerskie-uslugi": "courier",
        "services-turizm-i-vizovaya-podderzhka": "tourism",
        "services-domashniy-personal": "staff",
        "services-selskohozyaystvennye-uslugi": "agriculture",
        "services-ohrana-i-bezopasnost": "security",
        "services-ritualnye-uslugi": "ritual",
    }
    for slug, key in rest_map.items():
        if slug == "services-reklama-i-marketing":
            catalogs[slug] = {
                "label": "Реклама и маркетинг",
                "kinds": marketing_kinds,
                "executor_label": _section_executor_label("marketing"),
                "executors": _section_executors("marketing"),
                "objects": (),
                "materials": (),
            }
            continue
        label = next(
            lab for s, lab, _so in SERVICES_V2_CANONICAL_LEAVES if s == slug
        )
        catalogs[slug] = {
            "label": label,
            "kinds": _section_kinds(key),
            "executor_label": _section_executor_label(key),
            "executors": _section_executors(key),
            "objects": (),
            "materials": (),
        }

    assert set(catalogs) == SERVICES_V2_CANONICAL_SLUGS
    return catalogs


def build_services_v2_core_fields() -> dict[str, list]:
    """Create SoT core fields per canonical leaf (no city — shared geo UI)."""
    catalogs = build_services_v2_catalogs()
    out: dict[str, list] = {}
    for slug, _label, _sort in SERVICES_V2_CANONICAL_LEAVES:
        cat = catalogs[slug]
        fields = [
            _field(
                "service_kind",
                "Вид услуги",
                CategoryFieldType.enum,
                True,
                10,
                _choices(*cat["kinds"]),
                hint="Какую услугу оказываете?",
            ),
            _field(
                "executor",
                cat["executor_label"],
                CategoryFieldType.enum,
                True,
                20,
                _choices(*cat["executors"]),
            ),
        ]
        if cat["objects"]:
            fields.append(
                _field(
                    "service_object",
                    "Объект",
                    CategoryFieldType.multi_select,
                    False,
                    30,
                    _choices(*cat["objects"]),
                )
            )
        # service_materials intentionally omitted — not a Create characteristic.
        fields.extend(
            [
                _field(
                    "price",
                    "Цена от",
                    CategoryFieldType.price,
                    False,
                    200,
                    hint="Минимальная цена услуги, или выберите «По договорённости»",
                ),
                _field(
                    "negotiable",
                    "По договорённости",
                    CategoryFieldType.enum,
                    False,
                    210,
                    _choices(*_NEGOTIABLE),
                    hint="Без числовой цены — цена после осмотра/обсуждения",
                ),
                _field(
                    "contact_methods",
                    "Способы связи",
                    CategoryFieldType.enum,
                    True,
                    220,
                    _choices(*_CONTACT_METHODS),
                ),
            ]
        )
        out[slug] = fields
    return out


SERVICES_V2_ENTITY_TYPE = CategoryEntityType.service


def _filter_opts(*labels: str) -> dict[str, Any]:
    return {"options": [{"value": label, "label": label} for label in labels]}


def _search_filter(
    key: str,
    label: str,
    ftype: CategoryFilterType,
    sort: int,
    options: dict[str, Any] | None,
) -> tuple:
    return (key, label, ftype, sort, options)


def build_services_v2_search_filters() -> dict[str, list]:
    """Search SoT — useful filters only (no price / negotiable / contacts).

    Geo (region/city) stays on the shared Flutter Search contract.
    """
    catalogs = build_services_v2_catalogs()
    out: dict[str, list] = {}
    for slug, _label, _sort in SERVICES_V2_CANONICAL_LEAVES:
        cat = catalogs[slug]
        filters = [
            _search_filter(
                "service_kind",
                "Вид услуги",
                CategoryFilterType.multi_select,
                10,
                _filter_opts(*cat["kinds"]),
            ),
            _search_filter(
                "executor",
                str(cat["executor_label"] or "Исполнитель"),
                CategoryFilterType.multi_select,
                20,
                _filter_opts(*cat["executors"]),
            ),
        ]
        if cat["objects"]:
            filters.append(
                _search_filter(
                    "service_object",
                    "Объект",
                    CategoryFilterType.multi_select,
                    30,
                    _filter_opts(*cat["objects"]),
                )
            )
        out[slug] = filters
    return out
