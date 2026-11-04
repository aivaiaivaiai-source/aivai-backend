# -*- coding: utf-8 -*-
"""Transport → Автобусы / Микроавтобусы / Автодома V2 — leaf Create/Search SoT.

Parent ``transport-buses-microbuses-motorhomes`` is picker-only (not live Create SoT).
Cargo vans stay under Cargo; residential trailers stay under Trailers.
"""
from __future__ import annotations

from typing import Any

from app.models.category_enums import CategoryFieldType, CategoryFilterType
from app.seeds.car_sale_v2 import (
    CONDITION_V2_CHOICES,
    CONTACT_METHOD_CHOICES,
    EXCHANGE_CHOICES,
    INSTALLMENT_CHOICES,
    NEGOTIABLE_CHOICES,
    VEHICLE_COLOR_CHOICES,
    YES_NO_CHOICES,
    _engine_volume_options,
)

BUS_PARENT_SLUG = "transport-buses-microbuses-motorhomes"

BUS_LEAF_SLUGS: tuple[str, ...] = (
    "transport-commercial-avtobusy",
    "transport-commercial-mikroavtobusy",
    "transport-buses-avtodoma",
)

BUS_LEAF_LABELS: dict[str, str] = {
    "transport-commercial-avtobusy": "Автобусы",
    "transport-commercial-mikroavtobusy": "Микроавтобусы",
    "transport-buses-avtodoma": "Автодома",
}

BUS_LEAF_SORT: dict[str, int] = {
    "transport-commercial-avtobusy": 10,
    "transport-commercial-mikroavtobusy": 20,
    "transport-buses-avtodoma": 30,
}

BUS_LEAF_VEHICLE_TYPE: dict[str, str] = {
    "transport-commercial-avtobusy": "bus",
    "transport-commercial-mikroavtobusy": "microbus",
    "transport-buses-avtodoma": "motorhome",
}

# Alias normalized → leaf slug (not parent 1201).
BUS_LEAF_ALIASES: dict[str, str] = {
    "автобус": "transport-commercial-avtobusy",
    "микроавтобус": "transport-commercial-mikroavtobusy",
    "автодом": "transport-buses-avtodoma",
}

# Cargo-only / truck models wrongly living under microbus — disable in live picker.
MICROBUS_CARGO_MODEL_KEYS: frozenset[tuple[str, str]] = frozenset(
    {
        ("daewoo-microbus", "labo"),
        ("daewoo-microbus", "nexia-van"),
        ("isuzu-microbus", "elf"),
        ("isuzu-microbus", "nqr"),
        ("uaz-microbus", "3741"),
    }
)

BUS_FORBIDDEN_FIELD_KEYS: frozenset[str] = frozenset(
    {
        "passenger_cargo",
        "standing_places",
        "total_capacity",
        "bus_type",
        "motorhome_type",
        "base_vehicle",
    }
)

_SELLER = ("Частное лицо", "Компания", "Дилер")
_STEERING = ("Левый руль", "Правый руль")
_TRANSMISSION = ("Механика", "Автомат")
_DRIVE = ("Передний", "Задний", "Полный")
_FUEL = (
    "Бензин",
    "Дизель",
    "Газ",
    "Бензин + Газ",
    "Гибрид",
    "Электро",
)
_DOCUMENTS = ("Есть", "Нет")
MOTORHOME_AMENITIES: tuple[str, ...] = (
    "Кухня",
    "Туалет",
    "Душ",
    "Холодильник",
    "Отопление",
    "Кондиционер",
    "Солнечная панель",
)

BUS_YEAR_MIN = 1970
SEATS_MIN = 2
SEATS_MAX = 120
SLEEPING_MIN = 1
SLEEPING_MAX = 12
TRAVEL_SEATS_MIN = 1
TRAVEL_SEATS_MAX = 20
MILEAGE_MAX = 3_000_000

