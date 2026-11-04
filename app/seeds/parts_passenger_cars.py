# -*- coding: utf-8 -*-
"""Passenger-car parts catalog (Parts Step 2) — API Source of Truth.

Controlled dictionary of sections → items (optional children). Not a fork of
the category tree. Other applicability types keep legacy UX.
"""
from __future__ import annotations

from typing import Any

APPLICABILITY = "passenger_cars"

# (value, label, items) where item is (value, label) or (value, label, children)
_Item = tuple[str, str] | tuple[str, str, list[tuple[str, str]]]


def _items(*pairs: _Item) -> list[_Item]:
    return list(pairs)


PASSENGER_CAR_SECTIONS: list[tuple[str, str, list[_Item]]] = [
    (
        "engine",
        "Двигатель",
        _items(
            ("engine_assembly", "Двигатель в сборе"),
            ("engine_block", "Блок двигателя"),
            ("cylinder_head", "ГБЦ"),
            ("valve_cover", "Клапанная крышка"),
            ("crankshaft", "Коленвал"),
            ("camshaft", "Распредвал"),
            ("pistons", "Поршни"),
            ("connecting_rods", "Шатуны"),
            ("valves", "Клапаны"),
            ("timing", "ГРМ"),
            ("turbo", "Турбина"),
            ("intake_manifold", "Впускной коллектор"),
            ("throttle", "Дроссель"),
            ("intercooler", "Интеркулер"),
            ("oil_pump", "Масляный насос"),
            ("oil_pan", "Поддон двигателя"),
            # Starter/Generator live under Electrical (Auto Parts V2).
            ("engine_mounts", "Подушки двигателя"),
            ("gaskets", "Прокладки"),
            ("seals", "Сальники"),
            ("other", "Другое"),
        ),
    ),
    (
        "transmission",
        "Коробка передач и трансмиссия",
        _items(
            ("gearbox", "Коробка передач"),
            ("clutch", "Сцепление"),
            ("flywheel", "Маховик"),
            ("torque_converter", "Гидротрансформатор"),
            ("transfer_case", "Раздатка"),
            ("differential", "Редуктор"),
            ("driveshaft", "Кардан"),
            ("axle_shaft", "Полуось"),
            ("drive", "Привод"),
            ("cv_joint", "ШРУС"),
            ("other", "Другое"),
        ),
    ),
    (
        "chassis",
        "Ходовая и подвеска",
        _items(
            ("shock_absorbers", "Амортизаторы"),
            ("struts", "Стойки"),
            ("springs", "Пружины"),
            ("leaf_springs", "Рессоры"),
            ("control_arms", "Рычаги"),
            ("ball_joints", "Шаровые"),
            ("silent_blocks", "Сайлентблоки"),
            ("hubs", "Ступицы"),
            ("bearings", "Подшипники"),
            ("stabilizers", "Стабилизаторы"),
            ("bushings", "Втулки"),
            ("air_suspension", "Пневмоподвеска"),
            ("other", "Другое"),
        ),
    ),
    (
        "steering",
        "Рулевое управление",
        _items(
            ("steering_rack", "Рулевая рейка"),
            ("steering_column", "Рулевая колонка"),
            ("steering_shaft", "Рулевой вал"),
            ("tie_rods", "Рулевые тяги"),
            ("tie_rod_ends", "Рулевые наконечники"),
            ("power_steering_pump", "Насос ГУР"),
            ("electric_power_steering", "Электроусилитель руля"),
            ("other", "Другое"),
        ),
    ),
    (
        "brakes",
        "Тормозная система",
        _items(
            ("brake_pads", "Тормозные колодки"),
            ("brake_discs", "Тормозные диски"),
            ("brake_drums", "Тормозные барабаны"),
            ("calipers", "Суппорты"),
            ("brake_cylinders", "Тормозные цилиндры"),
            ("brake_hoses", "Тормозные шланги"),
            ("brake_lines", "Тормозные трубки"),
            ("handbrake", "Ручной тормоз"),
            ("abs", "ABS"),
            ("other", "Другое"),
        ),
    ),
    (
        "body",
        "Кузов и наружные детали",
        _items(
            ("bumpers", "Бамперы"),
            ("doors", "Двери"),
            ("hoods", "Капоты"),
            ("trunk_lids", "Крышки багажника"),
            ("fenders", "Крылья"),
            ("mirrors", "Зеркала"),
            ("glass", "Стёкла"),
            (
                "optics",
                "Оптика, фары и фонари",
                [
                    ("headlights", "Фары"),
                    ("tail_lights", "Задние фонари"),
                    ("fog_lights", "Противотуманные фары"),
                    ("turn_signals", "Поворотники"),
                    ("bulbs", "Лампы"),
                    ("lenses", "Линзы"),
                    ("other", "Другое"),
                ],
            ),
            ("grilles", "Решётки"),
            ("inner_fenders", "Подкрылки"),
            ("underbody_protection", "Защита днища"),
            ("sills", "Пороги"),
            ("cabin_nose_cut", "Кабина / ноускат"),
            ("body_elements", "Кузовные элементы"),
            ("other", "Другое"),
        ),
    ),
    (
        "interior",
        "Салон",
        _items(
            ("seats", "Сиденья"),
            ("steering_wheel", "Руль"),
            ("dashboard", "Торпедо / панель"),
            ("center_console", "Центральная консоль"),
            ("door_trims", "Обшивки дверей"),
            ("headliner", "Потолок"),
            ("seat_belts", "Ремни безопасности"),
            ("armrests", "Подлокотники"),
            ("interior_mirror", "Зеркало салона"),
            ("window_regulators", "Стеклоподъёмники"),
            ("interior_handles_buttons", "Ручки и кнопки салона"),
            ("other", "Другое"),
        ),
    ),
    (
        "electrical",
        "Электрика и электроника",
        _items(
            ("battery", "Аккумулятор"),
            ("wiring", "Проводка"),
            ("fuses", "Предохранители"),
            ("relays", "Реле"),
            ("ecu", "Блоки управления"),
            ("instrument_cluster", "Приборная панель"),
            ("ignition_lock", "Замок зажигания"),
            ("ignition_coils", "Катушки зажигания"),
            ("spark_plugs", "Свечи зажигания"),
            ("sensors", "Датчики"),
            ("other", "Другое"),
        ),
    ),
    (
        "climate",
        "Печка и кондиционер",
        _items(
            ("ac_compressor", "Компрессор кондиционера"),
            ("heater_radiator", "Радиатор печки"),
            ("heater_motor", "Моторчик печки"),
            ("climate_ac", "Климат / кондиционер"),
            ("evaporator", "Испаритель"),
            ("ac_condenser", "Конденсор кондиционера"),
            ("ac_lines", "Трубки кондиционера"),
            ("heater", "Печка"),
            ("other", "Другое"),
        ),
    ),
    (
        "cooling",
        "Система охлаждения",
        _items(
            ("radiator", "Радиатор"),
            ("water_pump", "Помпа"),
            ("thermostat", "Термостат"),
            ("fan", "Вентилятор"),
            ("expansion_tank", "Расширительный бачок"),
            ("hoses", "Патрубки"),
            ("other", "Другое"),
        ),
    ),
    (
        "fuel",
        "Топливная система",
        _items(
            ("fuel_tank", "Топливный бак"),
            ("fuel_pump", "Топливный насос"),
            ("injection_pump", "ТНВД"),
            ("injectors", "Форсунки"),
            ("fuel_rail", "Топливная рампа"),
            # Fuel filter lives under Consumables/filters (Auto Parts V2).
            ("fuel_lines", "Топливные трубки"),
            (
                "lpg",
                "ГБО",
                [
                    ("lpg_tank", "Баллон"),
                    ("lpg_reducer", "Редуктор"),
                    ("lpg_injectors", "Форсунки ГБО"),
                    ("lpg_ecu", "Блок управления ГБО"),
                    ("lpg_filler", "Заправочное устройство"),
                    ("lpg_lines", "Магистраль"),
                    ("other", "Другое"),
                ],
            ),
            ("other", "Другое"),
        ),
    ),
    (
        "exhaust",
        "Выхлопная система",
        _items(
            ("muffler", "Глушитель"),
            ("resonator", "Резонатор"),
            ("exhaust_manifold", "Выпускной коллектор"),
            ("catalytic_converter", "Катализатор"),
            ("dpf", "Сажевый фильтр"),
            ("flex_pipe", "Гофра"),
            ("exhaust_pipes", "Выхлопные трубы"),
            ("other", "Другое"),
        ),
    ),
    (
        "filters",
        "Фильтры",
        _items(
            ("oil_filter", "Масляный фильтр"),
            ("air_filter", "Воздушный фильтр"),
            ("cabin_filter", "Салонный фильтр"),
            ("fuel_filter_item", "Топливный фильтр"),
            ("other", "Другое"),
        ),
    ),
    (
        "hoses",
        "Трубки, патрубки и шланги",
        _items(
            ("coolant_hoses", "Патрубки охлаждения"),
            ("brake_hoses_item", "Тормозные шланги"),
            ("fuel_hoses", "Топливные шланги"),
            ("ac_hoses", "Шланги кондиционера"),
            ("vacuum_hoses", "Вакуумные шланги"),
            ("other", "Другое"),
        ),
    ),
    (
        "other",
        "Другое",
        _items(("other", "Другое")),
    ),
]

