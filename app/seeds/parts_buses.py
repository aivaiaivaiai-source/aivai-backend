# -*- coding: utf-8 -*-
"""Bus / microbus / motorhome parts catalogs — per subtype.

API: buses (+ optional equipment_type = bus, microbus, motorhome).
Keys match Flutter BusesMicrobusesMotorhomesSubcategoriesData.
"""
from __future__ import annotations

from typing import Any

APPLICABILITY = "buses"

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
    ("turbo", "Турбина"),
    ("injectors", "Форсунки"),
    ("fuel_pump", "ТНВД / топливный насос"),
    ("alternator", "Генератор"),
    ("starter", "Стартер"),
    ("radiator", "Радиатор"),
    ("other", "Другое"),
)

_TRANSMISSION = _section(
    "transmission",
    "КПП и трансмиссия",
    ("gearbox", "Коробка передач"),
    ("clutch", "Сцепление"),
    ("driveshaft", "Кардан"),
    ("differential", "Редуктор"),
    ("other", "Другое"),
)

_CHASSIS = _section(
    "chassis",
    "Ходовая и подвеска",
    ("shock_absorbers", "Амортизаторы"),
    ("springs", "Рессоры / пружины"),
    ("air_bags", "Пневмоподушки"),
    ("wheel_hub", "Ступица"),
    ("bearings", "Подшипники"),
    ("other", "Другое"),
)

_BRAKES = _section(
    "brakes",
    "Тормоза",
    ("brake_pads", "Колодки"),
    ("brake_discs", "Диски"),
    ("brake_drums", "Барабаны"),
    ("brake_chambers", "Тормозные камеры"),
    ("abs", "ABS / EBS"),
    ("other", "Другое"),
)

_STEERING = _section(
    "steering",
    "Рулевое",
    ("steering_gear", "Рулевой механизм"),
    ("power_steering", "ГУР"),
    ("tie_rods", "Тяги"),
    ("other", "Другое"),
)

_ELECTRICAL = _section(
    "electrical",
    "Электрика",
    ("battery", "АКБ"),
    ("wiring", "Проводка"),
    ("lights", "Фары / фонари"),
    ("dashboard", "Приборка"),
    ("other", "Другое"),
)

_BODY = _section(
    "body_cabin",
    "Кузов и кабина",
    ("doors", "Двери"),
    ("mirrors", "Зеркала"),
    ("glass", "Стёкла"),
    ("wipers", "Дворники"),
    ("bumpers", "Бамперы"),
    ("other", "Другое"),
)

_INTERIOR = _section(
    "interior",
    "Салон",
    ("seats", "Сиденья"),
    ("handrails", "Поручни"),
    ("flooring", "Пол / настил"),
    ("hvac", "Климат / отопитель"),
    ("other", "Другое"),
)

_CONSUMABLES = _section(
    "consumables",
    "Расходники",
    ("oil_filter", "Масляный фильтр"),
    ("air_filter", "Воздушный фильтр"),
    ("fuel_filter", "Топливный фильтр"),
    ("fluids", "Масла и жидкости"),
    ("belts", "Ремни"),
    ("other", "Другое"),
)

_OTHER = _section("other", "Другое", ("other", "Другое"))

_BUS_EXTRA = _section(
    "bus_equipment",
    "Оборудование автобуса",
    ("door_mechanism", "Механизм дверей"),
    ("destination_board", "Маршрутоуказатель"),
    ("validator_mount", "Крепление валидатора"),
    ("luggage_rack", "Багажные полки"),
    ("other", "Другое"),
)

_MICROBUS_EXTRA = _section(
    "microbus_equipment",
    "Оборудование микроавтобуса",
    ("sliding_door", "Сдвижная дверь"),
    ("step", "Подножка"),
    ("partition", "Перегородка кабины"),
    ("roof_hatch", "Люк"),
    ("other", "Другое"),
)

_MOTORHOME_EXTRA = _section(
    "motorhome_equipment",
    "Оборудование автодома",
    ("camper_kitchen", "Кухня / мойка"),
    ("camper_bed", "Спальное место"),
    ("fresh_water", "Бак чистой воды"),
    ("waste_water", "Бак стоков"),
    ("gas_system", "Газовая система"),
    ("awning", "Маркиза"),
    ("solar", "Солнечная панель"),
    ("other", "Другое"),
)


def _core(*extra: _Section) -> list[_Section]:
    return [
        _ENGINE,
        _TRANSMISSION,
        *extra,
        _CHASSIS,
        _BRAKES,
        _STEERING,
        _ELECTRICAL,
        _BODY,
        _INTERIOR,
        _CONSUMABLES,
        _OTHER,
    ]


TYPE_LABELS: dict[str, str] = {
    "bus": "Автобусы",
    "microbus": "Микроавтобусы",
    "motorhome": "Автодома",
}

TYPE_SECTIONS: dict[str, list[_Section]] = {
    "bus": _core(_BUS_EXTRA),
    "microbus": _core(_MICROBUS_EXTRA),
    "motorhome": _core(_MOTORHOME_EXTRA),
}

BUS_SECTIONS: list[_Section] = TYPE_SECTIONS["bus"]

BUS_PARTS_SEARCH_ALIASES: dict[str, tuple[str, str] | tuple[str, str, str]] = {
    "колодки": ("brakes", "brake_pads"),
    "сиденья": ("interior", "seats"),
    "двери": ("body_cabin", "doors"),
    "форсунки": ("engine", "injectors"),
    "акб": ("electrical", "battery"),
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
        "is_required": True,
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


def build_buses_catalog(*, equipment_type: str | None = None) -> dict[str, Any]:
    key = (equipment_type or "").strip().lower() or None
    if key and key not in TYPE_SECTIONS:
        key = None
    sections_src = TYPE_SECTIONS[key] if key else BUS_SECTIONS
    label = TYPE_LABELS.get(key or "", "Автобусы")
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
            for k, v in BUS_PARTS_SEARCH_ALIASES.items()
        },
    }
