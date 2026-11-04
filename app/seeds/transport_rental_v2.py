# -*- coding: utf-8 -*-
"""Transport → Аренда транспорта V2 — leaf Create/Search SoT.

Parent ``transport-rental`` is picker-only.
Final 9 active leaves. No crew/driver/operator. No condition/negotiable.
Listing.root ``price`` + ``rental_price_unit``. Provider: Частное лицо/Компания/Прокат.
"""
from __future__ import annotations

from typing import Any

from app.models.category_enums import CategoryFieldType, CategoryFilterType
from app.seeds.car_sale_v2 import CONTACT_METHOD_CHOICES

RENTAL_PARENT_SLUG = "transport-rental"
RENTAL_PARENT_ID = 695

# Bus/Microbus consolidation: reuse 845, retire 846.
BUS_COMBINED_ID = 845
BUS_COMBINED_OLD_SLUG = "transport-rental-mikroavtobusy"
BUS_COMBINED_SLUG = "transport-rental-mikroavtobusy-i-avtobusy"
BUS_COMBINED_LABEL = "Микроавтобусы и автобусы"
BUS_RETIRED_ID = 846
BUS_RETIRED_SLUG = "transport-rental-avtobusy"

ELECTRIC_RENTAL_ID = 852
ELECTRIC_RENTAL_SLUG = "transport-rental-elektrotransport"

# New leaves (created if missing).
TRAILER_RENTAL_SLUG = "transport-rental-pritsepy"
FARM_RENTAL_SLUG = "transport-rental-selhoztehnika"
OTHER_RENTAL_SLUG = "transport-rental-drugoy-transport"

RENTAL_LEAF_SLUGS: tuple[str, ...] = (
    "transport-rental-legkovye-avtomobili",
    BUS_COMBINED_SLUG,
    "transport-rental-gruzovoy-transport",
    "transport-rental-spetstehnika",
    "transport-rental-mototehnika",
    TRAILER_RENTAL_SLUG,
    FARM_RENTAL_SLUG,
    "transport-rental-vodnyy-transport",
    OTHER_RENTAL_SLUG,
)

RENTAL_LEAF_LABELS: dict[str, str] = {
    "transport-rental-legkovye-avtomobili": "Легковые автомобили",
    BUS_COMBINED_SLUG: BUS_COMBINED_LABEL,
    "transport-rental-gruzovoy-transport": "Грузовой транспорт",
    "transport-rental-spetstehnika": "Спецтехника",
    "transport-rental-mototehnika": "Мототехника",
    TRAILER_RENTAL_SLUG: "Прицепы",
    FARM_RENTAL_SLUG: "Сельхозтехника",
    "transport-rental-vodnyy-transport": "Водный транспорт",
    OTHER_RENTAL_SLUG: "Другой транспорт",
}

RENTAL_LEAF_SORT: dict[str, int] = {
    "transport-rental-legkovye-avtomobili": 10,
    BUS_COMBINED_SLUG: 20,
    "transport-rental-gruzovoy-transport": 30,
    "transport-rental-spetstehnika": 40,
    "transport-rental-mototehnika": 50,
    TRAILER_RENTAL_SLUG: 60,
    FARM_RENTAL_SLUG: 70,
    "transport-rental-vodnyy-transport": 80,
    OTHER_RENTAL_SLUG: 90,
}

RENTAL_LEAF_EXPECTED_IDS: dict[str, int | None] = {
    "transport-rental-legkovye-avtomobili": 843,
    BUS_COMBINED_SLUG: BUS_COMBINED_ID,
    "transport-rental-gruzovoy-transport": 847,
    "transport-rental-spetstehnika": 849,
    "transport-rental-mototehnika": 850,
    TRAILER_RENTAL_SLUG: None,  # create if missing
    FARM_RENTAL_SLUG: None,
    "transport-rental-vodnyy-transport": 851,
    OTHER_RENTAL_SLUG: None,
}

RENTAL_INACTIVE_LEGACY_SLUGS: tuple[str, ...] = (
    "transport-rental-vnedorozhniki-i-krossovery",
    "transport-rental-kommercheskiy-transport",
    BUS_RETIRED_SLUG,
    ELECTRIC_RENTAL_SLUG,
    "transport-rental-arenda-s-voditelem",
    "transport-rental-dolgosrochnaya-arenda",
    BUS_COMBINED_OLD_SLUG,  # after rename away from this slug
)

