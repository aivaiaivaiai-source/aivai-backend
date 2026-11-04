# -*- coding: utf-8 -*-
"""Transport → Спецтехника V2 — leaf Create/Search SoT.

Parent ``transport-special-equipment`` is picker-only (not live Create SoT).
Manipulator primary Brand/Model = chassis; crane OEM → ``manipulator_brand``.
"""
from __future__ import annotations

from typing import Any

from app.models.category_enums import CategoryFieldType, CategoryFilterType, VehicleType
from app.seeds.car_sale_v2 import (
    CONDITION_V2_CHOICES,
    CONTACT_METHOD_CHOICES,
    EXCHANGE_CHOICES,
    INSTALLMENT_CHOICES,
    NEGOTIABLE_CHOICES,
    YES_NO_CHOICES,
)

SPECIAL_PARENT_SLUG = "transport-special-equipment"

SPECIAL_LEAF_SLUGS: tuple[str, ...] = (
    "transport-special-equipment-ekskavatory",
    "transport-special-equipment-pogruzchiki",
    "transport-special-equipment-vilochnye-pogruzchiki",
    "transport-special-equipment-avtokrany",
    "transport-special-equipment-avtovyshki",
    "transport-special-equipment-buldozery",
    "transport-special-equipment-katki",
    "transport-special-equipment-greydery",
    "transport-special-equipment-manipulyatory",
    "transport-special-equipment-avtobetonomehalki",
    "transport-special-equipment-betononasosy",
    "transport-special-equipment-assenizatory",
    "transport-special-equipment-mini-dumper",
    "transport-special-equipment-kommunalnaya-tehnika",
    "transport-special-equipment-burovaya-tehnika",
    "transport-special-equipment-drobilno-sortirovochnaya-tehnika",
    "transport-special-equipment-navesnoe-i-rabochee-oborudovanie",
    "transport-special-equipment-drugaya-spetstehnika",
)

SPECIAL_LEAF_LABELS: dict[str, str] = {
    "transport-special-equipment-ekskavatory": "Экскаваторы",
    "transport-special-equipment-pogruzchiki": "Погрузчики",
    "transport-special-equipment-vilochnye-pogruzchiki": "Вилочные погрузчики",
    "transport-special-equipment-avtokrany": "Автокраны",
    "transport-special-equipment-avtovyshki": "Автовышки",
    "transport-special-equipment-buldozery": "Бульдозеры",
    "transport-special-equipment-katki": "Катки",
    "transport-special-equipment-greydery": "Грейдеры",
    "transport-special-equipment-manipulyatory": "Манипуляторы",
    "transport-special-equipment-avtobetonomehalki": "Автобетономешалки",
    "transport-special-equipment-betononasosy": "Бетононасосы",
    "transport-special-equipment-assenizatory": "Ассенизаторы",
    "transport-special-equipment-mini-dumper": "Мини-думпер",
    "transport-special-equipment-kommunalnaya-tehnika": "Коммунальная и дорожная техника",
    "transport-special-equipment-burovaya-tehnika": "Буровая техника",
    "transport-special-equipment-drobilno-sortirovochnaya-tehnika": (
        "Дробильно-сортировочная техника"
    ),
    "transport-special-equipment-navesnoe-i-rabochee-oborudovanie": (
        "Навесное и рабочее оборудование"
    ),
    "transport-special-equipment-drugaya-spetstehnika": "Другая спецтехника",
}

SPECIAL_LEAF_SORT: dict[str, int] = {
    "transport-special-equipment-ekskavatory": 10,
    "transport-special-equipment-pogruzchiki": 20,
    "transport-special-equipment-vilochnye-pogruzchiki": 25,
    "transport-special-equipment-avtokrany": 30,
    "transport-special-equipment-avtovyshki": 40,
    "transport-special-equipment-buldozery": 50,
    "transport-special-equipment-katki": 60,
    "transport-special-equipment-greydery": 70,
    "transport-special-equipment-manipulyatory": 80,
    "transport-special-equipment-avtobetonomehalki": 90,
    "transport-special-equipment-betononasosy": 92,
    "transport-special-equipment-assenizatory": 94,
    "transport-special-equipment-mini-dumper": 96,
    "transport-special-equipment-kommunalnaya-tehnika": 110,
    "transport-special-equipment-burovaya-tehnika": 120,
    "transport-special-equipment-drobilno-sortirovochnaya-tehnika": 130,
    "transport-special-equipment-navesnoe-i-rabochee-oborudovanie": 140,
    "transport-special-equipment-drugaya-spetstehnika": 150,
}

