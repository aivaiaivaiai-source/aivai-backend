# -*- coding: utf-8 -*-
"""Electric transport parts catalogs — per subtype.

API: electric (+ optional equipment_type = e_scooter, e_moped, …).
Keys match Flutter ElectricTransportSubcategoriesData.
"""
from __future__ import annotations

from typing import Any

APPLICABILITY = "electric"

_Item = tuple[str, str] | tuple[str, str, list[tuple[str, str]]]
_Section = tuple[str, str, list[_Item]]


def _items(*pairs: _Item) -> list[_Item]:
    return list(pairs)


def _section(value: str, label: str, *pairs: _Item) -> _Section:
    return (value, label, _items(*pairs))


_BATTERY = _section(
    "battery",
    "Аккумулятор и зарядка",
    ("battery_pack", "АКБ / батарея"),
    ("cells", "Ячейки"),
    ("bms", "BMS"),
    ("charger", "Зарядное устройство"),
    ("charge_port", "Разъём зарядки"),
    ("other", "Другое"),
)

_MOTOR = _section(
    "motor_controller",
    "Мотор и контроллер",
    ("hub_motor", "Мотор-колесо"),
    ("mid_drive", "Центральный мотор"),
    ("controller", "Контроллер"),
    ("throttle", "Ручка газа / курок"),
    ("hall_sensors", "Датчики Холла"),
    ("other", "Другое"),
)

_BRAKES = _section(
    "brakes",
    "Тормоза",
    ("brake_pads", "Колодки"),
    ("brake_discs", "Диски"),
    ("brake_caliper", "Суппорт"),
    ("brake_lever", "Рычаг тормоза"),
    ("ebrake_sensor", "Датчик тормоза"),
    ("other", "Другое"),
)

_WHEELS = _section(
    "wheel_bearings",
    "Подшипники колёс",
    ("bearing", "Подшипники"),
    ("other", "Другое"),
)

_SUSPENSION = _section(
    "suspension",
    "Подвеска",
    ("fork", "Вилка"),
    ("shock", "Амортизатор"),
    ("deck", "Дека / платформа"),
    ("other", "Другое"),
)

_ELECTRICAL = _section(
    "electrical",
    "Электрика и дисплей",
    ("display", "Дисплей / приборка"),
    ("wiring", "Проводка"),
    ("lights", "Фары / подсветка"),
    ("horn", "Сигнал"),
    ("other", "Другое"),
)

_BODY = _section(
    "body",
    "Корпус и пластик",
    ("body_shell", "Корпус"),
    ("fenders", "Крылья"),
    ("stand", "Подножка"),
    ("handlebar", "Руль"),
    ("grips", "Грипсы"),
    ("seat", "Сиденье"),
    ("other", "Другое"),
)

_FILTERS = _section(
    "consumables",
    "Расходники",
    ("grease", "Смазка"),
    ("bolts", "Крепёж"),
    ("other", "Другое"),
)

_OTHER = _section("other", "Другое", ("other", "Другое"))

_ESCOOTER_EXTRA = _section(
    "escooter_equipment",
    "Оборудование электросамоката",
    ("folding_mechanism", "Складной механизм"),
    ("stem", "Стойка руля"),
    ("kickstand", "Подножка"),
    ("other", "Другое"),
)

_EMOPED_EXTRA = _section(
    "emoped_equipment",
    "Оборудование электроскутера",
    ("underseat_box", "Бардачок"),
    ("floorboard", "Пол / дека"),
    ("windshield", "Ветровое стекло"),
    ("luggage_rack", "Багажник"),
    ("other", "Другое"),
)

_HOVER_EXTRA = _section(
    "hoverboard_equipment",
    "Оборудование гироскутера",
    ("gyro_sensor", "Гироскоп / сенсоры"),
    ("footpad", "Площадки ног"),
    ("shell", "Корпус"),
    ("other", "Другое"),
)

_MONO_EXTRA = _section(
    "monowheel_equipment",
    "Оборудование моноколеса",
    ("pedals", "Педали"),
    ("pads", "Пады"),
    ("trolley", "Тележка / ручка"),
    ("other", "Другое"),
)

_SEGWAY_EXTRA = _section(
    "segway_equipment",
    "Оборудование сигвея",
    ("knee_bar", "Упор / ручка"),
    ("platform", "Платформа"),
    ("other", "Другое"),
)

_GOLF_EXTRA = _section(
    "golf_cart_equipment",
    "Оборудование гольфкара",
    ("seats", "Сиденья"),
    ("roof", "Крыша"),
    ("windshield", "Лобовое стекло"),
    ("cargo_box", "Кузов / багажник"),
    ("other", "Другое"),
)


def _core(*extra: _Section) -> list[_Section]:
    return [
        _BATTERY,
        _MOTOR,
        *extra,
        _BRAKES,
        _WHEELS,
        _SUSPENSION,
        _ELECTRICAL,
        _BODY,
        _FILTERS,
        _OTHER,
    ]


def _micro(*extra: _Section) -> list[_Section]:
    """Balance boards / wheels: no fork, discs, or road chassis."""
    return [
        _BATTERY,
        _MOTOR,
        *extra,
        _WHEELS,
        _ELECTRICAL,
        _BODY,
        _FILTERS,
        _OTHER,
    ]


TYPE_LABELS: dict[str, str] = {
    "e_scooter": "Электросамокаты",
    "e_moped": "Электроскутеры",
    "hoverboard": "Гироскутеры",
    "monowheel": "Моноколёса",
    "segway": "Сигвеи",
    "golf_cart": "Гольфкары и электрические мини-мобили",
    "other_electric": "Другой электротранспорт",
}

TYPE_SECTIONS: dict[str, list[_Section]] = {
    "e_scooter": _core(_ESCOOTER_EXTRA),
    "e_moped": _core(_EMOPED_EXTRA),
    "hoverboard": _micro(_HOVER_EXTRA),
    "monowheel": _micro(_MONO_EXTRA),
    "segway": _micro(_SEGWAY_EXTRA),
    "golf_cart": _core(_GOLF_EXTRA),
    "other_electric": _core(_ESCOOTER_EXTRA),
}

ELECTRIC_SECTIONS: list[_Section] = TYPE_SECTIONS["other_electric"]

ELECTRIC_PARTS_SEARCH_ALIASES: dict[str, tuple[str, str] | tuple[str, str, str]] = {
    "акб": ("battery", "battery_pack"),
    "батарея": ("battery", "battery_pack"),
    "зарядка": ("battery", "charger"),
    "контроллер": ("motor_controller", "controller"),
    "мотор": ("motor_controller", "hub_motor"),
    "колодки": ("brakes", "brake_pads"),
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


def build_electric_catalog(*, equipment_type: str | None = None) -> dict[str, Any]:
    key = (equipment_type or "").strip().lower() or None
    if key and key not in TYPE_SECTIONS:
        key = None
    sections_src = TYPE_SECTIONS[key] if key else ELECTRIC_SECTIONS
    label = TYPE_LABELS.get(key or "", "Электротранспорт")
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
            for k, v in ELECTRIC_PARTS_SEARCH_ALIASES.items()
        },
    }