RENTAL_REMAP_TARGETS: dict[str, str] = {
    BUS_RETIRED_SLUG: BUS_COMBINED_SLUG,
    BUS_COMBINED_OLD_SLUG: BUS_COMBINED_SLUG,
}

# ---------------------------------------------------------------------------
# Shared options
# ---------------------------------------------------------------------------

RENTAL_PRICE_UNIT_CHOICES: tuple[tuple[str, str], ...] = (
    ("hour", "За час"),
    ("day", "За сутки"),
    ("week", "За неделю"),
    ("month", "За месяц"),
)

RENTAL_PRICE_UNIT_CARD_SUFFIX: dict[str, str] = {
    "hour": "/ час",
    "day": "/ сутки",
    "week": "/ неделю",
    "month": "/ месяц",
}

PROVIDER_TYPE_CHOICES = ("Частное лицо", "Компания", "Прокат")

DEPOSIT_REQUIRED_CHOICES = ("Без залога", "Есть залог")

_TRANSMISSION = ("Механика", "Автомат", "Робот", "Вариатор")
_FUEL = ("Бензин", "Дизель", "Газ", "Гибрид", "Электро")

BUS_TYPE_CHOICES = ("Микроавтобус", "Автобус")
BUS_TYPE_TO_VEHICLE: dict[str, str] = {
    "Микроавтобус": "microbus",
    "Автобус": "bus",
}

CARGO_TYPE_CHOICES = (
    "Самосвал",
    "Тягач",
    "Бортовой грузовик",
    "Фургон",
    "Рефрижератор",
    "Легкий грузовой",
    "Цистерна",
    "Другой",
)
CARGO_TYPE_TO_VEHICLE: dict[str, str] = {
    "Самосвал": "dump_truck",
    "Тягач": "tractor_unit",
    "Бортовой грузовик": "flatbed_truck",
    "Фургон": "box_truck",
    "Рефрижератор": "refrigerated_truck",
    "Легкий грузовой": "light_truck",
    "Цистерна": "tanker_truck",
    "Другой": "other_truck",
}

SPECIAL_TYPE_CHOICES = (
    "Экскаватор",
    "Погрузчик",
    "Вилочный погрузчик",
    "Автокран",
    "Автовышка",
    "Бульдозер",
    "Каток",
    "Грейдер",
    "Манипулятор",
    "Автобетономешалка",
    "Бетононасос",
    "Ассенизатор",
    "Мини-думпер",
    "Коммунальная и дорожная техника",
    "Буровая техника",
    "Дробильно-сортировочная техника",
    "Навесное и рабочее оборудование",
    "Другая спецтехника",
)
SPECIAL_TYPE_TO_VEHICLE: dict[str, str] = {
    "Экскаватор": "excavator",
    "Погрузчик": "loader",
    "Вилочный погрузчик": "forklift",
    "Автокран": "truck_crane",
    "Автовышка": "aerial_platform",
    "Бульдозер": "bulldozer",
    "Каток": "road_roller",
    "Грейдер": "grader",
    "Манипулятор": "manipulator",
    "Автобетономешалка": "concrete_mixer",
    "Бетононасос": "concrete_pump",
    "Ассенизатор": "septic_truck",
    "Мини-думпер": "mini_dumper",
    "Коммунальная и дорожная техника": "municipal",
    "Буровая техника": "drilling",
    "Дробильно-сортировочная техника": "crushing_screening",
    "Навесное и рабочее оборудование": "attachment",
    "Другая спецтехника": "other_special",
}

MOTO_TYPE_CHOICES = ("Мотоцикл", "Скутер", "Квадроцикл", "Другой")
MOTO_TYPE_TO_VEHICLE: dict[str, str] = {
    "Мотоцикл": "motorcycle",
    "Скутер": "scooter",
    "Квадроцикл": "atv",
    "Другой": "other_moto",
}

TRAILER_TYPE_CHOICES = ("Прицеп", "Полуприцеп", "Жилой прицеп / кемпер")
TRAILER_TYPE_TO_VEHICLE: dict[str, str] = {
    "Прицеп": "drawbar_trailer",
    "Полуприцеп": "semi_trailer",
    "Жилой прицеп / кемпер": "camper_trailer",
}

