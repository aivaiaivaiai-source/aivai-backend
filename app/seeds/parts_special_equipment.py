# -*- coding: utf-8 -*-
"""Special-equipment parts catalogs — per equipment subtype.

API: special_equipment (+ optional equipment_type = excavator, manipulator, …).
Keys match Flutter VehicleCatalogRepository / SpecialEquipmentSubcategoriesData.
"""
from __future__ import annotations

from typing import Any

APPLICABILITY = "special_equipment"

_Item = tuple[str, str] | tuple[str, str, list[tuple[str, str]]]
_Section = tuple[str, str, list[_Item]]


def _items(*pairs: _Item) -> list[_Item]:
    return list(pairs)


def _section(value: str, label: str, *pairs: _Item) -> _Section:
    return (value, label, _items(*pairs))


# --- Shared building blocks -------------------------------------------------

_OPTICS = [
    ("work_lights", "Рабочие фары"),
    ("headlights", "Фары"),
    ("beacons", "Проблесковые маяки"),
    ("bulbs", "Лампы"),
    ("other", "Другое"),
]

_ENGINE = _section(
    "engine",
    "Двигатель",
    ("engine_assembly", "Двигатель в сборе"),
    ("cylinder_head", "ГБЦ"),
    ("turbo", "Турбина"),
    ("oil_pump", "Масляный насос"),
    ("alternator", "Генератор"),
    ("starter", "Стартер"),
    ("gaskets_seals", "Прокладки и сальники"),
    ("other", "Другое"),
)

_COOLING = _section(
    "cooling",
    "Система охлаждения",
    ("radiator", "Радиатор"),
    ("water_pump", "Помпа"),
    ("thermostat", "Термостат"),
    ("fan", "Вентилятор"),
    ("hoses", "Патрубки"),
    ("other", "Другое"),
)

_FUEL = _section(
    "fuel",
    "Топливная система",
    ("fuel_tank", "Топливный бак"),
    ("fuel_pump", "Топливный насос"),
    ("injection_pump", "ТНВД"),
    ("injectors", "Форсунки"),
    ("fuel_filter", "Топливный фильтр"),
    ("other", "Другое"),
)

_ELECTRICAL = _section(
    "electrical",
    "Электрика и электроника",
    ("battery", "Аккумулятор"),
    ("wiring", "Проводка"),
    ("fuses", "Предохранители"),
    ("relays", "Реле"),
    ("ecu", "Блоки управления"),
    ("sensors", "Датчики"),
    ("display", "Монитор / дисплей"),
    ("other", "Другое"),
)

_BRAKES = _section(
    "brakes",
    "Тормозная система",
    ("brake_pads", "Колодки"),
    ("brake_discs", "Диски"),
    ("brake_drums", "Барабаны"),
    ("calipers", "Суппорты"),
    ("brake_chambers", "Тормозные камеры"),
    ("other", "Другое"),
)

_FILTERS = _section(
    "filters_consumables",
    "Фильтры и расходники",
    ("oil_filter", "Масляный фильтр"),
    ("air_filter", "Воздушный фильтр"),
    ("fuel_filter_consumable", "Топливный фильтр"),
    ("hydraulic_filter", "Гидрофильтр"),
    ("seals_kits", "Ремкомплекты / уплотнения"),
    ("other", "Другое"),
)

_CAB = _section(
    "operator_cab",
    "Кабина оператора",
    ("cab_assembly", "Кабина в сборе"),
    ("doors", "Двери"),
    ("glass", "Стёкла"),
    ("seat", "Сиденье"),
    ("controls", "Органы управления"),
    ("optics", "Оптика и освещение", _OPTICS),
    ("heater_ac", "Отопитель / кондиционер"),
    ("other", "Другое"),
)

_OTHER = _section("other", "Другое", ("other", "Другое"))

_HYDRAULICS_COMMON = _section(
    "hydraulics",
    "Гидравлика",
    ("main_pump", "Гидронасос"),
    ("hydraulic_motor", "Гидромотор"),
    ("control_valve", "Гидрораспределитель"),
    ("hydraulic_cylinder", "Гидроцилиндр"),
    ("hoses_rvd", "РВД / рукава"),
    ("fittings", "Фитинги"),
    ("filters_hydraulic", "Гидрофильтры"),
    ("coolers", "Маслоохладитель"),
    ("other", "Другое"),
)