SPECIAL_LEAF_VEHICLE_TYPE: dict[str, str] = {
    "transport-special-equipment-ekskavatory": "excavator",
    "transport-special-equipment-pogruzchiki": "loader",
    "transport-special-equipment-vilochnye-pogruzchiki": "forklift",
    "transport-special-equipment-avtokrany": "truck_crane",
    "transport-special-equipment-avtovyshki": "aerial_platform",
    "transport-special-equipment-buldozery": "bulldozer",
    "transport-special-equipment-katki": "road_roller",
    "transport-special-equipment-greydery": "grader",
    "transport-special-equipment-manipulyatory": "manipulator",
    "transport-special-equipment-avtobetonomehalki": "concrete_mixer",
    "transport-special-equipment-betononasosy": "concrete_pump",
    "transport-special-equipment-assenizatory": "septic_truck",
    "transport-special-equipment-mini-dumper": "mini_dumper",
    "transport-special-equipment-kommunalnaya-tehnika": "municipal",
    "transport-special-equipment-burovaya-tehnika": "drilling",
    "transport-special-equipment-drobilno-sortirovochnaya-tehnika": "crushing_screening",
    "transport-special-equipment-navesnoe-i-rabochee-oborudovanie": "attachment",
    "transport-special-equipment-drugaya-spetstehnika": "other_special",
}

SPECIAL_INACTIVE_LEGACY_SLUGS: tuple[str, ...] = (
    "transport-special-equipment-evakuatory",
    "transport-special-equipment-betonotehnika",
    "transport-special-equipment-dorozhnaya-tehnika",
    "transport-special-equipment-zapchasti-dlya-spetstehniki",
    "transport-special-equipment-remont-i-obsluzhivanie",
    "transport-cargo-spetsgruzoviki",
)

# Alias normalized → leaf/parent slug (sale-oriented).
SPECIAL_LEAF_ALIASES: dict[str, str] = {
    "спецтехника": SPECIAL_PARENT_SLUG,
    "экскаватор": "transport-special-equipment-ekskavatory",
    "погрузчик": "transport-special-equipment-pogruzchiki",
    "вилочный погрузчик": "transport-special-equipment-vilochnye-pogruzchiki",
    "автокран": "transport-special-equipment-avtokrany",
    "автовышка": "transport-special-equipment-avtovyshki",
    "бульдозер": "transport-special-equipment-buldozery",
    "каток": "transport-special-equipment-katki",
    "грейдер": "transport-special-equipment-greydery",
    "манипулятор": "transport-special-equipment-manipulyatory",
    "камаз манипулятор": "transport-special-equipment-manipulyatory",
    "автобетономешалка": "transport-special-equipment-avtobetonomehalki",
    "бетононасос": "transport-special-equipment-betononasosy",
    "ассенизатор": "transport-special-equipment-assenizatory",
}

# Sale-phrase aliases for evacuator (keep bare «эвакуатор» on Services).
EVACUATOR_SALE_ALIASES: dict[str, str] = {
    "продам эвакуатор": "transport-cargo-evakuatory",
    "продажа эвакуатора": "transport-cargo-evakuatory",
    "эвакуатор продам": "transport-cargo-evakuatory",
}

_SELLER = ("Частное лицо", "Компания", "Дилер")
_FUEL = (
    "Бензин",
    "Дизель",
    "Газ",
    "Бензин + Газ",
    "Гибрид",
    "Электро",
    "Другое",
)
_FORKLIFT_FUEL = (
    "Дизель",
    "Бензин",
    "Газ",
    "Электро",
    "Другое",
)

EXCAVATOR_TYPES = (
    "Гусеничный экскаватор",
    "Колёсный экскаватор",
    "Мини-экскаватор",
    "Экскаватор-погрузчик",
    "Другой",
)
LOADER_TYPES = (
    "Фронтальный погрузчик",
    "Мини-погрузчик",
    "Телескопический погрузчик",
    "Другой",
)
AERIAL_TYPES = (
    "Автовышка",
    "Ножничный подъёмник",
    "Телескопический подъёмник",
    "Другой",
)
MUNICIPAL_TYPES = (
    "Асфальтоукладчик",
    "Дорожная фреза",
    "Снегоуборочная техника",
    "Мусоровоз",
    "Подметально-уборочная техника",
    "Другая коммунальная и дорожная техника",
)
OTHER_SPECIAL_TYPES = (
    "Башенный кран",
    "Компрессор",
    "Другая спецтехника",
)
CONCRETE_PUMP_TYPES = (
    "Автобетононасос",
    "Стационарный бетононасос",
    "Другой",
)
CRUSHING_TYPES = (
    "Дробилка",
    "Грохот",
    "Дробильно-сортировочный комплекс",
    "Другое",
)
ATTACHMENT_TYPES = (
    "Ковш",
    "Гидромолот",
    "Вилы",
    "Бур",
    "Отвал",
    "Другое",
)