# «Другая марка» rows for typed catalogs.
BUS_OTHER_BRANDS: list[tuple[str, str, str | None, str]] = [
    ("other-bus", "Другая марка", None, "bus"),
    ("other-microbus", "Другая марка", None, "microbus"),
    ("other-motorhome", "Другая марка", None, "motorhome"),
]
BUS_OTHER_MODELS: dict[str, list[tuple[str, str]]] = {
    "other-bus": [("other-model", "Другая модель")],
    "other-microbus": [("other-model", "Другая модель")],
    "other-motorhome": [("other-model", "Другая модель")],
}


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


def _brand_model() -> list:
    return [
        _field("brand", "Марка", CategoryFieldType.brand, False, 10),
        _field("model", "Модель", CategoryFieldType.model, False, 20),
    ]


def _year(sort: int) -> list:
    return [
        _field(
            "year",
            "Год выпуска",
            CategoryFieldType.year,
            False,
            sort,
            {"min": BUS_YEAR_MIN, "max_offset_years": 1},
        ),
    ]


def _seats(sort: int) -> list:
    return [
        _field(
            "seats",
            "Количество мест",
            CategoryFieldType.number,
            False,
            sort,
            {"min": SEATS_MIN, "max": SEATS_MAX, "unit": "мест", "integer": True},
            "Количество пассажирских мест",
        ),
    ]


