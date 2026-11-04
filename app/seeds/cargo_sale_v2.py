# -*- coding: utf-8 -*-
"""Transport → Грузовой транспорт V2 — leaf Create/Search SoT.

Parent ``transport-cargo`` is picker-only (not live Create SoT).
Canonical key ``load_capacity_kg`` (not legacy ``payload_kg``).
Axle formula replaces Car-style drive for Cargo.
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
    YES_NO_CHOICES,
)

CARGO_PARENT_SLUG = "transport-cargo"

CARGO_LEAF_SLUGS: tuple[str, ...] = (
    "transport-cargo-samosvaly",
    "transport-cargo-tyagachi",
    "transport-cargo-bortovye-gruzoviki",
    "transport-cargo-furgony",
    "transport-cargo-refrizheratory",
    "transport-cargo-malotonnazhnye",
    "transport-cargo-tsisterny",
    "transport-cargo-evakuatory",
    "transport-cargo-drugie-gruzoviki",
)

CARGO_LEAF_LABELS: dict[str, str] = {
    "transport-cargo-samosvaly": "Самосвалы",
    "transport-cargo-tyagachi": "Тягачи",
    "transport-cargo-bortovye-gruzoviki": "Бортовые грузовики",
    "transport-cargo-furgony": "Фургоны",
    "transport-cargo-refrizheratory": "Рефрижераторы",
    "transport-cargo-malotonnazhnye": "Легкий грузовой",
    "transport-cargo-tsisterny": "Цистерны",
    "transport-cargo-evakuatory": "Эвакуаторы",
    "transport-cargo-drugie-gruzoviki": "Другие грузовики",
}

CARGO_LEAF_SORT: dict[str, int] = {
    "transport-cargo-samosvaly": 10,
    "transport-cargo-tyagachi": 20,
    "transport-cargo-bortovye-gruzoviki": 30,
    "transport-cargo-furgony": 40,
    "transport-cargo-refrizheratory": 45,
    "transport-cargo-malotonnazhnye": 48,
    "transport-cargo-tsisterny": 50,
    "transport-cargo-evakuatory": 55,
    "transport-cargo-drugie-gruzoviki": 58,
}

CARGO_LEAF_VEHICLE_TYPE: dict[str, str] = {
    "transport-cargo-samosvaly": "dump_truck",
    "transport-cargo-tyagachi": "tractor_unit",
    "transport-cargo-bortovye-gruzoviki": "flatbed_truck",
    "transport-cargo-furgony": "box_truck",
    "transport-cargo-refrizheratory": "refrigerated_truck",
    "transport-cargo-malotonnazhnye": "light_truck",
    "transport-cargo-tsisterny": "tanker_truck",
    "transport-cargo-evakuatory": "tow_truck",
    "transport-cargo-drugie-gruzoviki": "other_truck",
}

CARGO_INACTIVE_LEGACY_SLUGS: tuple[str, ...] = (
    "transport-trucks",
    "transport-commercial",
    "transport-commercial-malotonnazhnye-gruzoviki",
    "transport-commercial-furgony",
    "transport-commercial-pikapy",
    "transport-commercial-spetsavtomobili",
    "transport-cargo-spetsgruzoviki",
    "transport-cargo-zapchasti",
    "transport-cargo-remont-i-obsluzhivanie",
    "transport-special-equipment-evakuatory",
)

# Sale-oriented aliases → leaf (not parent).
CARGO_LEAF_ALIASES: dict[str, str] = {
    "самосвал": "transport-cargo-samosvaly",
    "тягач": "transport-cargo-tyagachi",
    "седельный тягач": "transport-cargo-tyagachi",
    "бортовой": "transport-cargo-bortovye-gruzoviki",
    "бортовой грузовик": "transport-cargo-bortovye-gruzoviki",
    "фургон": "transport-cargo-furgony",
    "рефрижератор": "transport-cargo-refrizheratory",
    "цистерна": "transport-cargo-tsisterny",
    "камаз самосвал": "transport-cargo-samosvaly",
    "камаз цистерна": "transport-cargo-tsisterny",
    "камаз тягач": "transport-cargo-tyagachi",
}

# Keep parent-level generic nouns on parent (existing).
CARGO_PARENT_ALIASES: dict[str, str] = {
    "грузовик": CARGO_PARENT_SLUG,
    "камаз": CARGO_PARENT_SLUG,
    "газель": CARGO_PARENT_SLUG,
    "фура": CARGO_PARENT_SLUG,
}

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
_TRANSMISSION = ("Механика", "Автомат")

# Canonical stable values (ASCII x). Create Flutter currently stores the
# picker label string — keep value==label so Create↔Search identity matches.
AXLE_VALUES: tuple[str, ...] = (
    "4x2",
    "4x4",
    "6x2",
    "6x4",
    "6x6",
    "8x2",
    "8x4",
    "8x8",
    "Другая",
)
AXLE_LABELS: dict[str, str] = {v: v for v in AXLE_VALUES}

VAN_TYPES = ("Промтоварный", "Изотермический", "Другой")
TANKER_PURPOSES = ("Топливная", "Для воды", "Пищевая", "Другая")
TRUCK_PURPOSES = (
    "Шасси",
    "Тентованный",
    "Контейнеровоз",
    "Лесовоз",
    "Зерновоз",
    "Скотовоз",
    "Автовоз",
    "Другой",
)
CABIN_SLEEPER = ("Есть", "Нет")

CARGO_OTHER_BRAND_TYPES: tuple[str, ...] = (
    "dump_truck",
    "tractor_unit",
    "flatbed_truck",
    "box_truck",
    "refrigerated_truck",
    "light_truck",
    "tanker_truck",
    "tow_truck",
    "other_truck",
)

CARGO_YEAR_MIN = 1970
MILEAGE_MAX = 3_000_000
LOAD_KG_MAX = 500_000
BODY_M3_MAX = 200
BODY_LENGTH_M_MAX = 30
TANK_L_MAX = 80_000


def _choices(*labels: str) -> dict[str, Any]:
    items = [{"value": x, "label": x} for x in labels]
    return {"choices": items, "values": items}


def _axle_choices() -> dict[str, Any]:
    items = [
        {"value": v, "label": AXLE_LABELS.get(v, v)} for v in AXLE_VALUES
    ]
    return {"choices": items, "values": items}


def _axle_opt_cfg() -> dict[str, Any]:
    return {
        "options": [
            {"value": v, "label": AXLE_LABELS.get(v, v)} for v in AXLE_VALUES
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
            {"min": CARGO_YEAR_MIN, "max_offset_years": 1},
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


def _fuel(sort: int) -> list:
    return [
        _field(
            "fuel",
            "Топливо",
            CategoryFieldType.enum,
            False,
            sort,
            _choices(*_FUEL),
        ),
    ]


def _transmission(sort: int) -> list:
    return [
        _field(
            "transmission",
            "Коробка передач",
            CategoryFieldType.enum,
            False,
            sort,
            _choices(*_TRANSMISSION),
        ),
    ]


def _axle(sort: int) -> list:
    return [
        _field(
            "axle_configuration",
            "Колёсная формула",
            CategoryFieldType.enum,
            False,
            sort,
            _axle_choices(),
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


def _body_volume(sort: int) -> list:
    return [
        _field(
            "body_volume_m3",
            "Объём кузова",
            CategoryFieldType.decimal,
            False,
            sort,
            {"min": 0, "max": BODY_M3_MAX, "unit": "m3"},
        ),
    ]


def _body_length(sort: int) -> list:
    return [
        _field(
            "body_length_m",
            "Длина кузова",
            CategoryFieldType.decimal,
            False,
            sort,
            {"min": 0, "max": BODY_LENGTH_M_MAX, "unit": "m"},
        ),
    ]


def _tank_capacity(sort: int) -> list:
    return [
        _field(
            "tank_capacity_l",
            "Объём цистерны",
            CategoryFieldType.number,
            False,
            sort,
            {"min": 0, "max": TANK_L_MAX, "unit": "L", "integer": True},
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


def _dump_fields() -> list:
    return [
        *_geo_head(),
        *_brand_model(10),
        *_year(30),
        *_mileage(40),
        *_fuel(50),
        *_transmission(55),
        *_axle(60),
        *_load_capacity(70),
        *_body_volume(80),
        *_condition_block(120),
        *_commerce(140),
    ]


def _tractor_fields() -> list:
    return [
        *_geo_head(),
        *_brand_model(10),
        *_year(30),
        *_mileage(40),
        *_fuel(50),
        *_transmission(55),
        *_axle(60),
        _field(
            "cabin_sleeper",
            "Спальное место в кабине",
            CategoryFieldType.enum,
            False,
            70,
            _choices(*CABIN_SLEEPER),
        ),
        *_condition_block(120),
        *_commerce(140),
    ]


def _flatbed_fields() -> list:
    return [
        *_geo_head(),
        *_brand_model(10),
        *_year(30),
        *_mileage(40),
        *_fuel(50),
        *_axle(60),
        *_load_capacity(70),
        *_body_length(80),
        *_condition_block(120),
        *_commerce(140),
    ]


def _van_fields() -> list:
    return [
        *_geo_head(),
        *_brand_model(10),
        _field(
            "van_type",
            "Тип фургона",
            CategoryFieldType.enum,
            False,
            25,
            _choices(*VAN_TYPES),
        ),
        *_year(30),
        *_mileage(40),
        *_fuel(50),
        *_transmission(55),
        *_load_capacity(70),
        *_body_volume(80),
        *_body_length(90),
        *_condition_block(120),
        *_commerce(140),
    ]


def _reefer_fields() -> list:
    return [
        *_geo_head(),
        *_brand_model(10),
        *_year(30),
        *_mileage(40),
        *_fuel(50),
        *_transmission(55),
        *_load_capacity(70),
        *_body_volume(80),
        *_condition_block(120),
        *_commerce(140),
    ]


def _light_fields() -> list:
    return [
        *_geo_head(),
        *_brand_model(10),
        *_year(30),
        *_mileage(40),
        *_fuel(50),
        *_transmission(55),
        *_load_capacity(70),
        *_condition_block(120),
        *_commerce(140),
    ]


def _tanker_fields() -> list:
    return [
        *_geo_head(),
        *_brand_model(10),
        _field(
            "tanker_purpose",
            "Назначение цистерны",
            CategoryFieldType.enum,
            False,
            25,
            _choices(*TANKER_PURPOSES),
        ),
        *_year(30),
        *_mileage(40),
        *_fuel(50),
        *_axle(60),
        *_load_capacity(70),
        *_tank_capacity(80),
        *_condition_block(120),
        *_commerce(140),
    ]


def _tow_fields() -> list:
    return [
        *_geo_head(),
        *_brand_model(10),
        *_year(30),
        *_mileage(40),
        *_fuel(50),
        *_load_capacity(70),
        *_condition_block(120),
        *_commerce(140),
    ]


def _other_fields() -> list:
    return [
        *_geo_head(),
        *_brand_model(10),
        _field(
            "truck_purpose",
            "Тип / назначение",
            CategoryFieldType.enum,
            False,
            25,
            _choices(*TRUCK_PURPOSES),
        ),
        *_year(30),
        *_mileage(40),
        *_fuel(50),
        *_transmission(55),
        *_axle(60),
        *_load_capacity(70),
        *_condition_block(120),
        *_commerce(140),
    ]


CARGO_CORE_FIELDS_BY_SLUG: dict[str, list] = {
    "transport-cargo-samosvaly": _dump_fields(),
    "transport-cargo-tyagachi": _tractor_fields(),
    "transport-cargo-bortovye-gruzoviki": _flatbed_fields(),
    "transport-cargo-furgony": _van_fields(),
    "transport-cargo-refrizheratory": _reefer_fields(),
    "transport-cargo-malotonnazhnye": _light_fields(),
    "transport-cargo-tsisterny": _tanker_fields(),
    "transport-cargo-evakuatory": _tow_fields(),
    "transport-cargo-drugie-gruzoviki": _other_fields(),
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


def _cargo_search(
    *,
    mileage: bool = True,
    fuel: bool = True,
    transmission: bool = False,
    axle: bool = False,
    load_from: bool = False,
    body_volume: bool = False,
    body_length: bool = False,
    tank: bool = False,
    cabin: bool = False,
    van_type: bool = False,
    tanker_purpose: bool = False,
    truck_purpose: bool = False,
) -> list:
    rows = [*_common_search_head(10)]
    n = 70
    if van_type:
        rows.append(
            _filt(
                "van_type",
                "Тип фургона",
                CategoryFilterType.multi_select,
                n,
                _opt_cfg(*VAN_TYPES),
            )
        )
        n += 5
    if tanker_purpose:
        rows.append(
            _filt(
                "tanker_purpose",
                "Назначение цистерны",
                CategoryFilterType.multi_select,
                n,
                _opt_cfg(*TANKER_PURPOSES),
            )
        )
        n += 5
    if truck_purpose:
        rows.append(
            _filt(
                "truck_purpose",
                "Тип / назначение",
                CategoryFilterType.multi_select,
                n,
                _opt_cfg(*TRUCK_PURPOSES),
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
    if body_volume:
        rows.append(
            _filt(
                "body_volume_m3",
                "Объём кузова от",
                CategoryFilterType.range,
                n,
                {"unit": "m3", "mode": "min"},
            )
        )
        n += 5
    if body_length:
        rows.append(
            _filt(
                "body_length_m",
                "Длина кузова от",
                CategoryFilterType.range,
                n,
                {"unit": "m", "mode": "min"},
            )
        )
        n += 5
    if tank:
        rows.append(
            _filt(
                "tank_capacity_l",
                "Объём цистерны от",
                CategoryFilterType.range,
                n,
                {"unit": "L", "mode": "min"},
            )
        )
        n += 5
    if axle:
        rows.append(
            _filt(
                "axle_configuration",
                "Колёсная формула",
                CategoryFilterType.multi_select,
                n,
                _axle_opt_cfg(),
            )
        )
        n += 5
    if cabin:
        rows.append(
            _filt(
                "cabin_sleeper",
                "Спальное место в кабине",
                CategoryFilterType.multi_select,
                n,
                _opt_cfg(*CABIN_SLEEPER),
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
    if transmission:
        rows.append(
            _filt(
                "transmission",
                "Коробка передач",
                CategoryFilterType.multi_select,
                n,
                _opt_cfg(*_TRANSMISSION),
            )
        )
        n += 5
    rows.extend(_condition_seller_sort(n + 10))
    return rows


CARGO_SEARCH_FILTERS_BY_SLUG: dict[str, list] = {
    "transport-cargo-samosvaly": _cargo_search(
        transmission=True,
        axle=True,
        load_from=True,
        body_volume=True,
    ),
    "transport-cargo-tyagachi": _cargo_search(
        transmission=True,
        axle=True,
        cabin=True,
    ),
    "transport-cargo-bortovye-gruzoviki": _cargo_search(
        axle=True,
        load_from=True,
        body_length=True,
    ),
    "transport-cargo-furgony": _cargo_search(
        transmission=True,
        load_from=True,
        body_volume=True,
        body_length=True,
        van_type=True,
    ),
    "transport-cargo-refrizheratory": _cargo_search(
        transmission=True,
        load_from=True,
        body_volume=True,
    ),
    "transport-cargo-malotonnazhnye": _cargo_search(
        transmission=True,
        load_from=True,
    ),
    "transport-cargo-tsisterny": _cargo_search(
        axle=True,
        load_from=True,
        tank=True,
        tanker_purpose=True,
    ),
    "transport-cargo-evakuatory": _cargo_search(load_from=True),
    "transport-cargo-drugie-gruzoviki": _cargo_search(
        transmission=True,
        axle=True,
        load_from=True,
        truck_purpose=True,
    ),
}


def cargo_other_brands() -> list[tuple[str, str, str | None, str]]:
    out: list[tuple[str, str, str | None, str]] = []
    for vt in CARGO_OTHER_BRAND_TYPES:
        slug = f"other-{vt.replace('_', '-')}"
        out.append((slug, "Другая марка", None, vt))
    return out


def cargo_other_models() -> dict[str, list[tuple[str, str]]]:
    return {
        f"other-{vt.replace('_', '-')}": [("other-model", "Другая модель")]
        for vt in CARGO_OTHER_BRAND_TYPES
    }
