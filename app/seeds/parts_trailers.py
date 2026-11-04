# -*- coding: utf-8 -*-
"""Trailer parts — axles, hitch, brakes, body. No engine or steering.

API: trailers (+ equipment_type = drawbar_trailer, semi_trailer, camper_trailer).
"""
from __future__ import annotations

from typing import Any

APPLICABILITY = "trailers"

_Item = tuple[str, str]
_Section = tuple[str, str, list[_Item]]


def _section(value: str, label: str, *pairs: _Item) -> _Section:
    return (value, label, list(pairs))


_HITCH = _section(
    "hitch",
    "Сцепка",
    ("coupler", "Сцепная головка / фаркоп"),
    ("drawbar", "Дышло"),
    ("kingpin", "Шкворень"),
    ("safety_chains", "Страховочные тросы"),
    ("jack", "Опорная стойка / домкрат"),
    ("other", "Другое"),
)

_AXLES = _section(
    "axles",
    "Оси и подвеска",
    ("axle", "Ось"),
    ("hub", "Ступица"),
    ("bearings", "Подшипники"),
    ("springs", "Рессоры"),
    ("shock", "Амортизатор"),
    ("other", "Другое"),
)

_BRAKES = _section(
    "brakes",
    "Тормоза",
    ("brake_pads", "Колодки"),
    ("brake_drums", "Барабаны"),
    ("overrun", "Накатной тормоз"),
    ("brake_cables", "Тросы"),
    ("air_chambers", "Тормозные камеры"),
    ("other", "Другое"),
)

_ELECTRICAL = _section(
    "electrical",
    "Электрика",
    ("plug", "Вилка / розетка"),
    ("lights", "Фонари"),
    ("wiring", "Проводка"),
    ("other", "Другое"),
)

_BODY = _section(
    "body",
    "Кузов",
    ("frame", "Рама"),
    ("boards", "Борта"),
    ("floor", "Пол"),
    ("tent", "Тент"),
    ("tailgate", "Задний борт"),
    ("other", "Другое"),
)

_REEFER = _section(
    "cargo_gear",
    "Надстройка",
    ("refrigeration", "Холодильная установка"),
    ("tarp", "Тент / каркас"),
    ("ramps", "Трапы"),
    ("other", "Другое"),
)

_CAMPER = _section(
    "camper",
    "Жилой модуль",
    ("furniture", "Мебель"),
    ("kitchen", "Кухня"),
    ("fresh_water", "Бак воды"),
    ("waste", "Бак стоков"),
    ("gas", "Газовая система"),
    ("awning", "Маркиза"),
    ("other", "Другое"),
)

_CONSUMABLES = _section(
    "consumables",
    "Расходники",
    ("grease", "Смазка ступиц"),
    ("bearings_kit", "Ремкомплект подшипников"),
    ("other", "Другое"),
)

_OTHER = _section("other", "Другое", ("other", "Другое"))

TYPE_LABELS: dict[str, str] = {
    "drawbar_trailer": "Прицепы",
    "semi_trailer": "Полуприцепы",
    "camper_trailer": "Жилые прицепы / кемперы",
}

TYPE_SECTIONS: dict[str, list[_Section]] = {
    "drawbar_trailer": [
        _HITCH,
        _AXLES,
        _BRAKES,
        _ELECTRICAL,
        _BODY,
        _CONSUMABLES,
        _OTHER,
    ],
    "semi_trailer": [
        _HITCH,
        _AXLES,
        _BRAKES,
        _ELECTRICAL,
        _BODY,
        _REEFER,
        _CONSUMABLES,
        _OTHER,
    ],
    "camper_trailer": [
        _HITCH,
        _AXLES,
        _BRAKES,
        _ELECTRICAL,
        _BODY,
        _CAMPER,
        _CONSUMABLES,
        _OTHER,
    ],
}

TRAILER_SECTIONS: list[_Section] = TYPE_SECTIONS["drawbar_trailer"]

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


def build_trailers_catalog(*, equipment_type: str | None = None) -> dict[str, Any]:
    key = (equipment_type or "").strip().lower() or None
    if key and key not in TYPE_SECTIONS:
        key = None
    sections_src = TYPE_SECTIONS[key] if key else TRAILER_SECTIONS
    label = TYPE_LABELS.get(key or "", "Прицепы")
    sections = [
        {
            "value": value,
            "label": section_label,
            "items": [{"value": a, "label": b} for a, b in items],
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
            "ось": {"part_section": "axles", "part_name": "axle"},
            "ступица": {"part_section": "axles", "part_name": "hub"},
            "шкворень": {"part_section": "hitch", "part_name": "kingpin"},
        },
    }