MANIPULATOR_CRANE_BRANDS = (
    "Palfinger",
    "HIAB",
    "Fassi",
    "UNIC",
    "Tadano",
    "Soosan",
    "Kanglim",
    "Dongyang",
    "XCMG",
    "Другая",
)

# Crane OEM brand slugs currently typed as manipulator — disable for primary picker.
MANIPULATOR_CRANE_OEM_BRAND_SLUGS: frozenset[str] = frozenset(
    {
        "palfinger-manip",
        "hiab",
        "fassi",
        "unimog-manip",
        "xcmg-manip",
        "soosan",
        "kanglim",
        "dongyang-manip",
    }
)

# Chassis-oriented manipulator brands (keep/enable as primary catalog).
MANIPULATOR_CHASSIS_BRANDS: list[tuple[str, str, str | None, VehicleType]] = [
    ("kamaz-manip", "KamAZ", "Russia", VehicleType.manipulator),
    ("gaz-manip", "ГАЗ", "Russia", VehicleType.manipulator),
    ("mercedes-manip", "Mercedes-Benz", "Germany", VehicleType.manipulator),
    ("hyundai-manip", "Hyundai", "Korea", VehicleType.manipulator),
    ("isuzu-manip", "Isuzu", "Japan", VehicleType.manipulator),
    ("howo-manip", "Howo", "China", VehicleType.manipulator),
    ("maz-manip", "МАЗ", "Belarus", VehicleType.manipulator),
    ("dongfeng-manip", "Dongfeng", "China", VehicleType.manipulator),
    ("foton-manip", "Foton", "China", VehicleType.manipulator),
    ("other-manipulator", "Другая марка", None, VehicleType.manipulator),
]

MANIPULATOR_CHASSIS_MODELS: dict[str, list[tuple[str, str]]] = {
    "kamaz-manip": [("4308", "4308"), ("43118", "43118"), ("65115", "65115")],
    "gaz-manip": [("gazelle-next", "Газель Next"), ("valdai-next", "Валдай Next")],
    "mercedes-manip": [
        ("atego", "Atego"),
        ("axor", "Axor"),
        ("actros", "Actros"),
    ],
    "hyundai-manip": [("hd78", "HD78"), ("mighty", "Mighty"), ("hd120", "HD120")],
    "isuzu-manip": [("npr", "NPR"), ("nqr", "NQR"), ("elf", "Elf")],
    "howo-manip": [("howo-t5g", "T5G"), ("howo-a7", "A7")],
    "maz-manip": [("4371", "4371"), ("5337", "5337")],
    "dongfeng-manip": [("dfh", "DFH"), ("captain-t", "Captain-T")],
    "foton-manip": [("auman", "Auman"), ("ollin", "Ollin")],
    "other-manipulator": [("other-model", "Другая модель")],
}

SPECIAL_OTHER_BRAND_TYPES: tuple[str, ...] = (
    "excavator",
    "loader",
    "forklift",
    "truck_crane",
    "aerial_platform",
    "bulldozer",
    "road_roller",
    "grader",
    "manipulator",
    "concrete_mixer",
    "concrete_pump",
    "septic_truck",
    "mini_dumper",
    "municipal",
    "drilling",
    "crushing_screening",
    "attachment",
    "other_special",
)

SPECIAL_YEAR_MIN = 1970
HOURS_MAX = 100_000
MILEAGE_MAX = 3_000_000
LOAD_KG_MAX = 500_000
HEIGHT_M_MAX = 200
DEPTH_M_MAX = 50
BUCKET_M3_MAX = 50
BOOM_M_MAX = 120
WEIGHT_KG_MAX = 500_000
DRUM_M3_MAX = 20
TANK_L_MAX = 50_000
DRILL_M_MAX = 500


def _choices(*labels: str) -> dict[str, Any]:
    items = [{"value": x, "label": x} for x in labels]
    return {"choices": items, "values": items}