# Search / alias normalization → (section_value, item_value[, child_value])
PASSENGER_PARTS_SEARCH_ALIASES: dict[str, tuple[str, str] | tuple[str, str, str]] = {
    "передние колодки": ("brakes", "brake_pads"),
    "задние колодки": ("brakes", "brake_pads"),
    "тормозные колодки": ("brakes", "brake_pads"),
    "колодки": ("brakes", "brake_pads"),
    "спортивные колодки": ("brakes", "brake_pads"),
    "комплект колодок": ("brakes", "brake_pads"),
    "армированный тормозной шланг": ("brakes", "brake_hoses"),
    "тормозной шланг": ("brakes", "brake_hoses"),
    "led фара": ("body", "optics", "headlights"),
    "фара": ("body", "optics", "headlights"),
    "фары": ("body", "optics", "headlights"),
    "спортивный глушитель": ("exhaust", "muffler"),
    "глушитель": ("exhaust", "muffler"),
    "масляный фильтр": ("filters", "oil_filter"),
    "воздушный фильтр": ("filters", "air_filter"),
    "гбо": ("fuel", "lpg"),
    "подшипник": ("chassis", "bearings"),
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

# Path fields already chosen before listing fields — not re-prompted in UX.
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
            "children": [
                {"value": c[0], "label": c[1]} for c in children
            ],
        }
    value, label = item  # type: ignore[misc]
    return {"value": value, "label": label}


def build_passenger_cars_catalog() -> dict[str, Any]:
    sections = []
    for value, label, items in PASSENGER_CAR_SECTIONS:
        sections.append(
            {
                "value": value,
                "label": label,
                "items": [_serialize_item(i) for i in items],
            }
        )
    return {
        "applicability": APPLICABILITY,
        "applicability_label": "Легковые автомобили",
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
            for k, v in PASSENGER_PARTS_SEARCH_ALIASES.items()
        },
    }


def resolve_passenger_parts_alias(text: str) -> dict[str, str] | None:
    key = " ".join(text.strip().lower().split())
    hit = PASSENGER_PARTS_SEARCH_ALIASES.get(key)
    if not hit:
        return None
    out = {"part_section": hit[0], "part_name": hit[1]}
    if len(hit) == 3:
        out["part_subtype"] = hit[2]
    return out