_TRACK_UNDERCARRIAGE = _section(
    "undercarriage",
    "Ходовая часть",
    ("tracks", "Гусеницы"),
    ("track_shoes", "Траки / башмаки"),
    ("rollers", "Катки"),
    ("idlers", "Направляющие колёса"),
    ("sprockets", "Ведущие звёздочки"),
    ("travel_drive", "Бортовой редуктор хода"),
    ("swing_drive", "Редуктор поворота"),
    ("swing_bearing", "Опорно-поворотный круг"),
    ("other", "Другое"),
)

_MIXED_UNDERCARRIAGE = _section(
    "undercarriage",
    "Ходовая часть",
    ("tracks", "Гусеницы"),
    ("track_shoes", "Траки / башмаки"),
    ("rollers", "Катки"),
    ("idlers", "Направляющие колёса"),
    ("sprockets", "Ведущие звёздочки"),
    ("travel_drive", "Бортовой редуктор хода"),
    ("swing_drive", "Редуктор поворота"),
    ("swing_bearing", "Опорно-поворотный круг"),
    ("axles", "Мосты"),
    ("hubs", "Ступицы"),
    ("springs", "Рессоры / подвеска"),
    ("brakes", "Тормоза ходовой"),
    ("other", "Другое"),
)

_WHEELED_UNDERCARRIAGE = _section(
    "undercarriage",
    "Ходовая часть",
    # «Шины и диски» — отдельная L1 Транспорта, не внутри запчастей спецтехники.
    ("axles", "Мосты"),
    ("hubs", "Ступицы"),
    ("springs", "Рессоры / подвеска"),
    ("brakes", "Тормоза ходовой"),
    ("other", "Другое"),
)

_TRANSMISSION = _section(
    "transmission",
    "Трансмиссия и привод",
    ("gearbox", "Коробка передач"),
    ("torque_converter", "Гидротрансформатор"),
    ("driveshaft", "Кардан"),
    ("differential", "Дифференциал / редуктор"),
    ("pto", "ВОМ / отбор мощности"),
    ("other", "Другое"),
)


def _core(*extra: _Section) -> list[_Section]:
    """Engine / fluids / electrics / cab + type-specific extras + other."""
    return [
        _ENGINE,
        *extra,
        _CAB,
        _ELECTRICAL,
        _COOLING,
        _FUEL,
        _BRAKES,
        _FILTERS,
        _OTHER,
    ]


# --- Per-type working-equipment / specialty sections ------------------------

_EXCAVATOR_WORK = _section(
    "working_equipment",
    "Рабочее оборудование",
    ("boom", "Стрела"),
    ("arm_stick", "Рукоять"),
    ("bucket", "Ковш"),
    ("bucket_linkage", "Тяги ковша"),
    ("quick_coupler", "Быстросъём"),
    ("hydraulic_hammer", "Гидромолот"),
    ("ripper", "Рыхлитель"),
    ("auger", "Бур"),
    ("other", "Другое"),
)

_LOADER_WORK = _section(
    "working_equipment",
    "Рабочее оборудование",
    ("loader_boom", "Стрела погрузчика"),
    ("bucket", "Ковш"),
    ("quick_coupler", "Быстросъём"),
    ("forks", "Вилы"),
    ("grapple", "Грейфер / захват"),
    ("blade", "Отвал"),
    ("other", "Другое"),
)

_CRANE_WORK = _section(
    "working_equipment",
    "Крановое оборудование",
    ("telescopic_boom", "Телескопическая стрела"),
    ("jib", "Удлинитель / гусёк"),
    ("winch", "Лебёдка"),
    ("hook_block", "Крюковая обойма"),
    ("cable", "Канат"),
    ("outriggers", "Аутригеры / опоры"),
    ("slewing", "Механизм поворота"),
    ("counterweight", "Противовес"),
    ("other", "Другое"),
)

_AERIAL_WORK = _section(
    "working_equipment",
    "Подъёмное оборудование",
    ("boom_sections", "Секции стрелы"),
    ("basket", "Люлька / корзина"),
    ("outriggers", "Опоры"),
    ("leveling", "Система выравнивания"),
    ("controls_platform", "Пульт на площадке"),
    ("other", "Другое"),
)

_BULLDOZER_WORK = _section(
    "working_equipment",
    "Рабочее оборудование",
    ("blade", "Отвал"),
    ("blade_cylinders", "Цилиндры отвала"),
    ("ripper", "Рыхлитель"),
    ("ripper_shank", "Стойка рыхлителя"),
    ("other", "Другое"),
)