def _field(
    key: str,
    label: str,
    ftype: CategoryFieldType,
    required: bool,
    sort: int,
    options: dict[str, Any] | None = None,
    hint: str | None = None,
) -> tuple[str, str, CategoryFieldType, bool, int, dict[str, Any] | None, str | None]:
    return (key, label, ftype, required, sort, options, hint)


def _filt(
    key: str,
    label: str,
    ftype: CategoryFilterType,
    sort: int,
    config: dict[str, Any] | None,
) -> tuple[str, str, CategoryFilterType, int, dict[str, Any] | None]:
    return (key, label, ftype, sort, config)


def _opt_cfg(*labels: str, **extra: Any) -> dict[str, Any]:
    cfg: dict[str, Any] = {
        "options": [{"value": o, "label": o} for o in labels],
    }
    cfg.update(extra)
    return cfg


def _geo_head() -> list:
    return [
        _field("region", "Регион", CategoryFieldType.string, True, 0),
        _field("city", "Город", CategoryFieldType.city, True, 1),
    ]


def _brand_model(sort: int = 10) -> list:
    return [
        _field("brand", "Марка", CategoryFieldType.brand, False, sort),
        _field("model", "Модель", CategoryFieldType.model, False, sort + 10),
    ]


def _year(sort: int) -> list:
    return [
        _field(
            "year",
            "Год выпуска",
            CategoryFieldType.year,
            False,
            sort,
            {"min": SPECIAL_YEAR_MIN, "max_offset_years": 1},
        ),
    ]


def _equipment_type(options: tuple[str, ...], sort: int) -> list:
    return [
        _field(
            "equipment_type",
            "Тип техники",
            CategoryFieldType.enum,
            False,
            sort,
            _choices(*options),
        ),
    ]


def _operating_hours(sort: int) -> list:
    return [
        _field(
            "operating_hours",
            "Моточасы",
            CategoryFieldType.number,
            False,
            sort,
            {"min": 0, "max": HOURS_MAX, "unit": "ч", "integer": True},
            "Наработка в моточасах",
        ),
    ]


def _mileage(sort: int) -> list:
    return [
        _field(
            "mileage",
            "Пробег, км",
            CategoryFieldType.number,
            False,
            sort,
            {"min": 0, "max": MILEAGE_MAX, "unit": "км", "integer": True},
            "Пробег в километрах",
        ),
    ]


def _fuel(sort: int, *, options: tuple[str, ...] = _FUEL) -> list:
    return [
        _field(
            "fuel",
            "Топливо",
            CategoryFieldType.enum,
            False,
            sort,
            _choices(*options),
        ),
    ]


def _load_capacity(sort: int) -> list:
    return [
        _field(
            "load_capacity_kg",
            "Грузоподъёмность",
            CategoryFieldType.number,
            False,
            sort,
            {"min": 0, "max": LOAD_KG_MAX, "unit": "kg", "integer": True},
            "Грузоподъёмность в килограммах",
        ),
    ]


def _lift_height(sort: int) -> list:
    return [
        _field(
            "lift_height_m",
            "Высота подъёма",
            CategoryFieldType.decimal,
            False,
            sort,
            {"min": 0, "max": HEIGHT_M_MAX, "unit": "m"},
            "Высота подъёма в метрах",
        ),
    ]


def _digging_depth(sort: int) -> list:
    return [
        _field(
            "digging_depth_m",
            "Глубина копания",
            CategoryFieldType.decimal,
            False,
            sort,
            {"min": 0, "max": DEPTH_M_MAX, "unit": "m"},
        ),
    ]


def _bucket(sort: int) -> list:
    return [
        _field(
            "bucket_capacity_m3",
            "Объём ковша",
            CategoryFieldType.decimal,
            False,
            sort,
            {"min": 0, "max": BUCKET_M3_MAX, "unit": "m3"},
        ),
    ]


def _boom_reach(sort: int) -> list:
    return [
        _field(
            "boom_reach_m",
            "Вылет стрелы",
            CategoryFieldType.decimal,
            False,
            sort,
            {"min": 0, "max": BOOM_M_MAX, "unit": "m"},
        ),
    ]


def _weight(sort: int) -> list:
    return [
        _field(
            "weight_kg",
            "Масса",
            CategoryFieldType.number,
            False,
            sort,
            {"min": 0, "max": WEIGHT_KG_MAX, "unit": "kg", "integer": True},
            "Масса техники в килограммах",
        ),
    ]