FARM_TYPE_CHOICES = (
    "Трактор",
    "Мини-трактор",
    "Комбайн",
    "Мотоблок / мотокультиватор",
    "Навесная и прицепная сельхозтехника",
    "Другая",
)
FARM_TYPE_TO_VEHICLE: dict[str, str] = {
    "Трактор": "tractor",
    "Мини-трактор": "mini_tractor",
    "Комбайн": "combine",
    "Мотоблок / мотокультиватор": "walk_behind",
    "Навесная и прицепная сельхозтехника": "farm_implement",
    "Другая": "other_agri",
}

WATER_TYPE_CHOICES = ("Лодка", "Катер", "Яхта", "Гидроцикл", "Другой")
WATER_TYPE_TO_VEHICLE: dict[str, str] = {
    "Лодка": "boat",
    "Катер": "motorboat",
    "Яхта": "yacht",
    "Гидроцикл": "jet_ski",
    "Другой": "other_watercraft",
}

# Leaf → (subtype_field_key | None, mapping)
RENTAL_SUBTYPE_CONFIG: dict[str, tuple[str | None, dict[str, str]]] = {
    "transport-rental-legkovye-avtomobili": (None, {}),
    BUS_COMBINED_SLUG: ("rental_bus_type", BUS_TYPE_TO_VEHICLE),
    "transport-rental-gruzovoy-transport": ("rental_cargo_type", CARGO_TYPE_TO_VEHICLE),
    "transport-rental-spetstehnika": ("rental_special_type", SPECIAL_TYPE_TO_VEHICLE),
    "transport-rental-mototehnika": ("rental_moto_type", MOTO_TYPE_TO_VEHICLE),
    TRAILER_RENTAL_SLUG: ("rental_trailer_type", TRAILER_TYPE_TO_VEHICLE),
    FARM_RENTAL_SLUG: ("rental_farm_type", FARM_TYPE_TO_VEHICLE),
    "transport-rental-vodnyy-transport": ("rental_water_type", WATER_TYPE_TO_VEHICLE),
    OTHER_RENTAL_SLUG: (None, {}),
}

# Fixed vehicle_type for leaves without subtype (Car).
RENTAL_LEAF_FIXED_VEHICLE_TYPE: dict[str, str] = {
    "transport-rental-legkovye-avtomobili": "car",
}

RENTAL_LEAF_ALIASES: dict[str, str] = {
    "аренда авто": "transport-rental-legkovye-avtomobili",
    "аренда машины": "transport-rental-legkovye-avtomobili",
    "сдам авто": "transport-rental-legkovye-avtomobili",
    "сдам машину": "transport-rental-legkovye-avtomobili",
    "прокат авто": "transport-rental-legkovye-avtomobili",
    "аренда микроавтобуса": BUS_COMBINED_SLUG,
    "аренда автобуса": BUS_COMBINED_SLUG,
    "сдам микроавтобус": BUS_COMBINED_SLUG,
    "сдам автобус": BUS_COMBINED_SLUG,
    "аренда грузовика": "transport-rental-gruzovoy-transport",
    "сдам самосвал": "transport-rental-gruzovoy-transport",
    "сдам грузовик": "transport-rental-gruzovoy-transport",
    "аренда спецтехники": "transport-rental-spetstehnika",
    "сдам экскаватор": "transport-rental-spetstehnika",
    "аренда мото": "transport-rental-mototehnika",
    "сдам мотоцикл": "transport-rental-mototehnika",
    "аренда прицепа": TRAILER_RENTAL_SLUG,
    "сдам прицеп": TRAILER_RENTAL_SLUG,
    "аренда трактора": FARM_RENTAL_SLUG,
    "сдам трактор": FARM_RENTAL_SLUG,
    "аренда комбайна": FARM_RENTAL_SLUG,
    "аренда лодки": "transport-rental-vodnyy-transport",
    "сдам катер": "transport-rental-vodnyy-transport",
}

RENTAL_PARENT_ALIASES: dict[str, str] = {
    "аренда транспорта": RENTAL_PARENT_SLUG,
    "прокат транспорта": RENTAL_PARENT_SLUG,
    "сдам в аренду": RENTAL_PARENT_SLUG,
}

