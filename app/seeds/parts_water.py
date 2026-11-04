# -*- coding: utf-8 -*-
"""Watercraft parts — hull / propulsion / deck. No road chassis.

API: watercraft (+ equipment_type = boat, motorboat, yacht, jet_ski, other_watercraft).
"""
from __future__ import annotations

from typing import Any

APPLICABILITY = "watercraft"

_Item = tuple[str, str] | tuple[str, str, list[tuple[str, str]]]
_Section = tuple[str, str, list[_Item]]


def _section(value: str, label: str, *pairs: _Item) -> _Section:
    return (value, label, list(pairs))


_HULL = _section(
    "hull",
    "Корпус и палуба",
    ("hull", "Корпус"),
    ("deck", "Палуба"),
    ("transom", "Транец"),
    ("rub_rail", "Привальный брус"),
    ("other", "Другое"),
)

_PROPULSION = _section(
    "propulsion",
    "Двигатель и движитель",
    ("engine", "Двигатель / мотор"),
    ("gearbox", "Редуктор"),
    ("propeller", "Винт"),
    ("shaft", "Гребной вал"),
    ("outdrive", "Колонка / угловой привод"),
    ("other", "Другое"),
)

_JET = _section(
    "jet_drive",
    "Водомёт",
    ("impeller", "Импеллер"),
    ("wear_ring", "Кольцо износа"),
    ("intake", "Водозабор"),
    ("nozzle", "Сопло"),
    ("reverse_bucket", "Реверс-заслонка"),
    ("other", "Другое"),
)

_FUEL = _section(
    "fuel",
    "Топливная система",
    ("tank", "Бак"),
    ("pump", "Насос"),
    ("filter", "Фильтр"),
    ("hoses", "Шланги"),
    ("other", "Другое"),
)

_STEERING = _section(
    "helm",
    "Управление",
    ("wheel", "Штурвал"),
    ("cables", "Тросы"),
    ("hydraulic", "Гидравлика руля"),
    ("tiller", "Румпель"),
    ("other", "Другое"),
)

_ELECTRICAL = _section(
    "electrical",
    "Электрика",
    ("battery", "АКБ"),
    ("wiring", "Проводка"),
    ("lights", "Ходовые огни"),
    ("bilge_pump", "Помпа осушения"),
    ("other", "Другое"),
)

_DECK = _section(
    "deck_gear",
    "Палубное оборудование",
    ("seats", "Сиденья"),
    ("canopy", "Тент"),
    ("anchor", "Якорь"),
    ("cleats", "Утки / рымы"),
    ("other", "Другое"),
)

_CABIN = _section(
    "cabin",
    "Каюта и салон",
    ("berth", "Спальное место"),
    ("galley", "Камбуз"),
    ("head", "Гальюн"),
    ("windows", "Иллюминаторы"),
    ("other", "Другое"),
)

_BOAT_GEAR = _section(
    "boat_gear",
    "Комплектация лодки",
    ("oars", "Вёсла"),
    ("seats", "Банки / сиденья"),
    ("floor", "Пайол"),
    ("motor_mount", "Крепление мотора"),
    ("other", "Другое"),
)

_CONSUMABLES = _section(
    "consumables",
    "Расходники",
    ("oil", "Масло"),
    ("filters", "Фильтры"),
    ("impeller_pump", "Крыльчатка помпы"),
    ("anodes", "Аноды"),
    ("other", "Другое"),
)

_OTHER = _section("other", "Другое", ("other", "Другое"))

TYPE_LABELS: dict[str, str] = {
    "boat": "Лодки",
    "motorboat": "Катера",
    "yacht": "Яхты",
    "jet_ski": "Гидроциклы",
    "other_watercraft": "Другой водный транспорт",
}

TYPE_SECTIONS: dict[str, list[_Section]] = {
    "boat": [
        _HULL,
        _BOAT_GEAR,
        _PROPULSION,
        _FUEL,
        _ELECTRICAL,
        _DECK,
        _CONSUMABLES,
        _OTHER,
    ],
    "motorboat": [
        _HULL,
        _PROPULSION,
        _FUEL,
        _STEERING,
        _ELECTRICAL,
        _DECK,
        _CONSUMABLES,
        _OTHER,
    ],
    "yacht": [
        _HULL,
        _PROPULSION,
        _FUEL,
        _STEERING,
        _ELECTRICAL,
        _CABIN,
        _DECK,
        _CONSUMABLES,
        _OTHER,
    ],
    "jet_ski": [
        _HULL,
        _PROPULSION,
        _JET,
        _FUEL,
        _STEERING,
        _ELECTRICAL,
        _CONSUMABLES,
        _OTHER,
    ],
    "other_watercraft": [
        _HULL,
        _PROPULSION,
        _JET,
        _FUEL,
        _STEERING,
        _ELECTRICAL,
        _DECK,
        _CONSUMABLES,
        _OTHER,
    ],
}

WATER_SECTIONS: list[_Section] = TYPE_SECTIONS["motorboat"]

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


def build_water_catalog(*, equipment_type: str | None = None) -> dict[str, Any]:
    key = (equipment_type or "").strip().lower() or None
    if key and key not in TYPE_SECTIONS:
        key = None
    sections_src = TYPE_SECTIONS[key] if key else WATER_SECTIONS
    label = TYPE_LABELS.get(key or "", "Водный транспорт")
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
            "винт": {"part_section": "propulsion", "part_name": "propeller"},
            "импеллер": {"part_section": "jet_drive", "part_name": "impeller"},
            "штурвал": {"part_section": "helm", "part_name": "wheel"},
        },
    }