_ROLLER_WORK = _section(
    "working_equipment",
    "Рабочие органы",
    ("drum", "Вал / барабан"),
    ("vibration_unit", "Виброузел"),
    ("scraper", "Скребки"),
    ("water_system", "Система полива"),
    ("other", "Другое"),
)

_GRADER_WORK = _section(
    "working_equipment",
    "Рабочее оборудование",
    ("moldboard", "Отвал грейдера"),
    ("circle", "Поворотный круг"),
    ("drawbar", "Тяговая рама"),
    ("scarifier", "Рыхлитель / скарификатор"),
    ("other", "Другое"),
)

_MANIPULATOR_WORK = _section(
    "working_equipment",
    "Оборудование манипулятора",
    ("crane_column", "Колонна"),
    ("knuckle_boom", "Шарнирная стрела"),
    ("outriggers", "Аутригеры / опоры"),
    ("rotator", "Ротатор"),
    ("grab", "Грейфер / захват"),
    ("winch", "Лебёдка"),
    ("hook", "Крюк"),
    ("stabilizers", "Стабилизаторы"),
    ("mounting_base", "Основание / плита крепления"),
    ("other", "Другое"),
)

_MANIPULATOR_HYDRAULICS = _section(
    "hydraulics",
    "Гидравлика манипулятора",
    ("main_pump", "Гидронасос"),
    ("control_valve", "Гидрораспределитель"),
    ("boom_cylinders", "Цилиндры стрелы"),
    ("outrigger_cylinders", "Цилиндры опор"),
    ("rotator_motor", "Гидромотор ротатора"),
    ("hoses_rvd", "РВД / рукава"),
    ("fittings", "Фитинги"),
    ("filters_hydraulic", "Гидрофильтры"),
    ("other", "Другое"),
)

_CONCRETE_WORK = _section(
    "working_equipment",
    "Бетонооборудование",
    ("mixer_drum", "Барабан"),
    ("chute", "Лоток"),
    ("water_system", "Водяная система"),
    ("pump_unit", "Насосный узел"),
    ("pipeline", "Бетоновод"),
    ("other", "Другое"),
)

_MIXER_WORK = _section(
    "working_equipment",
    "Оборудование бетономешалки",
    ("mixer_drum", "Барабан"),
    ("drum_drive", "Привод барабана"),
    ("chute", "Лоток"),
    ("water_system", "Водяная система"),
    ("hydraulic_reducer", "Редуктор"),
    ("other", "Другое"),
)

_CONCRETE_PUMP_WORK = _section(
    "working_equipment",
    "Оборудование бетононасоса",
    ("pump_unit", "Насосный узел"),
    ("pipeline", "Бетоновод"),
    ("boom_sections", "Секции стрелы"),
    ("placing_boom", "Распределительная стрела"),
    ("hopper", "Бункер"),
    ("s_valve", "S-клапан / шибер"),
    ("outriggers", "Опоры"),
    ("other", "Другое"),
)

_SEPTIC_WORK = _section(
    "working_equipment",
    "Ассенизаторное оборудование",
    ("vacuum_tank", "Цистерна"),
    ("vacuum_pump", "Вакуумный насос"),
    ("suction_hose", "Всасывающий рукав"),
    ("valves", "Запорная арматура"),
    ("level_gauge", "Указатель уровня"),
    ("other", "Другое"),
)

_MINI_DUMPER_WORK = _section(
    "working_equipment",
    "Рабочее оборудование",
    ("skip_body", "Кузов / ковш"),
    ("tipping_cylinder", "Цилиндр опрокидывания"),
    ("skip_hinges", "Петли кузова"),
    ("other", "Другое"),
)

_FORKLIFT_WORK = _section(
    "working_equipment",
    "Грузоподъёмное оборудование",
    ("mast", "Мачта"),
    ("carriage", "Каретка"),
    ("forks", "Вилы"),
    ("side_shift", "Сайдшифтер"),
    ("lift_chains", "Цепи подъёма"),
    ("lift_cylinder", "Цилиндр подъёма"),
    ("tilt_cylinder", "Цилиндр наклона"),
    ("other", "Другое"),
)

_TOW_WORK = _section(
    "working_equipment",
    "Эвакуаторное оборудование",
    ("platform", "Платформа"),
    ("winch", "Лебёдка"),
    ("slide_rails", "Сдвижные направляющие"),
    ("wheel_lift", "Подхват колёс"),
    ("crane_arm", "Кран-стрела"),
    ("cable", "Канат"),
    ("other", "Другое"),
)