# Service phrases / aliases stay on Services (not Rental).
RENTAL_SERVICE_BOUNDARY_ALIASES: dict[str, str] = {
    "такси": "services-gruzoperevozki-i-pereezdy",
    "трансфер": "services-gruzoperevozki-i-pereezdy",
    "услуги экскаватора": "services-uslugi-spetstehniki",
    "экскаватор с оператором": "services-uslugi-spetstehniki",
    "манипулятор с оператором": "services-uslugi-spetstehniki",
    "вспашка трактором": "services-uslugi-spetstehniki",
    "грузоперевозка": "services-gruzoperevozki-i-pereezdy",
    "пассажирские перевозки": "services-gruzoperevozki-i-pereezdy",
}


def _choices(*labels: str) -> dict[str, Any]:
    items = [{"value": x, "label": x} for x in labels]
    return {"choices": items, "values": items}


def _unit_choices() -> dict[str, Any]:
    items = [{"value": v, "label": lab} for v, lab in RENTAL_PRICE_UNIT_CHOICES]
    return {"choices": items, "values": items}


def _opt_cfg(*labels: str) -> dict[str, Any]:
    return {"options": [{"value": o, "label": o} for o in labels]}


def _unit_filter_cfg() -> dict[str, Any]:
    return {
        "options": [
            {"value": v, "label": lab} for v, lab in RENTAL_PRICE_UNIT_CHOICES
        ]
    }


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


def _geo() -> list:
    return [
        _field("region", "Регион", CategoryFieldType.string, True, 0),
        _field("city", "Город", CategoryFieldType.city, True, 1),
    ]


def _price_block(sort: int = 100) -> list:
    return [
        _field("price", "Стоимость аренды", CategoryFieldType.price, True, sort),
        _field(
            "rental_price_unit",
            "Период аренды",
            CategoryFieldType.enum,
            True,
            sort + 5,
            _unit_choices(),
        ),
    ]


def _provider_contacts(sort: int = 200) -> list:
    return [
        _field(
            "provider_type",
            "Кто сдаёт",
            CategoryFieldType.enum,
            True,
            sort,
            _choices(*PROVIDER_TYPE_CHOICES),
        ),
        _field(
            "contact_methods",
            "Способы связи",
            CategoryFieldType.enum,
            True,
            sort + 10,
            _choices(*CONTACT_METHOD_CHOICES),
        ),
    ]


def _deposit(sort: int = 180) -> list:
    return [
        _field(
            "deposit_required",
            "Залог",
            CategoryFieldType.enum,
            False,
            sort,
            _choices(*DEPOSIT_REQUIRED_CHOICES),
        ),
        _field(
            "deposit_amount",
            "Размер залога",
            CategoryFieldType.number,
            False,
            sort + 5,
            {
                "min": 0,
                "max": 10_000_000,
                "unit": "сом",
                "integer": True,
                "depends_on": {
                    "field": "deposit_required",
                    "values": ["Есть залог"],
                },
            },
        ),
    ]


def _brand_model_year(sort: int = 40, *, with_year: bool = True) -> list:
    fields = [
        _field("brand", "Марка", CategoryFieldType.brand, False, sort),
        _field("model", "Модель", CategoryFieldType.model, False, sort + 5),
    ]
    if with_year:
        fields.append(
            _field(
                "year",
                "Год выпуска",
                CategoryFieldType.year,
                False,
                sort + 10,
                {"min": 1960, "max_offset_years": 1},
            )
        )
    return fields


def _common_tail() -> list:
    return [*_deposit(180), *_price_block(200), *_provider_contacts(220)]


def _car_fields() -> list:
    return [
        *_geo(),
        *_brand_model_year(20),
        _field(
            "transmission",
            "Коробка передач",
            CategoryFieldType.enum,
            False,
            50,
            _choices(*_TRANSMISSION),
        ),
        _field("fuel", "Топливо", CategoryFieldType.enum, False, 55, _choices(*_FUEL)),
        _field(
            "passenger_capacity",
            "Количество мест",
            CategoryFieldType.number,
            False,
            60,
            {"min": 1, "max": 60, "integer": True},
        ),
        *_common_tail(),
    ]


def _bus_fields() -> list:
    return [
        *_geo(),
        _field(
            "rental_bus_type",
            "Тип транспорта",
            CategoryFieldType.enum,
            True,
            10,
            _choices(*BUS_TYPE_CHOICES),
        ),
        *_brand_model_year(20),
        _field(
            "passenger_capacity",
            "Количество мест",
            CategoryFieldType.number,
            False,
            50,
            {"min": 1, "max": 100, "integer": True},
        ),
        *_common_tail(),
    ]