def _condition_block(sort: int, *, after_accident: bool = False) -> list:
    rows = [
        _field(
            "condition",
            "Состояние",
            CategoryFieldType.enum,
            True,
            sort,
            _choices(*CONDITION_V2_CHOICES),
        ),
        _field(
            "needs_investment",
            "Требует вложений",
            CategoryFieldType.enum,
            False,
            sort + 5,
            _choices(*YES_NO_CHOICES),
        ),
    ]
    if after_accident:
        rows.append(
            _field(
                "after_accident",
                "После ДТП",
                CategoryFieldType.enum,
                False,
                sort + 10,
                _choices(*YES_NO_CHOICES),
            )
        )
    return rows


def _commerce(sort: int) -> list:
    return [
        _field("price", "Цена", CategoryFieldType.price, True, sort),
        _field(
            "negotiable",
            "Возможность торга",
            CategoryFieldType.enum,
            True,
            sort + 10,
            _choices(*NEGOTIABLE_CHOICES),
        ),
        _field(
            "exchange",
            "Возможность обмена",
            CategoryFieldType.enum,
            False,
            sort + 20,
            _choices(*EXCHANGE_CHOICES),
        ),
        _field(
            "installment",
            "Возможность рассрочки",
            CategoryFieldType.enum,
            False,
            sort + 30,
            _choices(*INSTALLMENT_CHOICES),
        ),
        _field(
            "seller_type",
            "Кто продаёт",
            CategoryFieldType.enum,
            True,
            sort + 40,
            _choices(*_SELLER),
        ),
        _field(
            "contact_methods",
            "Способы связи",
            CategoryFieldType.enum,
            True,
            sort + 50,
            _choices(*CONTACT_METHOD_CHOICES),
        ),
    ]


def _excavator_fields() -> list:
    return [
        *_geo_head(),
        *_equipment_type(EXCAVATOR_TYPES, 5),
        *_brand_model(10),
        *_year(30),
        *_operating_hours(40),
        *_weight(50),
        *_digging_depth(60),
        *_bucket(70),
        *_fuel(80),
        *_condition_block(120),
        *_commerce(140),
    ]


def _loader_fields() -> list:
    return [
        *_geo_head(),
        *_equipment_type(LOADER_TYPES, 5),
        *_brand_model(10),
        *_year(30),
        *_operating_hours(40),
        *_load_capacity(50),
        *_lift_height(60),
        *_bucket(70),
        *_fuel(80),
        *_condition_block(120),
        *_commerce(140),
    ]


def _forklift_fields() -> list:
    return [
        *_geo_head(),
        *_brand_model(10),
        *_year(30),
        *_operating_hours(40),
        *_load_capacity(50),
        *_lift_height(60),
        *_fuel(70, options=_FORKLIFT_FUEL),
        *_condition_block(120),
        *_commerce(140),
    ]


def _autocrane_fields() -> list:
    return [
        *_geo_head(),
        *_brand_model(10),
        *_year(30),
        *_operating_hours(40),
        *_mileage(45),
        *_load_capacity(50),
        *_boom_reach(60),
        *_weight(70),
        *_fuel(80),
        *_condition_block(120, after_accident=True),
        *_commerce(140),
    ]


def _aerial_fields() -> list:
    return [
        *_geo_head(),
        *_equipment_type(AERIAL_TYPES, 5),
        *_brand_model(10),
        *_year(30),
        *_operating_hours(40),
        *_mileage(45),
        *_lift_height(50),
        *_load_capacity(60),
        *_fuel(70),
        *_condition_block(120, after_accident=True),
        *_commerce(140),
    ]


def _bulldozer_fields() -> list:
    return [
        *_geo_head(),
        *_brand_model(10),
        *_year(30),
        *_operating_hours(40),
        *_weight(50),
        *_fuel(60),
        *_condition_block(120),
        *_commerce(140),
    ]


def _roller_fields() -> list:
    return [
        *_geo_head(),
        *_brand_model(10),
        *_year(30),
        *_operating_hours(40),
        *_weight(50),
        *_fuel(60),
        *_condition_block(120),
        *_commerce(140),
    ]


def _grader_fields() -> list:
    return _roller_fields()


