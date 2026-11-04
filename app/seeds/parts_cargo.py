# -*- coding: utf-8 -*-
"""Cargo-truck parts catalog (Parts Step 3) — API Source of Truth.

Same UX architecture as passenger_cars. Shared systems reuse the same simple
item names; cargo-specific sections: cabin_body, cargo_area.
"""
from __future__ import annotations

from typing import Any

APPLICABILITY = "cargo"

_Item = tuple[str, str] | tuple[str, str, list[tuple[str, str]]]


def _items(*pairs: _Item) -> list[_Item]:
    return list(pairs)


_OPTICS_CHILDREN: list[tuple[str, str]] = [
    ("headlights", "Фары"),
    ("tail_lights", "Задние фонари"),
    ("fog_lights", "Противотуманные фары"),
    ("turn_signals", "Поворотники"),
    ("bulbs", "Лампы"),
    ("lenses", "Линзы"),
    ("other", "Другое"),
]

CARGO_SECTIONS: list[tuple[str, str, list[_Item]]] = [
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
            ("alternator", "Генератор"),
            ("starter", "Стартер"),
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
            ("steering_gearbox", "Рулевой редуктор"),
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
        "cabin_body",
        "Кабина и кузов",
        _items(
            ("cabin", "Кабина"),
            ("doors", "Двери"),
            ("hood", "Капот"),
            ("bumpers", "Бамперы"),
            ("fenders", "Крылья"),
            ("mirrors", "Зеркала"),
            ("glass", "Стёкла"),
            ("optics", "Оптика, фары и фонари", _OPTICS_CHILDREN),
            ("grilles", "Решётки"),
            ("steps", "Подножки"),
            ("body_elements", "Кузовные элементы"),
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
            ("fuel_filter", "Топливный фильтр"),
            ("fuel_lines", "Топливные трубки"),
            (
                "lpg",
                "ГБО",
                [
                    ("lpg_tank", "Баллон"),
                    ("lpg_reducer", "Редуктор"),
                    ("lpg_injectors", "Форсунки ГБО"),
                    ("lpg_ecu", "Блок управления ГБО"),
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
        "cargo_area",
        "Грузовая часть",
        _items(
            ("cargo_body", "Кузов"),
            ("side_boards", "Борта"),
            ("awning", "Тент"),
            ("box_van", "Будка / фургон"),
            ("tail_lift", "Гидроборт"),
            ("dump_lift", "Механизм подъёма кузова"),
            ("fasteners", "Крепления"),
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
            ("air_lines", "Воздушные магистрали"),
            ("other", "Другое"),
        ),
    ),
    (
        "other",
        "Другое",
        _items(("other", "Другое")),
    ),
]

CARGO_PARTS_SEARCH_ALIASES: dict[str, tuple[str, str] | tuple[str, str, str]] = {
    "передние колодки": ("brakes", "brake_pads"),
    "задние колодки": ("brakes", "brake_pads"),
    "тормозные колодки": ("brakes", "brake_pads"),
    "колодки": ("brakes", "brake_pads"),
    "рулевой редуктор": ("steering", "steering_gearbox"),
    "гидроборт": ("cargo_area", "tail_lift"),
    "тент": ("cargo_area", "awning"),
    "led фара": ("cabin_body", "optics", "headlights"),
    "фара": ("cabin_body", "optics", "headlights"),
    "фары": ("cabin_body", "optics", "headlights"),
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


_DUMP_EXTRA: list[_Item] = [
    ("hydraulic_cylinder", "Гидроцилиндр подъёма"),
    ("dump_pump", "Насос подъёма"),
    ("tailgate", "Задний борт"),
    ("other", "Другое"),
]
_REEFER_EXTRA: list[_Item] = [
    ("reefer_unit", "Холодильная установка"),
    ("evaporator", "Испаритель"),
    ("reefer_compressor", "Компрессор рефрижератора"),
    ("insulation", "Теплоизоляция"),
    ("other", "Другое"),
]
_TANKER_EXTRA: list[_Item] = [
    ("tank_vessel", "Ёмкость / цистерна"),
    ("pump_unit", "Насосный агрегат"),
    ("hoses_valves", "Рукава / арматура"),
    ("metering", "Счётчик / дозатор"),
    ("other", "Другое"),
]
_TOW_EXTRA: list[_Item] = [
    ("winch", "Лебёдка"),
    ("slide_platform", "Сдвижная платформа"),
    ("crane_arm", "Стрела / манипулятор"),
    ("wheel_lift", "Подъёмник колёс"),
    ("other", "Другое"),
]
_TRACTOR_EXTRA: list[_Item] = [
    ("fifth_wheel", "Седло / ССУ"),
    ("air_lines", "Пневмомагистрали"),
    ("trailer_socket", "Розетка прицепа"),
    ("other", "Другое"),
]


def _with_type_section(
    section_value: str, section_label: str, extras: list[_Item]
) -> list[tuple[str, str, list[_Item]]]:
    out: list[tuple[str, str, list[_Item]]] = []
    inserted = False
    for value, label, items in CARGO_SECTIONS:
        if value == "cargo_area" and not inserted:
            out.append((section_value, section_label, extras))
            inserted = True
        out.append((value, label, items))
    if not inserted:
        out.append((section_value, section_label, extras))
    return out


TYPE_LABELS: dict[str, str] = {
    "dump_truck": "Самосвалы",
    "tractor_unit": "Тягачи",
    "flatbed_truck": "Бортовые грузовики",
    "box_truck": "Фургоны",
    "refrigerated_truck": "Рефрижераторы",
    "light_truck": "Легкий грузовой",
    "tanker_truck": "Цистерны",
    "tow_truck": "Эвакуаторы",
    "other_truck": "Другие грузовики",
}

TYPE_SECTIONS: dict[str, list[tuple[str, str, list[_Item]]]] = {
    "dump_truck": _with_type_section(
        "dump_equipment", "Оборудование самосвала", _DUMP_EXTRA
    ),
    "tractor_unit": _with_type_section(
        "tractor_equipment", "Оборудование тягача", _TRACTOR_EXTRA
    ),
    "flatbed_truck": list(CARGO_SECTIONS),
    "box_truck": list(CARGO_SECTIONS),
    "refrigerated_truck": _with_type_section(
        "reefer_equipment", "Оборудование рефрижератора", _REEFER_EXTRA
    ),
    "light_truck": list(CARGO_SECTIONS),
    "tanker_truck": _with_type_section(
        "tanker_equipment", "Оборудование цистерны", _TANKER_EXTRA
    ),
    "tow_truck": _with_type_section(
        "tow_equipment", "Оборудование эвакуатора", _TOW_EXTRA
    ),
    "other_truck": list(CARGO_SECTIONS),
}


def build_cargo_catalog(*, equipment_type: str | None = None) -> dict[str, Any]:
    key = (equipment_type or "").strip().lower() or None
    if key and key not in TYPE_SECTIONS:
        key = None
    sections_src = TYPE_SECTIONS[key] if key else CARGO_SECTIONS
    label = TYPE_LABELS.get(key or "", "Грузовой транспорт")
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
            for k, v in CARGO_PARTS_SEARCH_ALIASES.items()
        },
    }


def resolve_cargo_parts_alias(text: str) -> dict[str, str] | None:
    key = " ".join(text.strip().lower().split())
    hit = CARGO_PARTS_SEARCH_ALIASES.get(key)
    if not hit:
        return None
    out = {"part_section": hit[0], "part_name": hit[1]}
    if len(hit) == 3:
        out["part_subtype"] = hit[2]
    return out


def encode_parts_draft_path(
    *,
    applicability: str,
    part_section: str,
    part_name: str,
    part_subtype: str | None = None,
    brand: str | None = None,
    model: str | None = None,
    year: str | None = None,
    condition: str | None = None,
    city: str | None = None,
) -> dict[str, str]:
    """Canonical draft payload for parts wizard path + listing fields."""
    data: dict[str, str] = {
        "vehicle_applicability": applicability,
        "part_section": part_section,
        "part_name": part_name,
    }
    if part_subtype:
        data["part_subtype"] = part_subtype
    if brand:
        data["brand"] = brand
    if model:
        data["model"] = model
    if year:
        data["year"] = year
    if condition:
        data["condition"] = condition
    if city:
        data["city"] = city
    return data


def decode_parts_draft_path(data: dict[str, str]) -> dict[str, str]:
    """Round-trip restore of draft path fields (idempotent copy of known keys)."""
    keys = (
        "vehicle_applicability",
        "part_section",
        "part_name",
        "part_subtype",
        "brand",
        "model",
        "year",
        "condition",
        "city",
    )
    return {k: data[k] for k in keys if k in data and data[k]}