def _vehicle_tech(sort: int, *, engine: bool = True) -> list:
    rows: list = [
        _field(
            "mileage",
            "Пробег, км",
            CategoryFieldType.number,
            False,
            sort,
            {"min": 0, "max": MILEAGE_MAX},
            "Пробег в километрах",
        ),
        _field(
            "fuel",
            "Топливо",
            CategoryFieldType.enum,
            False,
            sort + 10,
            _choices(*_FUEL),
        ),
        _field(
            "transmission",
            "Коробка передач",
            CategoryFieldType.enum,
            False,
            sort + 20,
            _choices(*_TRANSMISSION),
        ),
        _field(
            "drive",
            "Привод",
            CategoryFieldType.enum,
            False,
            sort + 30,
            _choices(*_DRIVE),
        ),
        _field(
            "steering_side",
            "Руль",
            CategoryFieldType.enum,
            False,
            sort + 40,
            _choices(*_STEERING),
        ),
    ]
    n = sort + 50
    if engine:
        rows.append(
            _field(
                "engine_volume",
                "Объём двигателя",
                CategoryFieldType.decimal,
                False,
                n,
                _engine_volume_options(),
                "Объём в литрах (шаг 0.1)",
            )
        )
        n += 10
    rows.append(
        _field(
            "color",
            "Цвет",
            CategoryFieldType.enum,
            False,
            n,
            _choices(*VEHICLE_COLOR_CHOICES),
        )
    )
    return rows


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
        _field(
            "after_accident",
            "После ДТП",
            CategoryFieldType.enum,
            False,
            sort + 10,
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


def _motorhome_places(sort: int) -> list:
    return [
        _field(
            "sleeping_places",
            "Спальных мест",
            CategoryFieldType.number,
            False,
            sort,
            {
                "min": SLEEPING_MIN,
                "max": SLEEPING_MAX,
                "unit": "мест",
                "integer": True,
            },
            "Количество спальных мест",
        ),
        _field(
            "travel_seats",
            "Мест для поездки",
            CategoryFieldType.number,
            False,
            sort + 10,
            {
                "min": TRAVEL_SEATS_MIN,
                "max": TRAVEL_SEATS_MAX,
                "unit": "мест",
                "integer": True,
            },
            "Количество мест для поездки",
        ),
    ]


def _motorhome_amenities(sort: int) -> list:
    return [
        _field(
            "motorhome_amenities",
            "Оснащение",
            CategoryFieldType.multi_select,
            False,
            sort,
            _choices(*MOTORHOME_AMENITIES),
        ),
        _field(
            "documents",
            "Документы",
            CategoryFieldType.enum,
            False,
            sort + 10,
            _choices(*_DOCUMENTS),
        ),
    ]


def _bus_fields() -> list:
    return [
        *_geo_head(),
        *_brand_model(),
        *_year(30),
        *_seats(40),
        *_vehicle_tech(50, engine=True),
        *_condition_block(120),
        *_commerce(140),
    ]


def _minibus_fields() -> list:
    return [
        *_geo_head(),
        *_brand_model(),
        *_year(30),
        *_seats(40),
        *_vehicle_tech(50, engine=True),
        *_condition_block(120),
        *_commerce(140),
    ]


def _motorhome_fields() -> list:
    return [
        *_geo_head(),
        *_brand_model(),
        *_year(30),
        *_motorhome_places(40),
        *_vehicle_tech(60, engine=False),
        *_motorhome_amenities(120),
        *_condition_block(140),
        *_commerce(160),
    ]


BUS_CORE_FIELDS_BY_SLUG: dict[str, list] = {
    "transport-commercial-avtobusy": _bus_fields(),
    "transport-commercial-mikroavtobusy": _minibus_fields(),
    "transport-buses-avtodoma": _motorhome_fields(),
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


def _common_search_tail(
    sort: int,
    *,
    include_drive: bool = True,
) -> list:
    rows = [
        _filt(
            "condition",
            "Состояние",
            CategoryFilterType.multi_select,
            sort,
            _opt_cfg(*CONDITION_V2_CHOICES),
        ),
        _filt(
            "mileage",
            "Пробег до",
            CategoryFilterType.range,
            sort + 10,
            {"unit": "км"},
        ),
        _filt(
            "fuel",
            "Топливо",
            CategoryFilterType.multi_select,
            sort + 20,
            _opt_cfg(*_FUEL),
        ),
        _filt(
            "transmission",
            "Коробка",
            CategoryFilterType.multi_select,
            sort + 30,
            _opt_cfg(*_TRANSMISSION),
        ),
        _filt(
            "steering_side",
            "Руль",
            CategoryFilterType.multi_select,
            sort + 40,
            _opt_cfg(*_STEERING),
        ),
    ]
    n = sort + 50
    if include_drive:
        rows.append(
            _filt(
                "drive",
                "Привод",
                CategoryFilterType.multi_select,
                n,
                _opt_cfg(*_DRIVE),
            )
        )
        n += 10
    rows.extend(
        [
            _filt(
                "seller_type",
                "Кто продаёт",
                CategoryFilterType.multi_select,
                n,
                _opt_cfg(*_SELLER),
            ),
            _filt(
                "sort",
                "Сортировка",
                CategoryFilterType.select,
                n + 20,
                {
                    "options": [
                        {"value": "newest", "label": "Сначала новые"},
                        {"value": "price_asc", "label": "Сначала дешевле"},
                        {"value": "price_desc", "label": "Сначала дороже"},
                    ]
                },
            ),
        ]
    )
    return rows


def _bus_minibus_filters() -> list:
    return [
        *_common_search_head(10),
        _filt(
            "seats",
            "Количество мест от",
            CategoryFilterType.range,
            65,
            {"unit": "мест", "presets": ["8", "12", "18", "20", "30", "40", "50"]},
        ),
        *_common_search_tail(70, include_drive=True),
    ]


def _motorhome_filters() -> list:
    return [
        *_common_search_head(10),
        _filt(
            "sleeping_places",
            "Спальных мест от",
            CategoryFilterType.range,
            65,
            {"unit": "мест", "presets": ["2", "3", "4", "5", "6"]},
        ),
        _filt(
            "travel_seats",
            "Мест для поездки от",
            CategoryFilterType.range,
            68,
            {"unit": "мест", "presets": ["2", "3", "4", "5", "6"]},
        ),
        _filt(
            "motorhome_amenities",
            "Оснащение",
            CategoryFilterType.multi_select,
            72,
            _opt_cfg(*MOTORHOME_AMENITIES),
        ),
        *_common_search_tail(80, include_drive=False),
    ]


BUS_SEARCH_FILTERS_BY_SLUG: dict[str, list] = {
    "transport-commercial-avtobusy": _bus_minibus_filters(),
    "transport-commercial-mikroavtobusy": _bus_minibus_filters(),
    "transport-buses-avtodoma": _motorhome_filters(),
}