def _manipulator_fields() -> list:
    return [
        *_geo_head(),
        *_brand_model(10),
        _field(
            "manipulator_brand",
            "Марка манипулятора",
            CategoryFieldType.enum,
            False,
            25,
            _choices(*MANIPULATOR_CRANE_BRANDS),
            "Производитель крановой установки",
        ),
        *_year(30),
        *_mileage(40),
        *_operating_hours(45),
        *_load_capacity(50),
        *_boom_reach(60),
        *_fuel(70),
        *_condition_block(120, after_accident=True),
        *_commerce(140),
    ]


def _concrete_mixer_fields() -> list:
    return [
        *_geo_head(),
        *_brand_model(10),
        *_year(30),
        *_mileage(40),
        *_operating_hours(45),
        _field(
            "drum_capacity_m3",
            "Объём барабана",
            CategoryFieldType.decimal,
            False,
            50,
            {"min": 0, "max": DRUM_M3_MAX, "unit": "m3"},
        ),
        *_fuel(60),
        *_condition_block(120, after_accident=True),
        *_commerce(140),
    ]


def _concrete_pump_fields() -> list:
    return [
        *_geo_head(),
        *_equipment_type(CONCRETE_PUMP_TYPES, 5),
        *_brand_model(10),
        *_year(30),
        *_operating_hours(40),
        *_mileage(45),
        *_boom_reach(50),
        *_fuel(60),
        *_condition_block(120, after_accident=True),
        *_commerce(140),
    ]


def _septic_fields() -> list:
    return [
        *_geo_head(),
        *_brand_model(10),
        *_year(30),
        *_mileage(40),
        _field(
            "tank_capacity_l",
            "Объём цистерны",
            CategoryFieldType.number,
            False,
            50,
            {"min": 0, "max": TANK_L_MAX, "unit": "L", "integer": True},
        ),
        *_fuel(60),
        *_condition_block(120, after_accident=True),
        *_commerce(140),
    ]


def _mini_dumper_fields() -> list:
    return [
        *_geo_head(),
        *_brand_model(10),
        *_year(30),
        *_operating_hours(40),
        *_load_capacity(50),
        *_fuel(60),
        *_condition_block(120),
        *_commerce(140),
    ]


def _municipal_fields() -> list:
    return [
        *_geo_head(),
        *_equipment_type(MUNICIPAL_TYPES, 5),
        *_brand_model(10),
        *_year(30),
        *_operating_hours(40),
        *_mileage(45),
        *_fuel(50),
        *_condition_block(120, after_accident=True),
        *_commerce(140),
    ]


def _drilling_fields() -> list:
    return [
        *_geo_head(),
        *_brand_model(10),
        *_year(30),
        *_operating_hours(40),
        _field(
            "drilling_depth_m",
            "Глубина бурения",
            CategoryFieldType.decimal,
            False,
            50,
            {"min": 0, "max": DRILL_M_MAX, "unit": "m"},
        ),
        *_fuel(60),
        *_condition_block(120),
        *_commerce(140),
    ]


def _crushing_fields() -> list:
    return [
        *_geo_head(),
        *_equipment_type(CRUSHING_TYPES, 5),
        *_brand_model(10),
        *_year(30),
        *_operating_hours(40),
        *_fuel(50),
        *_condition_block(120),
        *_commerce(140),
    ]


def _attachment_fields() -> list:
    return [
        *_geo_head(),
        *_equipment_type(ATTACHMENT_TYPES, 5),
        *_brand_model(10),
        *_condition_block(40),
        *_commerce(60),
    ]


def _other_special_fields() -> list:
    return [
        *_geo_head(),
        *_equipment_type(OTHER_SPECIAL_TYPES, 5),
        *_brand_model(10),
        *_year(30),
        *_operating_hours(40),
        *_fuel(50),
        *_condition_block(120),
        *_commerce(140),
    ]


SPECIAL_CORE_FIELDS_BY_SLUG: dict[str, list] = {
    "transport-special-equipment-ekskavatory": _excavator_fields(),
    "transport-special-equipment-pogruzchiki": _loader_fields(),
    "transport-special-equipment-vilochnye-pogruzchiki": _forklift_fields(),
    "transport-special-equipment-avtokrany": _autocrane_fields(),
    "transport-special-equipment-avtovyshki": _aerial_fields(),
    "transport-special-equipment-buldozery": _bulldozer_fields(),
    "transport-special-equipment-katki": _roller_fields(),
    "transport-special-equipment-greydery": _grader_fields(),
    "transport-special-equipment-manipulyatory": _manipulator_fields(),
    "transport-special-equipment-avtobetonomehalki": _concrete_mixer_fields(),
    "transport-special-equipment-betononasosy": _concrete_pump_fields(),
    "transport-special-equipment-assenizatory": _septic_fields(),
    "transport-special-equipment-mini-dumper": _mini_dumper_fields(),
    "transport-special-equipment-kommunalnaya-tehnika": _municipal_fields(),
    "transport-special-equipment-burovaya-tehnika": _drilling_fields(),
    "transport-special-equipment-drobilno-sortirovochnaya-tehnika": _crushing_fields(),
    "transport-special-equipment-navesnoe-i-rabochee-oborudovanie": _attachment_fields(),
    "transport-special-equipment-drugaya-spetstehnika": _other_special_fields(),
}


