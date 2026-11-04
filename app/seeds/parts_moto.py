# -*- coding: utf-8 -*-
"""Mototechnika parts catalogs — per moto subtype.

API: moto (+ optional equipment_type = motorcycle, scooter, motoroller, …).
Keys match Flutter VehicleCatalogRepository / MotoTechnikaSubcategoriesData.
"""
from __future__ import annotations

from typing import Any

APPLICABILITY = "moto"

_Item = tuple[str, str] | tuple[str, str, list[tuple[str, str]]]
_Section = tuple[str, str, list[_Item]]


def _items(*pairs: _Item) -> list[_Item]:
    return list(pairs)


def _section(value: str, label: str, *pairs: _Item) -> _Section:
    return (value, label, _items(*pairs))


_ENGINE = _section(
    "engine",
    "Двигатель",
    ("engine_assembly", "Двигатель в сборе"),
    ("cylinder_piston", "ЦПГ / поршневая"),
    ("cylinder_head", "ГБЦ"),
    ("carburetor", "Карбюратор"),
    ("injection", "Инжектор / форсунки"),
    ("ignition", "Зажигание / CDI"),
    ("spark_plug", "Свеча"),
    ("air_filter", "Воздушный фильтр"),
    ("oil_filter", "Масляный фильтр"),
    ("gaskets_seals", "Прокладки и сальники"),
    ("other", "Другое"),
)

_COOLING = _section(
    "cooling",
    "Охлаждение",
    ("radiator", "Радиатор"),
    ("water_pump", "Помпа"),
    ("thermostat", "Термостат"),
    ("fan", "Вентилятор"),
    ("hoses", "Патрубки"),
    ("other", "Другое"),
)

_EXHAUST = _section(
    "exhaust",
    "Выхлопная система",
    ("exhaust_pipe", "Глушитель / банка"),
    ("header", "Коллектор"),
    ("catalyst", "Катализатор"),
    ("other", "Другое"),
)

_TRANSMISSION = _section(
    "transmission",
    "Трансмиссия",
    ("gearbox", "КПП"),
    ("clutch", "Сцепление"),
    ("drive_chain", "Цепь"),
    ("sprockets", "Звёзды"),
    ("belt_variator", "Ремень / вариатор"),
    ("cvt_rollers", "Ролики вариатора"),
    ("shaft_drive", "Кардан / редуктор"),
    ("other", "Другое"),
)

_BRAKES = _section(
    "brakes",
    "Тормоза",
    ("brake_pads", "Колодки"),
    ("brake_discs", "Диски"),
    ("brake_caliper", "Суппорт"),
    ("master_cylinder", "ГТЦ / машинка"),
    ("brake_hose", "Шланги"),
    ("other", "Другое"),
)

_SUSPENSION = _section(
    "suspension",
    "Подвеска",
    ("fork", "Вилка"),
    ("shock", "Амортизатор"),
    ("swingarm", "Маятник"),
    ("linkages", "Тяги / линк"),
    ("steering_stem", "Траверсы"),
    ("other", "Другое"),
)

_ELECTRICAL = _section(
    "electrical",
    "Электрика",
    ("battery", "Аккумулятор"),
    ("generator", "Генератор / статор"),
    ("starter", "Стартер"),
    ("wiring", "Проводка"),
    ("relays_fuses", "Реле / предохранители"),
    ("sensors", "Датчики"),
    ("switchgear", "Пульты / переключатели"),
    ("other", "Другое"),
)

_BODY = _section(
    "body",
    "Кузов и пластик",
    ("fairing", "Обтекатели / пластик"),
    ("tank", "Бензобак"),
    ("seat", "Сиденье"),
    ("mirrors", "Зеркала"),
    ("footpegs", "Подножки"),
    ("handlebars", "Руль"),
    ("levers", "Рычаги"),
    ("optics", "Оптика / фары"),
    ("other", "Другое"),
)

_FILTERS = _section(
    "filters_consumables",
    "Фильтры и расходники",
    ("oil", "Масло"),
    ("oil_filter_consumable", "Масляный фильтр"),
    ("air_filter_consumable", "Воздушный фильтр"),
    ("fuel_filter", "Топливный фильтр"),
    ("brake_fluid", "Тормозная жидкость"),
    ("other", "Другое"),
)

_OTHER = _section("other", "Другое", ("other", "Другое"))

_MOTORCYCLE_EXTRA = _section(
    "controls_frame",
    "Рама и органы управления",
    ("frame", "Рама"),
    ("subframe", "Подрамник"),
    ("kickstand", "Подножка"),
    ("cables", "Тросы"),
    ("other", "Другое"),
)

_SCOOTER_EXTRA = _section(
    "scooter_specific",
    "Скутерное оборудование",
    ("underseat_box", "Бардачок / кофр"),
    ("floorboard", "Пол / дека"),
    ("kickstand", "Подножка"),
    ("windshield", "Ветровое стекло"),
    ("other", "Другое"),
)

_MOTOROLLER_EXTRA = _section(
    "motoroller_equipment",
    "Оборудование для мотороллера",
    ("cargo_platform", "Грузовая площадка"),
    ("sideboards", "Борта"),
    ("trailer_hitch", "Фаркоп"),
    ("cabin", "Кабина / тент"),
    ("other", "Другое"),
)

_ATV_EXTRA = _section(
    "atv_equipment",
    "Оборудование квадроцикла",
    ("winch", "Лебёдка"),
    ("rack", "Багажник"),
    ("bumper", "Бампер / защита"),
    ("snorkel", "Шноркель"),
    ("other", "Другое"),
)