_MUNICIPAL_WORK = _section(
    "working_equipment",
    "Коммунальное и дорожное оборудование",
    ("brush", "Щётки"),
    ("hopper", "Бункер"),
    ("water_tank", "Цистерна / бак"),
    ("pump", "Насос"),
    ("blade", "Отвал"),
    ("spreader", "Разбрасыватель"),
    ("vacuum", "Вакуумное оборудование"),
    ("other", "Другое"),
)

_DRILLING_WORK = _section(
    "working_equipment",
    "Буровое оборудование",
    ("mast", "Мачта"),
    ("rotary_head", "Вращатель"),
    ("kelly", "Штанга Келли"),
    ("auger", "Шнек / бур"),
    ("winch", "Лебёдка"),
    ("outriggers", "Опоры"),
    ("other", "Другое"),
)

_CRUSHING_WORK = _section(
    "working_equipment",
    "Дробильно-сортировочное",
    ("jaw_plates", "Брони / щеки"),
    ("cone_liners", "Футеровки"),
    ("screen_mesh", "Сита"),
    ("conveyor", "Конвейер"),
    ("feeder", "Питатель"),
    ("other", "Другое"),
)

_ATTACHMENT_WORK = _section(
    "working_equipment",
    "Навесное оборудование",
    ("bucket", "Ковш"),
    ("hydraulic_hammer", "Гидромолот"),
    ("quick_coupler", "Быстросъём"),
    ("ripper", "Рыхлитель"),
    ("forks", "Вилы"),
    ("grapple", "Грейфер"),
    ("auger", "Бур"),
    ("shear", "Ножницы"),
    ("compactor", "Виброплита навесная"),
    ("other", "Другое"),
)

TYPE_LABELS: dict[str, str] = {
    "excavator": "Экскаваторы",
    "loader": "Погрузчики",
    "forklift": "Вилочные погрузчики",
    "truck_crane": "Автокраны",
    "tow_truck": "Эвакуаторы",
    "aerial_platform": "Автовышки",
    "bulldozer": "Бульдозеры",
    "road_roller": "Катки",
    "grader": "Грейдеры",
    "manipulator": "Манипуляторы",
    "concrete_equipment": "Бетонотехника",
    "concrete_mixer": "Автобетономешалки",
    "concrete_pump": "Бетононасосы",
    "septic_truck": "Ассенизаторы",
    "mini_dumper": "Мини-думпер",
    "municipal": "Коммунальная и дорожная техника",
    "drilling": "Буровая техника",
    "crushing_screening": "Дробильно-сортировочная техника",
    "attachment": "Навесное и рабочее оборудование",
    "other_special": "Другая спецтехника",
}