def _cargo_fields() -> list:
    return [
        *_geo(),
        _field(
            "rental_cargo_type",
            "Тип транспорта",
            CategoryFieldType.enum,
            True,
            10,
            _choices(*CARGO_TYPE_CHOICES),
        ),
        *_brand_model_year(20),
        _field(
            "load_capacity_kg",
            "Грузоподъёмность",
            CategoryFieldType.number,
            False,
            50,
            {"min": 0, "max": 100_000, "unit": "кг", "integer": True},
        ),
        *_common_tail(),
    ]


def _special_fields() -> list:
    return [
        *_geo(),
        _field(
            "rental_special_type",
            "Тип техники",
            CategoryFieldType.enum,
            True,
            10,
            _choices(*SPECIAL_TYPE_CHOICES),
        ),
        *_brand_model_year(20),
        _field(
            "operating_hours",
            "Моточасы",
            CategoryFieldType.number,
            False,
            50,
            {"min": 0, "max": 100_000, "unit": "ч", "integer": True},
        ),
        *_common_tail(),
    ]


def _moto_fields() -> list:
    return [
        *_geo(),
        _field(
            "rental_moto_type",
            "Тип транспорта",
            CategoryFieldType.enum,
            True,
            10,
            _choices(*MOTO_TYPE_CHOICES),
        ),
        *_brand_model_year(20),
        *_common_tail(),
    ]


def _trailer_fields() -> list:
    return [
        *_geo(),
        _field(
            "rental_trailer_type",
            "Тип транспорта",
            CategoryFieldType.enum,
            True,
            10,
            _choices(*TRAILER_TYPE_CHOICES),
        ),
        *_brand_model_year(20),
        _field(
            "load_capacity_kg",
            "Грузоподъёмность",
            CategoryFieldType.number,
            False,
            50,
            {"min": 0, "max": 100_000, "unit": "кг", "integer": True},
        ),
        *_common_tail(),
    ]


def _farm_fields() -> list:
    return [
        *_geo(),
        _field(
            "rental_farm_type",
            "Тип техники",
            CategoryFieldType.enum,
            True,
            10,
            _choices(*FARM_TYPE_CHOICES),
        ),
        *_brand_model_year(20),
        _field(
            "engine_power_hp",
            "Мощность двигателя",
            CategoryFieldType.number,
            False,
            50,
            {"min": 0, "max": 2000, "unit": "л.с.", "integer": True},
        ),
        *_common_tail(),
    ]


def _water_fields() -> list:
    return [
        *_geo(),
        _field(
            "rental_water_type",
            "Тип транспорта",
            CategoryFieldType.enum,
            True,
            10,
            _choices(*WATER_TYPE_CHOICES),
        ),
        *_brand_model_year(20),
        _field(
            "passenger_capacity",
            "Количество мест",
            CategoryFieldType.number,
            False,
            50,
            {"min": 1, "max": 100, "integer": True},
        ),
        *_common_tail(),
    ]


def _other_fields() -> list:
    return [
        *_geo(),
        *_common_tail(),
    ]


RENTAL_CORE_FIELDS_BY_SLUG: dict[str, list] = {
    "transport-rental-legkovye-avtomobili": _car_fields(),
    BUS_COMBINED_SLUG: _bus_fields(),
    "transport-rental-gruzovoy-transport": _cargo_fields(),
    "transport-rental-spetstehnika": _special_fields(),
    "transport-rental-mototehnika": _moto_fields(),
    TRAILER_RENTAL_SLUG: _trailer_fields(),
    FARM_RENTAL_SLUG: _farm_fields(),
    "transport-rental-vodnyy-transport": _water_fields(),
    OTHER_RENTAL_SLUG: _other_fields(),
}


