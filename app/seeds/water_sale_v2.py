# -*- coding: utf-8 -*-
"""Transport → Водный транспорт V2 — leaf Create/Search SoT.

Parent ``transport-watercraft`` is picker-only (not live Create SoT).
Boat Motor reuses existing category 817 ``transport-watercraft-lodochnye-motory``.
Kayak/Canoe/SUP/Water Bike → future Sport (not Water leaves).
Inflatable → ``boat_type`` on Boats (legacy inflatable leaf stays inactive).
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

WATER_PARENT_SLUG = "transport-watercraft"

WATER_LEAF_SLUGS: tuple[str, ...] = (
    "transport-watercraft-lodki",
    "transport-watercraft-katera",
    "transport-watercraft-yahty",
    "transport-watercraft-gidrotsikly",
    "transport-watercraft-lodochnye-motory",
    "transport-watercraft-drugoy-vodnyy-transport",
)

WATER_LEAF_LABELS: dict[str, str] = {
    "transport-watercraft-lodki": "Лодки",
    "transport-watercraft-katera": "Катера",
    "transport-watercraft-yahty": "Яхты",
    "transport-watercraft-gidrotsikly": "Гидроциклы",
    "transport-watercraft-lodochnye-motory": "Лодочные моторы",
    "transport-watercraft-drugoy-vodnyy-transport": "Другой водный транспорт",
}

WATER_LEAF_SORT: dict[str, int] = {
    "transport-watercraft-lodki": 10,
    "transport-watercraft-katera": 20,
    "transport-watercraft-yahty": 30,
    "transport-watercraft-gidrotsikly": 40,
    "transport-watercraft-lodochnye-motory": 45,
    "transport-watercraft-drugoy-vodnyy-transport": 50,
}

WATER_LEAF_VEHICLE_TYPE: dict[str, str] = {
    "transport-watercraft-lodki": "boat",
    "transport-watercraft-katera": "motorboat",
    "transport-watercraft-yahty": "yacht",
    "transport-watercraft-gidrotsikly": "jet_ski",
    "transport-watercraft-lodochnye-motory": "boat_motor",
    "transport-watercraft-drugoy-vodnyy-transport": "other_watercraft",
}

WATER_INACTIVE_LEGACY_SLUGS: tuple[str, ...] = (
    "transport-water",
    "transport-watercraft-naduvnye-lodki",
    "transport-watercraft-pritsepy-dlya-vodnogo-transporta",
    "transport-watercraft-zapchasti-i-komplektuyuschie",
    "transport-watercraft-aksessuary-i-oborudovanie",
    "transport-watercraft-remont-i-obsluzhivanie",
)

# Jet Ski model-as-brand pollution (disable; models fold into real manufacturers).
JET_SKI_DISABLE_BRAND_SLUGS: tuple[str, ...] = (
    "spark-brp",
    "gti-brp",
    "ultra-kawasaki",
)

# Engine manufacturers wrongly seeded as other_watercraft craft brands.
OTHER_WATERCRAFT_DISABLE_BRAND_SLUGS: tuple[str, ...] = (
    "mercury-other",
    "volvo-penta-other",
)

WATER_LEAF_ALIASES: dict[str, str] = {
    "лодка": "transport-watercraft-lodki",
    "моторная лодка": "transport-watercraft-lodki",
    "надувная лодка": "transport-watercraft-lodki",
    "катер": "transport-watercraft-katera",
    "яхта": "transport-watercraft-yahty",
    "гидроцикл": "transport-watercraft-gidrotsikly",
    "водный мотоцикл": "transport-watercraft-gidrotsikly",
    "лодочный мотор": "transport-watercraft-lodochnye-motory",
    "подвесной мотор": "transport-watercraft-lodochnye-motory",
    "outboard": "transport-watercraft-lodochnye-motory",
}

WATER_PARENT_ALIASES: dict[str, str] = {
    "водный транспорт": WATER_PARENT_SLUG,
    "водная техника": WATER_PARENT_SLUG,
}

_SELLER = ("Частное лицо", "Магазин")
_FUEL = ("Бензин", "Дизель", "Электро", "Другое")
_BOAT_TYPES = ("Моторная", "Надувная", "Гребная", "Другая")
_HULL = ("ПВХ", "Алюминий", "Стеклопластик", "Дерево", "Другое")
_ENGINE_TYPES = ("Подвесной", "Стационарный", "Другой")
_STROKE = ("2-тактный", "4-тактный")

WATER_OTHER_BRAND_TYPES: tuple[str, ...] = (
    "boat",
    "motorboat",
    "yacht",
    "jet_ski",
    "boat_motor",
    "other_watercraft",
)

WATER_YEAR_MIN = 1950
LENGTH_M_MAX = 100
PASSENGER_MAX = 100
ENGINE_HP_MAX = 5000
HOURS_MAX = 100_000


def _choices(*labels: str) -> dict[str, Any]:
    items = [{"value": x, "label": x} for x in labels]
    return {"choices": items, "values": items}


def _opt_cfg(*labels: str, **extra: Any) -> dict[str, Any]:
    cfg: dict[str, Any] = {
        "options": [{"value": o, "label": o} for o in labels],
    }
    cfg.update(extra)
    return cfg


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


def _geo_head() -> list:
    return [
        _field("region", "Регион", CategoryFieldType.string, True, 0),
        _field("city", "Город", CategoryFieldType.city, True, 1),
    ]


def _brand_model(sort: int = 10) -> list:
    return [
        _field("brand", "Марка", CategoryFieldType.brand, False, sort),
        _field("model", "Модель", CategoryFieldType.model, False, sort + 5),
    ]


def _year(sort: int) -> list:
    return [
        _field(
            "year",
            "Год выпуска",
            CategoryFieldType.year,
            False,
            sort,
            {"min": WATER_YEAR_MIN, "max_offset_years": 1},
        ),
    ]


def _condition_block(sort: int) -> list:
    return [
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


def _hull(sort: int) -> list:
    return [
        _field(
            "hull_material",
            "Материал корпуса",
            CategoryFieldType.enum,
            False,
            sort,
            _choices(*_HULL),
        ),
    ]


def _length(sort: int) -> list:
    return [
        _field(
            "length_m",
            "Длина",
            CategoryFieldType.decimal,
            False,
            sort,
            {"min": 0, "max": LENGTH_M_MAX, "unit": "m"},
            "Длина в метрах",
        ),
    ]


def _passengers(sort: int) -> list:
    return [
        _field(
            "passenger_capacity",
            "Количество мест",
            CategoryFieldType.number,
            False,
            sort,
            {"min": 1, "max": PASSENGER_MAX, "unit": "мест", "integer": True},
        ),
    ]


def _power_hp(
    sort: int,
    *,
    depends_on_engine_included: bool = False,
) -> list:
    opts: dict[str, Any] = {
        "min": 0,
        "max": ENGINE_HP_MAX,
        "unit": "л.с.",
        "integer": True,
    }
    if depends_on_engine_included:
        opts["depends_on"] = {
            "field": "engine_included",
            "values": ["Да"],
        }
    return [
        _field(
            "engine_power_hp",
            "Мощность двигателя",
            CategoryFieldType.number,
            False,
            sort,
            opts,
            "Мощность в лошадиных силах",
        ),
    ]


def _hours(
    sort: int,
    *,
    depends_on_engine_included: bool = False,
) -> list:
    opts: dict[str, Any] = {
        "min": 0,
        "max": HOURS_MAX,
        "unit": "ч",
        "integer": True,
    }
    if depends_on_engine_included:
        opts["depends_on"] = {
            "field": "engine_included",
            "values": ["Да"],
        }
    return [
        _field(
            "operating_hours",
            "Моточасы",
            CategoryFieldType.number,
            False,
            sort,
            opts,
            "Наработка в моточасах",
        ),
    ]


def _fuel(
    sort: int,
    *,
    depends_on_engine_included: bool = False,
) -> list:
    opts = _choices(*_FUEL)
    if depends_on_engine_included:
        opts = {
            **opts,
            "depends_on": {
                "field": "engine_included",
                "values": ["Да"],
            },
        }
    return [
        _field(
            "fuel",
            "Топливо",
            CategoryFieldType.enum,
            False,
            sort,
            opts,
        ),
    ]


def _boat_fields() -> list:
    return [
        *_geo_head(),
        _field(
            "boat_type",
            "Тип лодки",
            CategoryFieldType.enum,
            False,
            8,
            _choices(*_BOAT_TYPES),
        ),
        *_brand_model(10),
        *_year(25),
        *_hull(30),
        *_length(35),
        *_passengers(40),
        _field(
            "engine_included",
            "Мотор в комплекте",
            CategoryFieldType.enum,
            False,
            45,
            _choices(*YES_NO_CHOICES),
        ),
        *_power_hp(50, depends_on_engine_included=True),
        *_hours(55, depends_on_engine_included=True),
        *_fuel(60, depends_on_engine_included=True),
        *_condition_block(100),
        *_commerce(120),
    ]


def _motorboat_fields() -> list:
    return [
        *_geo_head(),
        *_brand_model(10),
        *_year(25),
        *_hull(30),
        *_length(35),
        *_passengers(40),
        *_power_hp(50),
        *_hours(55),
        *_fuel(60),
        *_condition_block(100),
        *_commerce(120),
    ]


def _yacht_fields() -> list:
    return [
        *_geo_head(),
        *_brand_model(10),
        *_year(25),
        *_hull(30),
        *_length(35),
        *_passengers(40),
        *_power_hp(50),
        *_hours(55),
        *_fuel(60),
        *_condition_block(100),
        *_commerce(120),
    ]


def _jet_ski_fields() -> list:
    return [
        *_geo_head(),
        *_brand_model(10),
        *_year(25),
        *_passengers(40),
        *_power_hp(50),
        *_hours(55),
        *_fuel(60),
        *_condition_block(100),
        *_commerce(120),
    ]


def _boat_motor_fields() -> list:
    return [
        *_geo_head(),
        *_brand_model(10),
        *_year(25),
        *_power_hp(40),
        *_hours(45),
        _field(
            "engine_type",
            "Тип мотора",
            CategoryFieldType.enum,
            False,
            50,
            _choices(*_ENGINE_TYPES),
        ),
        _field(
            "stroke",
            "Тактность",
            CategoryFieldType.enum,
            False,
            55,
            _choices(*_STROKE),
        ),
        *_fuel(60),
        *_condition_block(100),
        *_commerce(120),
    ]


def _other_fields() -> list:
    return [
        *_geo_head(),
        *_brand_model(10),
        *_year(25),
        *_hull(30),
        *_length(35),
        *_passengers(40),
        *_power_hp(50),
        *_hours(55),
        *_condition_block(100),
        *_commerce(120),
    ]


WATER_CORE_FIELDS_BY_SLUG: dict[str, list] = {
    "transport-watercraft-lodki": _boat_fields(),
    "transport-watercraft-katera": _motorboat_fields(),
    "transport-watercraft-yahty": _yacht_fields(),
    "transport-watercraft-gidrotsikly": _jet_ski_fields(),
    "transport-watercraft-lodochnye-motory": _boat_motor_fields(),
    "transport-watercraft-drugoy-vodnyy-transport": _other_fields(),
}


def _common_search_head(*, year: bool = True, sort: int = 10) -> list:
    rows = [
        _filt("brand", "Марка", CategoryFilterType.select, sort, {}),
        _filt("model", "Модель", CategoryFilterType.select, sort + 10, {}),
        _filt("price", "Цена", CategoryFilterType.range, sort + 20, {"unit": "KGS"}),
    ]
    if year:
        rows.append(
            _filt("year", "Год выпуска", CategoryFilterType.range, sort + 30, {})
        )
    rows.extend(
        [
            _filt("region", "Регион", CategoryFilterType.select, sort + 40, {}),
            _filt("city", "Город", CategoryFilterType.select, sort + 50, {}),
        ]
    )
    return rows


def _condition_seller_sort(sort: int) -> list:
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
            sort + 10,
            _opt_cfg(*_SELLER),
        ),
        _filt(
            "sort",
            "Сортировка",
            CategoryFilterType.select,
            sort + 20,
            {
                "options": [
                    {"value": "newest", "label": "Сначала новые"},
                    {"value": "price_asc", "label": "Сначала дешевле"},
                    {"value": "price_desc", "label": "Сначала дороже"},
                ]
            },
        ),
    ]


def _water_search(
    *,
    year: bool = True,
    boat_type: bool = False,
    hull: bool = False,
    length: bool = False,
    passengers: bool = False,
    power_from: bool = False,
    hours_max: bool = False,
    engine_type: bool = False,
    stroke: bool = False,
    fuel: bool = False,
) -> list:
    rows = [*_common_search_head(year=year)]
    adv = 200
    if boat_type:
        rows.append(
            _filt(
                "boat_type",
                "Тип лодки",
                CategoryFilterType.multi_select,
                15,
                _opt_cfg(*_BOAT_TYPES),
            )
        )
    if hull:
        rows.append(
            _filt(
                "hull_material",
                "Материал корпуса",
                CategoryFilterType.multi_select,
                adv,
                _opt_cfg(*_HULL),
            )
        )
        adv += 10
    if length:
        rows.append(
            _filt(
                "length_m",
                "Длина",
                CategoryFilterType.range,
                adv,
                {"unit": "m", "mode": "range"},
            )
        )
        adv += 10
    if passengers:
        rows.append(
            _filt(
                "passenger_capacity",
                "Количество мест",
                CategoryFilterType.range,
                adv,
                {"unit": "мест", "mode": "min", "integer": True},
            )
        )
        adv += 10
    if power_from:
        rows.append(
            _filt(
                "engine_power_hp",
                "Мощность двигателя",
                CategoryFilterType.range,
                adv,
                {"unit": "л.с.", "mode": "min", "integer": True},
            )
        )
        adv += 10
    if hours_max:
        rows.append(
            _filt(
                "operating_hours",
                "Моточасы",
                CategoryFilterType.range,
                adv,
                {"unit": "ч", "mode": "max", "integer": True},
            )
        )
        adv += 10
    if engine_type:
        rows.append(
            _filt(
                "engine_type",
                "Тип мотора",
                CategoryFilterType.multi_select,
                adv,
                _opt_cfg(*_ENGINE_TYPES),
            )
        )
        adv += 10
    if stroke:
        rows.append(
            _filt(
                "stroke",
                "Тактность",
                CategoryFilterType.multi_select,
                adv,
                _opt_cfg(*_STROKE),
            )
        )
        adv += 10
    if fuel:
        rows.append(
            _filt(
                "fuel",
                "Топливо",
                CategoryFilterType.multi_select,
                adv,
                _opt_cfg(*_FUEL),
            )
        )
        adv += 10
    rows.extend(_condition_seller_sort(300))
    return rows


WATER_SEARCH_FILTERS_BY_SLUG: dict[str, list] = {
    "transport-watercraft-lodki": _water_search(
        year=True,
        boat_type=True,
        hull=True,
        length=True,
        passengers=True,
        power_from=True,
    ),
    "transport-watercraft-katera": _water_search(
        year=True,
        hull=True,
        length=True,
        passengers=True,
        power_from=True,
        hours_max=True,
    ),
    "transport-watercraft-yahty": _water_search(
        year=True,
        length=True,
        passengers=True,
        power_from=True,
        hours_max=True,
    ),
    "transport-watercraft-gidrotsikly": _water_search(
        year=True,
        passengers=True,
        power_from=True,
        hours_max=True,
    ),
    "transport-watercraft-lodochnye-motory": _water_search(
        year=True,
        power_from=True,
        hours_max=True,
        engine_type=True,
        stroke=True,
        fuel=True,
    ),
    "transport-watercraft-drugoy-vodnyy-transport": _water_search(
        year=True,
        hull=True,
        length=True,
        passengers=True,
    ),
}


def water_other_brands() -> list[tuple[str, str, str | None, str]]:
    out: list[tuple[str, str, str | None, str]] = []
    for vt in WATER_OTHER_BRAND_TYPES:
        slug = f"other-{vt.replace('_', '-')}"
        out.append((slug, "Другая марка", None, vt))
    return out


def water_other_models() -> dict[str, list[tuple[str, str]]]:
    return {
        f"other-{vt.replace('_', '-')}": [("other-model", "Другая модель")]
        for vt in WATER_OTHER_BRAND_TYPES
    }


# Clean typed Boat Motor sale catalog (not parts watercraft / not car Mercury).
BOAT_MOTOR_BRANDS: list[tuple[str, str, str | None, VehicleType]] = [
    ("yamaha-boat-motor", "Yamaha", "Japan", VehicleType.boat_motor),
    ("mercury-boat-motor", "Mercury", "USA", VehicleType.boat_motor),
    ("honda-boat-motor", "Honda", "Japan", VehicleType.boat_motor),
    ("suzuki-boat-motor", "Suzuki", "Japan", VehicleType.boat_motor),
    ("tohatsu-boat-motor", "Tohatsu", "Japan", VehicleType.boat_motor),
    ("hidea-boat-motor", "Hidea", "China", VehicleType.boat_motor),
    ("parsun-boat-motor", "Parsun", "China", VehicleType.boat_motor),
]

BOAT_MOTOR_MODELS: dict[str, list[tuple[str, str]]] = {
    "yamaha-boat-motor": [
        ("f60", "F60"),
        ("f115", "F115"),
        ("f150", "F150"),
    ],
    "mercury-boat-motor": [
        ("60-efi", "60 EFI"),
        ("115-efi", "115 EFI"),
        ("150-pro-xs", "150 Pro XS"),
    ],
    "honda-boat-motor": [
        ("bf60", "BF60"),
        ("bf90", "BF90"),
        ("bf115", "BF115"),
    ],
    "suzuki-boat-motor": [
        ("df60", "DF60"),
        ("df115", "DF115"),
        ("df140", "DF140"),
    ],
    "tohatsu-boat-motor": [
        ("mfs9-8", "MFS9.8"),
        ("mfs15", "MFS15"),
        ("mfs30", "MFS30"),
    ],
    "hidea-boat-motor": [
        ("hdf6", "HDF6"),
        ("hdf15", "HDF15"),
        ("hdf40", "HDF40"),
    ],
    "parsun-boat-motor": [
        ("f9-8", "F9.8"),
        ("f15", "F15"),
        ("f40", "F40"),
    ],
}


# Jet Ski models after folding Spark/GTI/Ultra families under manufacturers.
JET_SKI_CLEAN_MODELS: dict[str, list[tuple[str, str]]] = {
    "sea-doo": [
        ("gti", "GTI"),
        ("gtx", "GTX"),
        ("rxp-x", "RXP-X"),
        ("rxt-x", "RXT-X"),
        ("spark", "Spark"),
        ("spark-2up", "Spark 2UP"),
        ("spark-3up", "Spark 3UP"),
        ("spark-trixx", "Spark Trixx"),
        ("gti-130", "GTI 130"),
        ("gti-170", "GTI 170"),
        ("gti-se", "GTI SE"),
    ],
    "kawasaki-jetski": [
        ("stx-160", "STX 160"),
        ("ultra-310", "Ultra 310"),
        ("sx-r", "SX-R"),
        ("ultra-310lx", "Ultra 310LX"),
        ("ultra-310x", "Ultra 310X"),
    ],
}