_BUGGY_EXTRA = _section(
    "buggy_equipment",
    "Оборудование багги",
    ("cage", "Каркас безопасности"),
    ("seat_harness", "Ремни / сиденья"),
    ("winch", "Лебёдка"),
    ("skid_plate", "Защита днища"),
    ("other", "Другое"),
)

_TRICYCLE_EXTRA = _section(
    "tricycle_body",
    "Кузов трицикла",
    ("cargo_box", "Кузов / будка"),
    ("cabin", "Кабина"),
    ("doors", "Двери"),
    ("other", "Другое"),
)

_SNOW_EXTRA = _section(
    "snowmobile_drive",
    "Ходовая снегохода",
    ("track", "Гусеница"),
    ("skis", "Лыжи"),
    ("tunnel", "Туннель"),
    ("drive_sprocket", "Ведущая звезда"),
    ("other", "Другое"),
)

_KART_EXTRA = _section(
    "kart_chassis",
    "Шасси карта",
    ("chassis", "Рама"),
    ("axle", "Ось"),
    ("seat", "Сиденье"),
    ("spoiler", "Спойлер"),
    ("other", "Другое"),
)


def _core(*extra: _Section) -> list[_Section]:
    return [
        _ENGINE,
        *extra,
        _TRANSMISSION,
        _BRAKES,
        _SUSPENSION,
        _ELECTRICAL,
        _EXHAUST,
        _COOLING,
        _BODY,
        _FILTERS,
        _OTHER,
    ]


TYPE_LABELS: dict[str, str] = {
    "motorcycle": "Мотоциклы",
    "scooter": "Скутеры и мопеды",
    "motoroller": "Мотороллеры муравей",
    "atv": "Квадроциклы",
    "buggy": "Багги",
    "tricycle": "Трициклы",
    "snowmobile": "Снегоходы",
    "kart": "Карты",
    "other_moto": "Другая мототехника",
}

TYPE_SECTIONS: dict[str, list[_Section]] = {
    "motorcycle": _core(_MOTORCYCLE_EXTRA),
    "scooter": _core(_SCOOTER_EXTRA),
    "motoroller": _core(_MOTOROLLER_EXTRA),
    "atv": _core(_ATV_EXTRA),
    "buggy": _core(_BUGGY_EXTRA),
    "tricycle": _core(_TRICYCLE_EXTRA),
    "snowmobile": _core(_SNOW_EXTRA),
    "kart": _core(_KART_EXTRA),
    "other_moto": _core(_MOTORCYCLE_EXTRA),
}

MOTO_SECTIONS: list[_Section] = TYPE_SECTIONS["other_moto"]

MOTO_PARTS_SEARCH_ALIASES: dict[str, tuple[str, str] | tuple[str, str, str]] = {
    "цепь": ("transmission", "drive_chain"),
    "вариатор": ("transmission", "belt_variator"),
    "колодки": ("brakes", "brake_pads"),
    "вилка": ("suspension", "fork"),
    "глушитель": ("exhaust", "exhaust_pipe"),
    "карбюратор": ("engine", "carburetor"),
    "цпг": ("engine", "cylinder_piston"),
    "гусеница": ("snowmobile_drive", "track"),
    "площадка": ("motoroller_equipment", "cargo_platform"),
}

LISTING_FIELDS: list[dict[str, Any]] = [
    {
        "field_key": "brand",
        "label": "Марка",
        "field_type": "brand",
        "is_required": True,
        "sort_order": 10,
    },
    {
        "field_key": "model",
        "label": "Модель",
        "field_type": "model",
        "is_required": True,
        "sort_order": 20,
    },
    {
        "field_key": "year",
        "label": "Год",
        "field_type": "year",
        "is_required": False,
        "sort_order": 30,
    },
    {
        "field_key": "condition",
        "label": "Состояние",
        "field_type": "enum",
        "is_required": True,
        "sort_order": 40,
        "options": {
            "values": [
                {"value": "new", "label": "Новое"},
                {"value": "used", "label": "Б/у"},
            ]
        },
    },
    {
        "field_key": "city",
        "label": "Город",
        "field_type": "city",
        "is_required": True,
        "sort_order": 50,
    },
]

PATH_FIELDS: tuple[str, ...] = (
    "vehicle_applicability",
    "part_section",
    "part_name",
    "part_subtype",
)


def _serialize_item(item: _Item) -> dict[str, Any]:
    if len(item) == 3:
        value, label, children = item  # type: ignore[misc]
        return {
            "value": value,
            "label": label,
            "children": [{"value": c[0], "label": c[1]} for c in children],
        }
    value, label = item  # type: ignore[misc]
    return {"value": value, "label": label}


def build_moto_catalog(*, equipment_type: str | None = None) -> dict[str, Any]:
    key = (equipment_type or "").strip().lower() or None
    if key and key not in TYPE_SECTIONS:
        key = None
    sections_src = TYPE_SECTIONS[key] if key else MOTO_SECTIONS
    label = TYPE_LABELS.get(key or "", "Мототехника")
    sections = [
        {
            "value": value,
            "label": section_label,
            "items": [_serialize_item(i) for i in items],
        }
        for value, section_label, items in sections_src
    ]
    return {
        "applicability": APPLICABILITY,
        "applicability_label": label,
        "category_slug": "transport-auto-parts",
        "sections": sections,
        "listing_fields": LISTING_FIELDS,
        "path_fields": list(PATH_FIELDS),
        "search_aliases": {
            k: {
                "part_section": v[0],
                "part_name": v[1],
                **({"part_subtype": v[2]} if len(v) == 3 else {}),
            }
            for k, v in MOTO_PARTS_SEARCH_ALIASES.items()
        },
    }