def _common_search_head(
    subtype_key: str | None = None,
    subtype_opts: tuple[str, ...] | None = None,
) -> list:
    rows: list = []
    sort = 0
    if subtype_key and subtype_opts:
        rows.append(
            _filt(
                subtype_key,
                "Тип транспорта" if "farm" not in subtype_key and "special" not in subtype_key else "Тип техники",
                CategoryFilterType.select,
                sort,
                _opt_cfg(*subtype_opts),
            )
        )
        sort += 10
    rows.append(
        _filt(
            "rental_price_unit",
            "Период аренды",
            CategoryFilterType.select,
            sort,
            _unit_filter_cfg(),
        )
    )
    sort += 10
    rows.append(
        _filt(
            "price",
            "Цена",
            CategoryFilterType.range,
            sort,
            {
                "unit": "KGS",
                "requires_filter": "rental_price_unit",
                "sort_requires_filter": "rental_price_unit",
            },
        )
    )
    sort += 10
    rows.extend(
        [
            _filt("region", "Регион", CategoryFilterType.select, sort, {}),
            _filt("city", "Город", CategoryFilterType.select, sort + 10, {}),
            _filt(
                "provider_type",
                "Кто сдаёт",
                CategoryFilterType.select,
                sort + 20,
                _opt_cfg(*PROVIDER_TYPE_CHOICES),
            ),
        ]
    )
    return rows


def _deposit_adv(sort: int) -> list:
    return [
        _filt(
            "deposit_required",
            "Залог",
            CategoryFilterType.select,
            sort,
            _opt_cfg(*DEPOSIT_REQUIRED_CHOICES),
        ),
    ]


def _car_search() -> list:
    rows = _common_search_head(subtype_key=None, subtype_opts=None)
    rows.extend(
        [
            _filt("brand", "Марка", CategoryFilterType.select, 100, {}),
            _filt("model", "Модель", CategoryFilterType.select, 110, {}),
            _filt("year", "Год выпуска", CategoryFilterType.range, 200, {}),
            _filt(
                "transmission",
                "Коробка передач",
                CategoryFilterType.multi_select,
                210,
                _opt_cfg(*_TRANSMISSION),
            ),
            _filt(
                "fuel",
                "Топливо",
                CategoryFilterType.multi_select,
                220,
                _opt_cfg(*_FUEL),
            ),
            _filt(
                "passenger_capacity",
                "Количество мест",
                CategoryFilterType.range,
                230,
                {},
            ),
            *_deposit_adv(240),
        ]
    )
    return rows


def _bus_search() -> list:
    rows = _common_search_head("rental_bus_type", BUS_TYPE_CHOICES)
    # fix label
    rows[0] = _filt(
        "rental_bus_type",
        "Тип транспорта",
        CategoryFilterType.select,
        0,
        _opt_cfg(*BUS_TYPE_CHOICES),
    )
    rows.extend(
        [
            _filt("brand", "Марка", CategoryFilterType.select, 100, {}),
            _filt("model", "Модель", CategoryFilterType.select, 110, {}),
            _filt(
                "passenger_capacity",
                "Количество мест",
                CategoryFilterType.range,
                200,
                {},
            ),
            _filt("year", "Год выпуска", CategoryFilterType.range, 210, {}),
            *_deposit_adv(220),
        ]
    )
    return rows


def _cargo_search() -> list:
    rows = _common_search_head("rental_cargo_type", CARGO_TYPE_CHOICES)
    rows[0] = _filt(
        "rental_cargo_type",
        "Тип транспорта",
        CategoryFilterType.select,
        0,
        _opt_cfg(*CARGO_TYPE_CHOICES),
    )
    rows.extend(
        [
            _filt("brand", "Марка", CategoryFilterType.select, 200, {}),
            _filt("model", "Модель", CategoryFilterType.select, 210, {}),
            _filt(
                "load_capacity_kg",
                "Грузоподъёмность",
                CategoryFilterType.range,
                220,
                {"unit": "кг"},
            ),
            _filt("year", "Год выпуска", CategoryFilterType.range, 230, {}),
            *_deposit_adv(240),
        ]
    )
    return rows


def _special_search() -> list:
    rows = _common_search_head("rental_special_type", SPECIAL_TYPE_CHOICES)
    rows[0] = _filt(
        "rental_special_type",
        "Тип техники",
        CategoryFilterType.select,
        0,
        _opt_cfg(*SPECIAL_TYPE_CHOICES),
    )
    rows.extend(
        [
            _filt("brand", "Марка", CategoryFilterType.select, 200, {}),
            _filt("model", "Модель", CategoryFilterType.select, 210, {}),
            _filt("year", "Год выпуска", CategoryFilterType.range, 220, {}),
            _filt(
                "operating_hours",
                "Моточасы",
                CategoryFilterType.range,
                230,
                {"unit": "ч"},
            ),
            *_deposit_adv(240),
        ]
    )
    return rows