def _common_search_head(sort: int = 10) -> list:
    return [
        _filt("brand", "Марка", CategoryFilterType.select, sort, {}),
        _filt("model", "Модель", CategoryFilterType.select, sort + 10, {}),
        _filt("price", "Цена", CategoryFilterType.range, sort + 20, {"unit": "KGS"}),
        _filt("year", "Год выпуска", CategoryFilterType.range, sort + 30, {}),
        _filt("region", "Регион", CategoryFilterType.select, sort + 40, {}),
        _filt("city", "Город", CategoryFilterType.select, sort + 50, {}),
    ]


def _condition_seller_photo_sort(sort: int) -> list:
    """Condition + seller + sort. Photo is publication-required — no Search UI filter."""
    return [
        _filt(
            "condition",
            "Состояние",
            CategoryFilterType.multi_select,
            sort,
            _opt_cfg(*CONDITION_V2_CHOICES),
        ),
        _filt(
            "seller_type",
            "Кто продаёт",
            CategoryFilterType.multi_select,
            sort + 40,
            _opt_cfg(*_SELLER),
        ),
        _filt(
            "sort",
            "Сортировка",
            CategoryFilterType.select,
            sort + 60,
            {
                "options": [
                    {"value": "newest", "label": "Сначала новые"},
                    {"value": "price_asc", "label": "Сначала дешевле"},
                    {"value": "price_desc", "label": "Сначала дороже"},
                ]
            },
        ),
    ]


def _machine_search(
    *,
    equipment_types: tuple[str, ...] | None = None,
    hours: bool = True,
    fuel: bool = True,
    load_from: bool = False,
    lift_from: bool = False,
    dig_from: bool = False,
    bucket: bool = False,
    boom_from: bool = False,
    weight: bool = False,
    mileage: bool = False,
    manipulator_brand: bool = False,
) -> list:
    rows = [*_common_search_head(10)]
    n = 70
    if equipment_types:
        rows.append(
            _filt(
                "equipment_type",
                "Тип техники",
                CategoryFilterType.multi_select,
                n,
                _opt_cfg(*equipment_types),
            )
        )
        n += 5
    if manipulator_brand:
        rows.append(
            _filt(
                "manipulator_brand",
                "Марка манипулятора",
                CategoryFilterType.multi_select,
                n,
                _opt_cfg(*MANIPULATOR_CRANE_BRANDS),
            )
        )
        n += 5
    if load_from:
        rows.append(
            _filt(
                "load_capacity_kg",
                "Грузоподъёмность от",
                CategoryFilterType.range,
                n,
                {"unit": "kg", "mode": "min"},
            )
        )
        n += 5
    if lift_from:
        rows.append(
            _filt(
                "lift_height_m",
                "Высота подъёма от",
                CategoryFilterType.range,
                n,
                {"unit": "m", "mode": "min"},
            )
        )
        n += 5
    if dig_from:
        rows.append(
            _filt(
                "digging_depth_m",
                "Глубина копания от",
                CategoryFilterType.range,
                n,
                {"unit": "m", "mode": "min"},
            )
        )
        n += 5
    if bucket:
        rows.append(
            _filt(
                "bucket_capacity_m3",
                "Объём ковша от",
                CategoryFilterType.range,
                n,
                {"unit": "m3", "mode": "min"},
            )
        )
        n += 5
    if boom_from:
        rows.append(
            _filt(
                "boom_reach_m",
                "Вылет стрелы от",
                CategoryFilterType.range,
                n,
                {"unit": "m", "mode": "min"},
            )
        )
        n += 5
    if weight:
        rows.append(
            _filt(
                "weight_kg",
                "Масса до",
                CategoryFilterType.range,
                n,
                {"unit": "kg", "mode": "max"},
            )
        )
        n += 5
    if hours:
        rows.append(
            _filt(
                "operating_hours",
                "Моточасы до",
                CategoryFilterType.range,
                n,
                {"unit": "ч", "mode": "max"},
            )
        )
        n += 5
    if mileage:
        rows.append(
            _filt(
                "mileage",
                "Пробег до",
                CategoryFilterType.range,
                n,
                {"unit": "км", "mode": "max"},
            )
        )
        n += 5
    if fuel:
        rows.append(
            _filt(
                "fuel",
                "Топливо",
                CategoryFilterType.multi_select,
                n,
                _opt_cfg(*_FUEL),
            )
        )
        n += 5
    rows.extend(_condition_seller_photo_sort(n + 10))
    return rows


