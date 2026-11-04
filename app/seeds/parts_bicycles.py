# -*- coding: utf-8 -*-
"""Bicycle parts catalogs — per subtype.

API: bicycles (+ optional equipment_type = mountain_bike, city_bike, …).
Keys match Flutter BicyclesSubcategoriesData.
"""
from __future__ import annotations

from typing import Any

APPLICABILITY = "bicycles"

_Item = tuple[str, str] | tuple[str, str, list[tuple[str, str]]]
_Section = tuple[str, str, list[_Item]]


def _items(*pairs: _Item) -> list[_Item]:
    return list(pairs)


def _section(value: str, label: str, *pairs: _Item) -> _Section:
    return (value, label, _items(*pairs))


_FRAME = _section(
    "frame_fork",
    "Рама и вилка",
    ("frame", "Рама"),
    ("fork", "Вилка"),
    ("headset", "Рулевая колонка"),
    ("seatpost", "Подседельный штырь"),
    ("saddle", "Седло"),
    ("other", "Другое"),
)

_DRIVETRAIN = _section(
    "drivetrain",
    "Трансмиссия",
    ("chain", "Цепь"),
    ("cassette", "Кассета / трещотка"),
    ("chainring", "Звёзды / система"),
    ("crankset", "Шатуны"),
    ("bottom_bracket", "Каретка"),
    ("derailleur_front", "Передний переключатель"),
    ("derailleur_rear", "Задний переключатель"),
    ("shifter", "Манетки"),
    ("pedals", "Педали"),
    ("other", "Другое"),
)

_BRAKES = _section(
    "brakes",
    "Тормоза",
    ("brake_pads", "Колодки"),
    ("brake_discs", "Диски"),
    ("brake_caliper", "Суппорт / машинка"),
    ("brake_lever", "Ручки тормоза"),
    ("brake_cable", "Тросики / рубашки"),
    ("brake_hose", "Гидролиния"),
    ("other", "Другое"),
)

_WHEELS = _section(
    "hubs_spokes",
    "Втулки и спицы",
    ("hub", "Втулка"),
    ("spokes", "Спицы"),
    ("other", "Другое"),
)

_CONTROLS = _section(
    "controls",
    "Руль и управление",
    ("handlebar", "Руль"),
    ("stem", "Вынос"),
    ("grips", "Грипсы / обмотка"),
    ("bar_ends", "Рога"),
    ("other", "Другое"),
)

_ELECTRICAL = _section(
    "electrical",
    "Электрика и свет",
    ("lights", "Фары / фонари"),
    ("dynamo", "Динамо"),
    ("computer", "Велокомпьютер"),
    ("wiring", "Проводка"),
    ("other", "Другое"),
)

_CONSUMABLES = _section(
    "consumables",
    "Расходники",
    ("lube", "Смазка"),
    ("bolts", "Крепёж"),
    ("cable_kit", "Тросики / рубашки"),
    ("other", "Другое"),
)

_OTHER = _section("other", "Другое", ("other", "Другое"))

_EBIKE_EXTRA = _section(
    "ebike_equipment",
    "Оборудование электровелосипеда",
    ("battery_pack", "АКБ / батарея"),
    ("charger", "Зарядное устройство"),
    ("controller", "Контроллер"),
    ("hub_motor", "Мотор-колесо"),
    ("mid_drive", "Центральный мотор"),
    ("display", "Дисплей / панель"),
    ("throttle", "Ручка газа"),
    ("pas_sensor", "Датчик PAS"),
    ("other", "Другое"),
)

_MTB_EXTRA = _section(
    "mtb_equipment",
    "Оборудование горного велосипеда",
    ("rear_shock", "Задний амортизатор"),
    ("dropper", "Дроппер"),
    ("tubeless_kit", "Бескамерный набор"),
    ("other", "Другое"),
)

_ROAD_EXTRA = _section(
    "road_equipment",
    "Оборудование шоссейного велосипеда",
    ("aero_bars", "Лежаки"),
    ("clipless_pedals", "Контактные педали"),
    ("tubular", "Трубки"),
    ("other", "Другое"),
)

_BMX_EXTRA = _section(
    "bmx_equipment",
    "Оборудование BMX",
    ("pegs", "Пеги"),
    ("gyro", "Гироротор"),
    ("freestyle_seat", "Седло freestyle"),
    ("other", "Другое"),
)

def _core(*extra: _Section) -> list[_Section]:
    return [
        _FRAME,
        _DRIVETRAIN,
        *extra,
        _BRAKES,
        _WHEELS,
        _CONTROLS,
        _ELECTRICAL,
        _CONSUMABLES,
        _OTHER,
    ]


TYPE_LABELS: dict[str, str] = {
    "mountain_bike": "Горные",
    "city_bike": "Городские",
    "road_bike": "Шоссейные",
    "teen_bike": "Подростковые",
    "e_bike": "Электровелосипеды",
    "bmx": "BMX",
    "other_bicycle": "Другие велосипеды",
}

TYPE_SECTIONS: dict[str, list[_Section]] = {
    "mountain_bike": _core(_MTB_EXTRA),
    "city_bike": _core(),
    "road_bike": _core(_ROAD_EXTRA),
    "teen_bike": _core(),
    "e_bike": _core(_EBIKE_EXTRA),
    "bmx": _core(_BMX_EXTRA),
    "other_bicycle": _core(),
}

BICYCLE_SECTIONS: list[_Section] = TYPE_SECTIONS["other_bicycle"]

BICYCLE_PARTS_SEARCH_ALIASES: dict[str, tuple[str, str] | tuple[str, str, str]] = {
    "цепь": ("drivetrain", "chain"),
    "кассета": ("drivetrain", "cassette"),
    "колодки": ("brakes", "brake_pads"),
    "вилка": ("frame_fork", "fork"),
    "акб": ("ebike_equipment", "battery_pack"),
    "контроллер": ("ebike_equipment", "controller"),
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


def build_bicycles_catalog(*, equipment_type: str | None = None) -> dict[str, Any]:
    key = (equipment_type or "").strip().lower() or None
    if key and key not in TYPE_SECTIONS:
        key = None
    sections_src = TYPE_SECTIONS[key] if key else BICYCLE_SECTIONS
    label = TYPE_LABELS.get(key or "", "Велосипеды")
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
            for k, v in BICYCLE_PARTS_SEARCH_ALIASES.items()
        },
    }