def _moto_search() -> list:
    rows = _common_search_head("rental_moto_type", MOTO_TYPE_CHOICES)
    rows[0] = _filt(
        "rental_moto_type",
        "Тип транспорта",
        CategoryFilterType.select,
        0,
        _opt_cfg(*MOTO_TYPE_CHOICES),
    )
    rows.extend(
        [
            _filt("brand", "Марка", CategoryFilterType.select, 100, {}),
            _filt("model", "Модель", CategoryFilterType.select, 110, {}),
            _filt("year", "Год выпуска", CategoryFilterType.range, 200, {}),
            *_deposit_adv(210),
        ]
    )
    return rows


def _trailer_search() -> list:
    rows = _common_search_head("rental_trailer_type", TRAILER_TYPE_CHOICES)
    rows[0] = _filt(
        "rental_trailer_type",
        "Тип транспорта",
        CategoryFilterType.select,
        0,
        _opt_cfg(*TRAILER_TYPE_CHOICES),
    )
    rows.extend(
        [
            _filt("brand", "Марка", CategoryFilterType.select, 200, {}),
            _filt("model", "Модель", CategoryFilterType.select, 210, {}),
            _filt(
                "load_capacity_kg",
                "Грузоподъёмность",
                CategoryFilterType.range,
                220,
                {"unit": "кг"},
            ),
            *_deposit_adv(230),
        ]
    )
    return rows


def _farm_search() -> list:
    rows = _common_search_head("rental_farm_type", FARM_TYPE_CHOICES)
    rows[0] = _filt(
        "rental_farm_type",
        "Тип техники",
        CategoryFilterType.select,
        0,
        _opt_cfg(*FARM_TYPE_CHOICES),
    )
    rows.extend(
        [
            _filt("brand", "Марка", CategoryFilterType.select, 200, {}),
            _filt("model", "Модель", CategoryFilterType.select, 210, {}),
            _filt(
                "engine_power_hp",
                "Мощность двигателя",
                CategoryFilterType.range,
                220,
                {"unit": "л.с."},
            ),
            _filt("year", "Год выпуска", CategoryFilterType.range, 230, {}),
            *_deposit_adv(240),
        ]
    )
    return rows


def _water_search() -> list:
    rows = _common_search_head("rental_water_type", WATER_TYPE_CHOICES)
    rows[0] = _filt(
        "rental_water_type",
        "Тип транспорта",
        CategoryFilterType.select,
        0,
        _opt_cfg(*WATER_TYPE_CHOICES),
    )
    rows.extend(
        [
            _filt("brand", "Марка", CategoryFilterType.select, 200, {}),
            _filt("model", "Модель", CategoryFilterType.select, 210, {}),
            _filt("year", "Год выпуска", CategoryFilterType.range, 220, {}),
            _filt(
                "passenger_capacity",
                "Количество мест",
                CategoryFilterType.range,
                230,
                {},
            ),
            *_deposit_adv(240),
        ]
    )
    return rows


def _other_search() -> list:
    rows = _common_search_head(None, None)
    rows.extend(_deposit_adv(200))
    return rows


RENTAL_SEARCH_FILTERS_BY_SLUG: dict[str, list] = {
    "transport-rental-legkovye-avtomobili": _car_search(),
    BUS_COMBINED_SLUG: _bus_search(),
    "transport-rental-gruzovoy-transport": _cargo_search(),
    "transport-rental-spetstehnika": _special_search(),
    "transport-rental-mototehnika": _moto_search(),
    TRAILER_RENTAL_SLUG: _trailer_search(),
    FARM_RENTAL_SLUG: _farm_search(),
    "transport-rental-vodnyy-transport": _water_search(),
    OTHER_RENTAL_SLUG: _other_search(),
}


def format_rental_price(amount: int | float | str, unit: str) -> str:
    """Canonical Create/Preview/Card/Detail formatter."""
    try:
        n = int(float(str(amount).replace(" ", "").replace(",", ".")))
    except (TypeError, ValueError):
        n = 0
    formatted = f"{n:,}".replace(",", " ")
    suffix = RENTAL_PRICE_UNIT_CARD_SUFFIX.get(unit, "")
    if not suffix:
        return f"{formatted} сом"
    return f"{formatted} сом {suffix}"