def _attachment_search() -> list:
    return [
        _filt(
            "equipment_type",
            "Тип техники",
            CategoryFilterType.multi_select,
            10,
            _opt_cfg(*ATTACHMENT_TYPES),
        ),
        _filt("brand", "Марка", CategoryFilterType.select, 20, {}),
        _filt("model", "Модель", CategoryFilterType.select, 30, {}),
        _filt("price", "Цена", CategoryFilterType.range, 40, {"unit": "KGS"}),
        _filt("region", "Регион", CategoryFilterType.select, 50, {}),
        _filt("city", "Город", CategoryFilterType.select, 60, {}),
        *_condition_seller_photo_sort(70),
    ]


SPECIAL_SEARCH_FILTERS_BY_SLUG: dict[str, list] = {
    "transport-special-equipment-ekskavatory": _machine_search(
        equipment_types=EXCAVATOR_TYPES,
        dig_from=True,
        bucket=True,
        weight=True,
    ),
    "transport-special-equipment-pogruzchiki": _machine_search(
        equipment_types=LOADER_TYPES,
        load_from=True,
        lift_from=True,
        bucket=True,
    ),
    "transport-special-equipment-vilochnye-pogruzchiki": _machine_search(
        load_from=True,
        lift_from=True,
        fuel=True,
    ),
    "transport-special-equipment-avtokrany": _machine_search(
        load_from=True,
        boom_from=True,
        mileage=True,
        weight=True,
    ),
    "transport-special-equipment-avtovyshki": _machine_search(
        equipment_types=AERIAL_TYPES,
        lift_from=True,
        load_from=True,
        mileage=True,
    ),
    "transport-special-equipment-buldozery": _machine_search(weight=True),
    "transport-special-equipment-katki": _machine_search(weight=True),
    "transport-special-equipment-greydery": _machine_search(weight=True),
    "transport-special-equipment-manipulyatory": _machine_search(
        load_from=True,
        boom_from=True,
        mileage=True,
        manipulator_brand=True,
    ),
    "transport-special-equipment-avtobetonomehalki": _machine_search(mileage=True),
    "transport-special-equipment-betononasosy": _machine_search(
        equipment_types=CONCRETE_PUMP_TYPES,
        boom_from=True,
        mileage=True,
    ),
    "transport-special-equipment-assenizatory": _machine_search(
        hours=False,
        mileage=True,
    ),
    "transport-special-equipment-mini-dumper": _machine_search(load_from=True),
    "transport-special-equipment-kommunalnaya-tehnika": _machine_search(
        equipment_types=MUNICIPAL_TYPES,
        mileage=True,
    ),
    "transport-special-equipment-burovaya-tehnika": _machine_search(),
    "transport-special-equipment-drobilno-sortirovochnaya-tehnika": _machine_search(
        equipment_types=CRUSHING_TYPES,
    ),
    "transport-special-equipment-navesnoe-i-rabochee-oborudovanie": _attachment_search(),
    "transport-special-equipment-drugaya-spetstehnika": _machine_search(
        equipment_types=OTHER_SPECIAL_TYPES,
    ),
}


def special_other_brands() -> list[tuple[str, str, str | None, str]]:
    out: list[tuple[str, str, str | None, str]] = []
    for vt in SPECIAL_OTHER_BRAND_TYPES:
        slug = f"other-{vt.replace('_', '-')}"
        out.append((slug, "Другая марка", None, vt))
    return out


def special_other_models() -> dict[str, list[tuple[str, str]]]:
    return {
        f"other-{vt.replace('_', '-')}": [("other-model", "Другая модель")]
        for vt in SPECIAL_OTHER_BRAND_TYPES
    }
