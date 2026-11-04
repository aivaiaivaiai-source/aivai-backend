# -*- coding: utf-8 -*-
"""Transport → Электротранспорт V2 — leaf Create/Search vocabulary (Backend SoT).

Parent ``transport-electric`` is picker-only (no live Create/Search SoT).
E-bike stays under ``transport-bicycles`` (not duplicated here).
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
)

ELECTRIC_PARENT_SLUG = "transport-electric"

# Stable IDs: 7 existing electric leaves + re-parented moto electric 754/756.
ELECTRIC_LEAF_SLUGS: tuple[str, ...] = (
    "transport-electric-elektrosamokaty",
    "transport-electric-elektroskutery",
    "transport-moto-tech-elektromototsikly",  # re-parented → Electric
    "transport-moto-tech-elektrokvadrotsikly",  # re-parented → Electric
    "transport-electric-giroskutery",
    "transport-electric-monokolesa",
    "transport-electric-sigvei-i-mini-sigvei",
    "transport-electric-elektricheskie-mini-mobili",
    "transport-electric-drugoy-redkiy-elektrotransport",
)

ELECTRIC_LEAF_LABELS: dict[str, str] = {
    "transport-electric-elektrosamokaty": "Электросамокаты",
    "transport-electric-elektroskutery": "Электроскутеры",
    "transport-moto-tech-elektromototsikly": "Электромотоциклы",
    "transport-moto-tech-elektrokvadrotsikly": "Электроквадроциклы",
    "transport-electric-giroskutery": "Гироскутеры",
    "transport-electric-monokolesa": "Моноколёса",
    "transport-electric-sigvei-i-mini-sigvei": "Сигвеи",
    "transport-electric-elektricheskie-mini-mobili": (
        "Гольфкары и электрические мини-мобили"
    ),
    "transport-electric-drugoy-redkiy-elektrotransport": "Другой электротранспорт",
}

ELECTRIC_LEAF_SORT: dict[str, int] = {
    "transport-electric-elektrosamokaty": 10,
    "transport-electric-elektroskutery": 15,
    "transport-moto-tech-elektromototsikly": 20,
    "transport-moto-tech-elektrokvadrotsikly": 25,
    "transport-electric-giroskutery": 30,
    "transport-electric-monokolesa": 40,
    "transport-electric-sigvei-i-mini-sigvei": 50,
    "transport-electric-elektricheskie-mini-mobili": 60,
    "transport-electric-drugoy-redkiy-elektrotransport": 70,
}

ELECTRIC_LEAF_VEHICLE_TYPE: dict[str, str] = {
    "transport-electric-elektrosamokaty": "e_scooter",
    "transport-electric-elektroskutery": "e_moped",
    "transport-moto-tech-elektromototsikly": "e_motorcycle",
    "transport-moto-tech-elektrokvadrotsikly": "e_atv",
    "transport-electric-giroskutery": "hoverboard",
    "transport-electric-monokolesa": "monowheel",
    "transport-electric-sigvei-i-mini-sigvei": "segway",
    "transport-electric-elektricheskie-mini-mobili": "golf_cart",
    "transport-electric-drugoy-redkiy-elektrotransport": "other_electric",
}

# Stay inactive under Electric (or Moto duplicate scooter). Never re-activate.
ELECTRIC_INACTIVE_LEGACY_SLUGS: frozenset[str] = frozenset(
    {
        "transport-electric-elektrobaggi",
        "transport-electric-elektrokarty",
        "transport-electric-elektrotrayki",
        "transport-electric-zapchasti-dlya-elektrotransporta",
        "transport-electric-aksessuary-dlya-elektrotransporta",
        "transport-electric-remont-i-obsluzhivanie",
        "transport-moto-tech-elektroskutery",  # duplicate of Electric 1652
    }
)

ELECTRIC_SUBTYPE_CHOICES: tuple[str, ...] = (
    "Электротрицикл",
    "Электробагги",
    "Электрокартинг",
    "Электрическая мини-техника",
    "Другое",
)

_SELLER = ("Частное лицо", "Магазин", "Дилер")
_DOCUMENTS = ("Есть", "Нет")
ELECTRIC_YEAR_MIN = 1960

# Reasonable numeric bounds (not product censorship).
POWER_W_OPTIONS: dict[str, Any] = {
    "min": 1,
    "max": 200000,
    "unit": "W",
}
RANGE_KM_OPTIONS: dict[str, Any] = {"min": 1, "max": 1000, "unit": "km"}
BATTERY_V_OPTIONS: dict[str, Any] = {"min": 1, "max": 800, "unit": "V"}
BATTERY_AH_OPTIONS: dict[str, Any] = {"min": 1, "max": 500, "unit": "Ah"}
SPEED_KMH_OPTIONS: dict[str, Any] = {"min": 1, "max": 300, "unit": "km/h"}

ELECTRIC_FORBIDDEN_FIELD_KEYS: frozenset[str] = frozenset(
    {
        "engine_cc",
        "engine_volume",
        "fuel",
        "transmission",
        "mileage",
        "mileage_unit",
        "drive",
        "after_accident",
        "registration_country",
        "available_in_kg",
        "customs_cleared_kg",
        "taxes_paid",
        "steering_side",
        "fresh_import",
        "power_kw",
        "battery_capacity",
    }
)


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


def _brand_model(*, required: bool) -> list:
    return [
        _field("brand", "Марка", CategoryFieldType.brand, required, 10),
        _field("model", "Модель", CategoryFieldType.model, required, 20),
    ]


def _year(*, required: bool, sort: int = 30) -> list:
    return [
        _field(
            "year",
            "Год выпуска",
            CategoryFieldType.year,
            required,
            sort,
            {"min": ELECTRIC_YEAR_MIN, "max_offset_years": 1},
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


def _tech_light(*, removable: bool, sort: int) -> list:
    rows = [
        _field(
            "power_w",
            "Мощность",
            CategoryFieldType.number,
            False,
            sort,
            POWER_W_OPTIONS,
            "Мощность двигателя в ваттах (Вт)",
        ),
        _field(
            "range_km",
            "Запас хода",
            CategoryFieldType.number,
            False,
            sort + 10,
            RANGE_KM_OPTIONS,
            "Запас хода в км",
        ),
        _field(
            "battery_voltage_v",
            "Напряжение батареи",
            CategoryFieldType.number,
            False,
            sort + 20,
            BATTERY_V_OPTIONS,
            "Напряжение в вольтах (В)",
        ),
        _field(
            "battery_capacity_ah",
            "Ёмкость батареи",
            CategoryFieldType.number,
            False,
            sort + 30,
            BATTERY_AH_OPTIONS,
            "Ёмкость в ампер-часах (А·ч)",
        ),
    ]
    n = sort + 40
    if removable:
        rows.append(
            _field(
                "removable_battery",
                "Съёмная батарея",
                CategoryFieldType.enum,
                False,
                n,
                _choices(*YES_NO_CHOICES),
            )
        )
        n += 10
    rows.extend(
        [
            _field(
                "max_speed_kmh",
                "Максимальная скорость",
                CategoryFieldType.number,
                False,
                n,
                SPEED_KMH_OPTIONS,
                "км/ч",
            ),
            _field(
                "charger_included",
                "Зарядное устройство в комплекте",
                CategoryFieldType.enum,
                False,
                n + 10,
                _choices(*YES_NO_CHOICES),
            ),
            _field(
                "color",
                "Цвет",
                CategoryFieldType.enum,
                False,
                n + 20,
                _choices(*VEHICLE_COLOR_CHOICES),
            ),
        ]
    )
    return rows


def _documents(*, required: bool, sort: int) -> list:
    return [
        _field(
            "documents",
            "Документы",
            CategoryFieldType.enum,
            required,
            sort,
            _choices(*_DOCUMENTS),
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


def _e_scooter_fields() -> list:
    return [
        *_geo_head(),
        *_brand_model(required=True),
        *_year(required=False, sort=30),
        *_condition_block(40),
        *_tech_light(removable=True, sort=50),
        *_commerce(120),
    ]


def _e_moped_fields() -> list:
    return [
        *_geo_head(),
        *_brand_model(required=True),
        *_year(required=True, sort=30),
        *_condition_block(40),
        *_tech_light(removable=True, sort=50),
        *_documents(required=False, sort=130),
        *_commerce(140),
    ]


def _e_motorcycle_fields() -> list:
    return [
        *_geo_head(),
        *_brand_model(required=True),
        *_year(required=True, sort=30),
        *_condition_block(40),
        *_tech_light(removable=True, sort=50),
        *_documents(required=True, sort=130),
        *_commerce(140),
    ]


def _e_atv_fields() -> list:
    return [
        *_geo_head(),
        *_brand_model(required=True),
        *_year(required=True, sort=30),
        *_condition_block(40),
        *_tech_light(removable=False, sort=50),
        *_documents(required=False, sort=130),
        *_commerce(140),
    ]


def _hoverboard_fields() -> list:
    return [
        *_geo_head(),
        *_brand_model(required=True),
        *_year(required=False, sort=30),
        *_condition_block(40),
        *_tech_light(removable=False, sort=50),
        *_commerce(120),
    ]


def _monowheel_fields() -> list:
    return _hoverboard_fields()


def _segway_fields() -> list:
    return _hoverboard_fields()


def _golf_fields() -> list:
    return [
        *_geo_head(),
        *_brand_model(required=True),
        *_year(required=True, sort=30),
        *_condition_block(40),
        *_tech_light(removable=False, sort=50),
        *_documents(required=False, sort=130),
        *_commerce(140),
    ]


def _other_fields() -> list:
    return [
        *_geo_head(),
        _field(
            "electric_subtype",
            "Тип электротранспорта",
            CategoryFieldType.enum,
            True,
            5,
            _choices(*ELECTRIC_SUBTYPE_CHOICES),
        ),
        *_brand_model(required=False),
        *_year(required=False, sort=30),
        *_condition_block(40),
        *_tech_light(removable=False, sort=50),
        *_documents(required=False, sort=130),
        *_commerce(140),
    ]


ELECTRIC_CORE_FIELDS_BY_SLUG: dict[str, list] = {
    "transport-electric-elektrosamokaty": _e_scooter_fields(),
    "transport-electric-elektroskutery": _e_moped_fields(),
    "transport-moto-tech-elektromototsikly": _e_motorcycle_fields(),
    "transport-moto-tech-elektrokvadrotsikly": _e_atv_fields(),
    "transport-electric-giroskutery": _hoverboard_fields(),
    "transport-electric-monokolesa": _monowheel_fields(),
    "transport-electric-sigvei-i-mini-sigvei": _segway_fields(),
    "transport-electric-elektricheskie-mini-mobili": _golf_fields(),
    "transport-electric-drugoy-redkiy-elektrotransport": _other_fields(),
}


def _common_search(
    *,
    include_brand_model: bool = True,
    include_year: bool = False,
    include_power: bool = False,
    include_range: bool = False,
    extra: list | None = None,
) -> list:
    rows: list = []
    sort_n = 10
    if include_brand_model:
        rows.append(_filt("brand", "Марка", CategoryFilterType.select, sort_n, {}))
        sort_n += 10
        rows.append(_filt("model", "Модель", CategoryFilterType.select, sort_n, {}))
        sort_n += 10
    rows.append(
        _filt("price", "Цена", CategoryFilterType.range, sort_n, {"unit": "KGS"})
    )
    sort_n += 10
    if include_year:
        rows.append(_filt("year", "Год выпуска", CategoryFilterType.range, sort_n, {}))
        sort_n += 10
    rows.append(_filt("region", "Регион", CategoryFilterType.select, sort_n, {}))
    sort_n += 10
    rows.append(_filt("city", "Город", CategoryFilterType.select, sort_n, {}))
    sort_n += 10
    if include_power:
        rows.append(
            _filt(
                "power_w",
                "Мощность",
                CategoryFilterType.range,
                sort_n,
                {"unit": "W"},
            )
        )
        sort_n += 10
    if include_range:
        rows.append(
            _filt(
                "range_km",
                "Запас хода",
                CategoryFilterType.range,
                sort_n,
                {"unit": "km"},
            )
        )
        sort_n += 10
    if extra:
        for item in extra:
            key, label, ftype, _s, config = item
            rows.append(_filt(key, label, ftype, sort_n, config))
            sort_n += 10
    rows.extend(
        [
            _filt(
                "condition",
                "Состояние",
                CategoryFilterType.multi_select,
                sort_n,
                _opt_cfg(*CONDITION_V2_CHOICES),
            ),
            _filt(
                "seller_type",
                "Кто продаёт",
                CategoryFilterType.multi_select,
                sort_n + 10,
                _opt_cfg(*_SELLER),
            ),
            _filt(
                "sort",
                "Сортировка",
                CategoryFilterType.select,
                sort_n + 30,
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


ELECTRIC_SEARCH_FILTERS_BY_SLUG: dict[str, list] = {
    "transport-electric-elektrosamokaty": _common_search(
        include_year=True,
        include_power=True,
        include_range=True,
    ),
    "transport-electric-elektroskutery": _common_search(
        include_year=True,
        include_power=True,
        include_range=True,
    ),
    "transport-moto-tech-elektromototsikly": _common_search(
        include_year=True,
        include_power=True,
        include_range=True,
    ),
    "transport-moto-tech-elektrokvadrotsikly": _common_search(
        include_year=True,
        include_power=True,
        include_range=False,
    ),
    "transport-electric-giroskutery": _common_search(
        include_year=True,
        include_power=False,
        include_range=False,
    ),
    "transport-electric-monokolesa": _common_search(
        include_year=True,
        include_power=True,
        include_range=True,
    ),
    "transport-electric-sigvei-i-mini-sigvei": _common_search(
        include_year=True,
        include_power=False,
        include_range=False,
    ),
    "transport-electric-elektricheskie-mini-mobili": _common_search(
        include_year=True,
        include_power=True,
        include_range=True,
    ),
    "transport-electric-drugoy-redkiy-elektrotransport": _common_search(
        include_brand_model=True,
        include_year=True,
        include_power=False,
        include_range=False,
        extra=[
            _filt(
                "electric_subtype",
                "Тип электротранспорта",
                CategoryFilterType.multi_select,
                0,
                _opt_cfg(*ELECTRIC_SUBTYPE_CHOICES),
            ),
        ],
    ),
}