TYPE_SECTIONS: dict[str, list[_Section]] = {
    "excavator": _core(
        _HYDRAULICS_COMMON,
        _EXCAVATOR_WORK,
        _TRACK_UNDERCARRIAGE,
    ),
    "loader": _core(
        _HYDRAULICS_COMMON,
        _LOADER_WORK,
        _WHEELED_UNDERCARRIAGE,
        _TRANSMISSION,
    ),
    "truck_crane": _core(
        _HYDRAULICS_COMMON,
        _CRANE_WORK,
        _WHEELED_UNDERCARRIAGE,
        _TRANSMISSION,
    ),
    "aerial_platform": _core(
        _HYDRAULICS_COMMON,
        _AERIAL_WORK,
        _WHEELED_UNDERCARRIAGE,
        _TRANSMISSION,
    ),
    "bulldozer": _core(
        _HYDRAULICS_COMMON,
        _BULLDOZER_WORK,
        _TRACK_UNDERCARRIAGE,
    ),
    "road_roller": _core(
        _HYDRAULICS_COMMON,
        _ROLLER_WORK,
        _WHEELED_UNDERCARRIAGE,
        _TRANSMISSION,
    ),
    "grader": _core(
        _HYDRAULICS_COMMON,
        _GRADER_WORK,
        _WHEELED_UNDERCARRIAGE,
        _TRANSMISSION,
    ),
    "manipulator": _core(
        _MANIPULATOR_HYDRAULICS,
        _MANIPULATOR_WORK,
        _WHEELED_UNDERCARRIAGE,
        _TRANSMISSION,
    ),
    "concrete_equipment": _core(
        _HYDRAULICS_COMMON,
        _CONCRETE_WORK,
        _WHEELED_UNDERCARRIAGE,
        _TRANSMISSION,
    ),
    "concrete_mixer": _core(
        _HYDRAULICS_COMMON,
        _MIXER_WORK,
        _WHEELED_UNDERCARRIAGE,
        _TRANSMISSION,
    ),
    "concrete_pump": _core(
        _HYDRAULICS_COMMON,
        _CONCRETE_PUMP_WORK,
        _WHEELED_UNDERCARRIAGE,
        _TRANSMISSION,
    ),
    "septic_truck": _core(
        _HYDRAULICS_COMMON,
        _SEPTIC_WORK,
        _WHEELED_UNDERCARRIAGE,
        _TRANSMISSION,
    ),
    "mini_dumper": _core(
        _HYDRAULICS_COMMON,
        _MINI_DUMPER_WORK,
        _section(
            "undercarriage",
            "Ходовая часть",
            ("tracks", "Гусеницы"),
            ("axles", "Мосты"),
            ("hubs", "Ступицы"),
            ("other", "Другое"),
        ),
        _TRANSMISSION,
    ),
    "forklift": _core(
        _HYDRAULICS_COMMON,
        _FORKLIFT_WORK,
        _WHEELED_UNDERCARRIAGE,
        _TRANSMISSION,
    ),
    "tow_truck": _core(
        _HYDRAULICS_COMMON,
        _TOW_WORK,
        _WHEELED_UNDERCARRIAGE,
        _TRANSMISSION,
    ),
    "municipal": _core(
        _HYDRAULICS_COMMON,
        _MUNICIPAL_WORK,
        _WHEELED_UNDERCARRIAGE,
        _TRANSMISSION,
    ),
    "drilling": _core(
        _HYDRAULICS_COMMON,
        _DRILLING_WORK,
        _section(
            "undercarriage",
            "Ходовая часть",
            ("tracks", "Гусеницы"),
            ("outriggers_frame", "Рама / опоры"),
            ("axles", "Мосты"),
            ("other", "Другое"),
        ),
    ),
    "crushing_screening": _core(
        _HYDRAULICS_COMMON,
        _CRUSHING_WORK,
        _section(
            "undercarriage",
            "Ходовая / шасси",
            ("tracks", "Гусеницы"),
            ("frame", "Рама"),
            ("other", "Другое"),
        ),
    ),
    "attachment": [
        _ATTACHMENT_WORK,
        _HYDRAULICS_COMMON,
        _FILTERS,
        _OTHER,
    ],
    "other_special": _core(
        _HYDRAULICS_COMMON,
        _section(
            "working_equipment",
            "Рабочее оборудование",
            ("attachments", "Навесное"),
            ("other", "Другое"),
        ),
        _MIXED_UNDERCARRIAGE,
        _TRANSMISSION,
    ),
}

# Generic fallback (no subtype) — same as excavator-leaning CE set.
SPECIAL_SECTIONS: list[_Section] = TYPE_SECTIONS["other_special"]

SPECIAL_PARTS_SEARCH_ALIASES: dict[str, tuple[str, str] | tuple[str, str, str]] = {
    "ковш": ("working_equipment", "bucket"),
    "гидромолот": ("working_equipment", "hydraulic_hammer"),
    "гидронасос": ("hydraulics", "main_pump"),
    "гидроцилиндр": ("hydraulics", "hydraulic_cylinder"),
    "рвд": ("hydraulics", "hoses_rvd"),
    "гусеница": ("undercarriage", "tracks"),
    "аутригер": ("working_equipment", "outriggers"),
    "ротатор": ("working_equipment", "rotator"),
    "колонна": ("working_equipment", "crane_column"),
    "лебёдка": ("working_equipment", "winch"),
    "лебедка": ("working_equipment", "winch"),
    "опк": ("undercarriage", "swing_bearing"),
    "тнвд": ("fuel", "injection_pump"),
    "барабан": ("working_equipment", "mixer_drum"),
    "бетоновод": ("working_equipment", "pipeline"),
    "вилы": ("working_equipment", "forks"),
    "мачта": ("working_equipment", "mast"),
    "платформа": ("working_equipment", "platform"),
    "цистерна": ("working_equipment", "vacuum_tank"),
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


def build_special_equipment_catalog(
    *,
    equipment_type: str | None = None,
) -> dict[str, Any]:
    key = (equipment_type or "").strip().lower() or None
    if key and key not in TYPE_SECTIONS:
        # Unknown subtype — keep generic CE catalog, not 404.
        key = None
    sections_src = TYPE_SECTIONS[key] if key else SPECIAL_SECTIONS
    label = TYPE_LABELS.get(key or "", "Спецтехника")
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
            for k, v in SPECIAL_PARTS_SEARCH_ALIASES.items()
        },
    }
