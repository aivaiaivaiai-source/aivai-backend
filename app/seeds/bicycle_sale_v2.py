# -*- coding: utf-8 -*-
"""Transport → Велосипеды V2 — leaf Create/Search vocabulary (Backend SoT).

Parent ``transport-bicycles`` is picker-only (no live Create/Search SoT).
Default currency for bicycles is KGS (product policy; user may override USD).
E-bike lives only here (not under Электротранспорт).
Gravel / Fixie / folding / fat / touring stay under «Другие» — no extra leaves.
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
from app.seeds.electric_sale_v2 import (
    BATTERY_AH_OPTIONS,
    BATTERY_V_OPTIONS,
    POWER_W_OPTIONS,
    RANGE_KM_OPTIONS,
    SPEED_KMH_OPTIONS,
)

BICYCLE_PARENT_SLUG = "transport-bicycles"

BICYCLE_LEAF_SLUGS: tuple[str, ...] = (
    "transport-bicycles-gornye-velosipedy",
    "transport-bicycles-gorodskie-velosipedy",
    "transport-bicycles-shosseynye-velosipedy",
    "transport-bicycles-podrostkovye-velosipedy",
    "transport-bicycles-elektrovelosipedy",
    "transport-bicycles-bmx",
    "transport-bicycles-drugie",
)

BICYCLE_LEAF_LABELS: dict[str, str] = {
    "transport-bicycles-gornye-velosipedy": "Горные",
    "transport-bicycles-gorodskie-velosipedy": "Городские",
    "transport-bicycles-shosseynye-velosipedy": "Шоссейные",
    "transport-bicycles-podrostkovye-velosipedy": "Подростковые",
    "transport-bicycles-elektrovelosipedy": "Электровелосипеды",
    "transport-bicycles-bmx": "BMX",
    "transport-bicycles-drugie": "Другие велосипеды",
}

BICYCLE_LEAF_SORT: dict[str, int] = {
    "transport-bicycles-gornye-velosipedy": 10,
    "transport-bicycles-gorodskie-velosipedy": 20,
    "transport-bicycles-shosseynye-velosipedy": 30,
    "transport-bicycles-podrostkovye-velosipedy": 40,
    "transport-bicycles-elektrovelosipedy": 45,
    "transport-bicycles-bmx": 50,
    "transport-bicycles-drugie": 60,
}

BICYCLE_LEAF_VEHICLE_TYPE: dict[str, str] = {
    "transport-bicycles-gornye-velosipedy": "mountain_bike",
    "transport-bicycles-gorodskie-velosipedy": "city_bike",
    "transport-bicycles-shosseynye-velosipedy": "road_bike",
    "transport-bicycles-podrostkovye-velosipedy": "teen_bike",
    "transport-bicycles-elektrovelosipedy": "e_bike",
    "transport-bicycles-bmx": "bmx",
    "transport-bicycles-drugie": "other_bicycle",
}

BICYCLE_INACTIVE_LEGACY_SLUGS: frozenset[str] = frozenset(
    {
        "transport-bicycles-detskie",
        "transport-bicycles-skladnye-velosipedy",
        "transport-bicycles-velozapchasti",
        "transport-bicycles-veloaksessuary",
        "transport-bicycles-veloservis",
    }
)

# Fake type-as-brand rows — disable; never treat as manufacturers.
BICYCLE_FAKE_BRAND_SLUGS: frozenset[str] = frozenset(
    {
        "gravel-other",
        "fix-other-bike",
    }
)

_SELLER = ("Частное лицо", "Магазин")
BICYCLE_YEAR_MIN = 1980

# Canonical inches; storage value without unit; display adds ″ in Flutter/options.
WHEEL_SIZE_VALUES: tuple[str, ...] = (
    "12",
    "14",
    "16",
    "18",
    "20",
    "24",
    "26",
    "27.5",
    "28",
    "29",
)

# Curated frame contract: letter codes + common inch top-tube sizes (BMX/teen).
FRAME_SIZE_VALUES: tuple[str, ...] = (
    "XS",
    "S",
    "M",
    "L",
    "XL",
    "XXL",
    "15",
    "16",
    "17",
    "18",
    "18.5",
    "19",
    "20",
    "20.5",
    "21",
)

FRAME_MATERIAL_CHOICES: tuple[str, ...] = (
    "Алюминий",
    "Сталь",
    "Карбон",
    "Другое",
)

BRAKES_CHOICES: tuple[str, ...] = (
    "Дисковые механические",
    "Дисковые гидравлические",
    "Ободные",
    "Другие",
)

SUSPENSION_CHOICES: tuple[str, ...] = (
    "Без амортизации",
    "Хардтейл",
    "Двухподвес",
)

GEARS_CHOICES: tuple[str, ...] = (
    "1",
    "3",
    "6",
    "7",
    "8",
    "9",
    "10",
    "11",
    "12",
    "18",
    "21",
    "24",
    "27",
)

BICYCLE_FORBIDDEN_FIELD_KEYS: frozenset[str] = frozenset(
    {
        "electric_assist",
        "age_group",
        "bike_type",
        "bike_power",
        "ebike_range",
        "ebike_battery",
        "engine_cc",
        "engine_volume",
        "fuel",
        "mileage",
        "power_kw",
        "battery_capacity",
    }
)


def _choices(*labels: str) -> dict[str, Any]:
    items = [{"value": x, "label": x} for x in labels]
    return {"choices": items, "values": items}


def _wheel_choices() -> dict[str, Any]:
    items = [{"value": v, "label": f"{v}″"} for v in WHEEL_SIZE_VALUES]
    return {"choices": items, "values": items, "unit": "in"}


def _frame_choices() -> dict[str, Any]:
    items: list[dict[str, str]] = []
    for v in FRAME_SIZE_VALUES:
        if v in {"XS", "S", "M", "L", "XL", "XXL"}:
            items.append({"value": v, "label": v})
        else:
            items.append({"value": v, "label": f'{v}"'})
    return {"choices": items, "values": items}


def _gears_choices() -> dict[str, Any]:
    items = [{"value": v, "label": v} for v in GEARS_CHOICES]
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


def _opt_cfg_items(items: list[dict[str, str]], **extra: Any) -> dict[str, Any]:
    cfg: dict[str, Any] = {"options": items}
    cfg.update(extra)
    return cfg


def _geo_head() -> list:
    return [
        _field("region", "Регион", CategoryFieldType.string, True, 0),
        _field("city", "Город", CategoryFieldType.city, True, 1),
    ]


def _brand_model() -> list:
    # Optional for all bicycle leaves (no-name / self-build / unknown).
    return [
        _field("brand", "Марка", CategoryFieldType.brand, False, 10),
        _field("model", "Модель", CategoryFieldType.model, False, 20),
    ]


def _condition_block(sort: int, *, needs_investment: bool = True) -> list:
    rows = [
        _field(
            "condition",
            "Состояние",
            CategoryFieldType.enum,
            True,
            sort,
            _choices(*CONDITION_V2_CHOICES),
        ),
    ]
    if needs_investment:
        rows.append(
            _field(
                "needs_investment",
                "Требует вложений",
                CategoryFieldType.enum,
                False,
                sort + 5,
                _choices(*YES_NO_CHOICES),
            )
        )
    return rows


def _bike_size_block(
    sort: int,
    *,
    include_frame: bool = True,
    frame_options: dict[str, Any] | None = None,
) -> list:
    rows = [
        _field(
            "wheel_size",
            "Диаметр колёс",
            CategoryFieldType.enum,
            False,
            sort,
            _wheel_choices(),
            "Дюймы",
        ),
    ]
    if include_frame:
        rows.append(
            _field(
                "frame_size",
                "Размер рамы",
                CategoryFieldType.enum,
                False,
                sort + 10,
                frame_options or _frame_choices(),
            )
        )
    return rows


def _bike_tech(
    sort: int,
    *,
    material: bool = True,
    brakes: bool = True,
    gears: bool = True,
    suspension: bool = False,
    foldable: bool = False,
) -> list:
    rows: list = []
    n = sort
    if material:
        rows.append(
            _field(
                "frame_material",
                "Материал рамы",
                CategoryFieldType.enum,
                False,
                n,
                _choices(*FRAME_MATERIAL_CHOICES),
            )
        )
        n += 10
    if brakes:
        rows.append(
            _field(
                "brakes",
                "Тормоза",
                CategoryFieldType.enum,
                False,
                n,
                _choices(*BRAKES_CHOICES),
            )
        )
        n += 10
    if gears:
        rows.append(
            _field(
                "gears",
                "Количество скоростей",
                CategoryFieldType.enum,
                False,
                n,
                _gears_choices(),
            )
        )
        n += 10
    if suspension:
        rows.append(
            _field(
                "suspension",
                "Подвеска",
                CategoryFieldType.enum,
                False,
                n,
                _choices(*SUSPENSION_CHOICES),
            )
        )
        n += 10
    if foldable:
        rows.append(
            _field(
                "foldable",
                "Складной",
                CategoryFieldType.enum,
                False,
                n,
                _choices(*YES_NO_CHOICES),
            )
        )
    return rows


def _year_color(sort: int, *, year: bool = True, color: bool = True) -> list:
    rows: list = []
    n = sort
    if year:
        rows.append(
            _field(
                "year",
                "Год выпуска",
                CategoryFieldType.year,
                False,
                n,
                {"min": BICYCLE_YEAR_MIN, "max_offset_years": 1},
            )
        )
        n += 10
    if color:
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


def _ebike_tech(sort: int) -> list:
    return [
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
        _field(
            "removable_battery",
            "Съёмная батарея",
            CategoryFieldType.enum,
            False,
            sort + 40,
            _choices(*YES_NO_CHOICES),
        ),
        _field(
            "max_speed_kmh",
            "Максимальная скорость",
            CategoryFieldType.number,
            False,
            sort + 50,
            SPEED_KMH_OPTIONS,
            "км/ч",
        ),
        _field(
            "charger_included",
            "Зарядное устройство в комплекте",
            CategoryFieldType.enum,
            False,
            sort + 60,
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


def _mtb_fields() -> list:
    return [
        *_geo_head(),
        *_brand_model(),
        *_bike_size_block(30),
        *_bike_tech(50, suspension=True),
        *_year_color(90),
        *_condition_block(110),
        *_commerce(130),
    ]


def _city_fields() -> list:
    return [
        *_geo_head(),
        *_brand_model(),
        *_bike_size_block(30),
        *_bike_tech(50, suspension=False, foldable=False),
        *_year_color(90),
        *_condition_block(110),
        *_commerce(130),
    ]


def _road_fields() -> list:
    return [
        *_geo_head(),
        *_brand_model(),
        *_bike_size_block(30),
        *_bike_tech(50, suspension=False),
        *_year_color(90),
        *_condition_block(110),
        *_commerce(130),
    ]


def _teen_fields() -> list:
    return [
        *_geo_head(),
        *_brand_model(),
        *_bike_size_block(30),
        *_bike_tech(50, material=False, suspension=False),
        *_year_color(90, year=False),
        *_condition_block(110),
        *_commerce(130),
    ]


def _bmx_fields() -> list:
    return [
        *_geo_head(),
        *_brand_model(),
        *_bike_size_block(30),
        *_bike_tech(50, gears=False, suspension=False),
        *_year_color(90, year=False),
        *_condition_block(110),
        *_commerce(130),
    ]


def _other_fields() -> list:
    return [
        *_geo_head(),
        *_brand_model(),
        *_bike_size_block(30),
        *_bike_tech(50, suspension=False, foldable=True),
        *_year_color(100),
        *_condition_block(120),
        *_commerce(140),
    ]


def _ebike_fields() -> list:
    return [
        *_geo_head(),
        *_brand_model(),
        *_bike_size_block(30),
        *_bike_tech(50, suspension=True),
        *_ebike_tech(100),
        *_year_color(170),
        *_condition_block(190),
        *_commerce(210),
    ]


BICYCLE_CORE_FIELDS_BY_SLUG: dict[str, list] = {
    "transport-bicycles-gornye-velosipedy": _mtb_fields(),
    "transport-bicycles-gorodskie-velosipedy": _city_fields(),
    "transport-bicycles-shosseynye-velosipedy": _road_fields(),
    "transport-bicycles-podrostkovye-velosipedy": _teen_fields(),
    "transport-bicycles-elektrovelosipedy": _ebike_fields(),
    "transport-bicycles-bmx": _bmx_fields(),
    "transport-bicycles-drugie": _other_fields(),
}


def _wheel_filter(sort: int) -> tuple:
    return _filt(
        "wheel_size",
        "Диаметр колёс",
        CategoryFilterType.multi_select,
        sort,
        _opt_cfg_items(
            [{"value": v, "label": f"{v}″"} for v in WHEEL_SIZE_VALUES]
        ),
    )


def _frame_filter(sort: int) -> tuple:
    items = []
    for v in FRAME_SIZE_VALUES:
        if v in {"XS", "S", "M", "L", "XL", "XXL"}:
            items.append({"value": v, "label": v})
        else:
            items.append({"value": v, "label": f'{v}"'})
    return _filt(
        "frame_size",
        "Размер рамы",
        CategoryFilterType.multi_select,
        sort,
        _opt_cfg_items(items),
    )


def _common_search(
    *,
    include_wheel: bool = True,
    include_frame: bool = True,
    include_material: bool = True,
    include_brakes: bool = True,
    include_gears: bool = False,
    include_suspension: bool = False,
    include_foldable: bool = False,
    include_power: bool = False,
    include_range: bool = False,
) -> list:
    rows: list = []
    sort_n = 10
    rows.append(_filt("brand", "Марка", CategoryFilterType.select, sort_n, {}))
    sort_n += 10
    rows.append(_filt("model", "Модель", CategoryFilterType.select, sort_n, {}))
    sort_n += 10
    rows.append(
        _filt("price", "Цена", CategoryFilterType.range, sort_n, {"unit": "KGS"})
    )
    sort_n += 10
    rows.append(_filt("region", "Регион", CategoryFilterType.select, sort_n, {}))
    sort_n += 10
    rows.append(_filt("city", "Город", CategoryFilterType.select, sort_n, {}))
    sort_n += 10
    if include_wheel:
        rows.append(_wheel_filter(sort_n))
        sort_n += 10
    if include_frame:
        rows.append(_frame_filter(sort_n))
        sort_n += 10
    if include_material:
        rows.append(
            _filt(
                "frame_material",
                "Материал рамы",
                CategoryFilterType.multi_select,
                sort_n,
                _opt_cfg(*FRAME_MATERIAL_CHOICES),
            )
        )
        sort_n += 10
    if include_brakes:
        rows.append(
            _filt(
                "brakes",
                "Тормоза",
                CategoryFilterType.multi_select,
                sort_n,
                _opt_cfg(*BRAKES_CHOICES),
            )
        )
        sort_n += 10
    if include_suspension:
        rows.append(
            _filt(
                "suspension",
                "Подвеска",
                CategoryFilterType.multi_select,
                sort_n,
                _opt_cfg(*SUSPENSION_CHOICES),
            )
        )
        sort_n += 10
    if include_gears:
        rows.append(
            _filt(
                "gears",
                "Количество скоростей",
                CategoryFilterType.multi_select,
                sort_n,
                _opt_cfg(*GEARS_CHOICES),
            )
        )
        sort_n += 10
    if include_foldable:
        rows.append(
            _filt(
                "foldable",
                "Складной",
                CategoryFilterType.select,
                sort_n,
                _opt_cfg(*YES_NO_CHOICES),
            )
        )
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


BICYCLE_SEARCH_FILTERS_BY_SLUG: dict[str, list] = {
    "transport-bicycles-gornye-velosipedy": _common_search(
        include_suspension=True,
        include_gears=True,
    ),
    "transport-bicycles-gorodskie-velosipedy": _common_search(
        include_gears=True,
    ),
    "transport-bicycles-shosseynye-velosipedy": _common_search(
        include_gears=True,
    ),
    "transport-bicycles-podrostkovye-velosipedy": _common_search(
        include_material=False,
        include_gears=True,
    ),
    "transport-bicycles-elektrovelosipedy": _common_search(
        include_suspension=True,
        include_gears=True,
        include_power=True,
        include_range=True,
    ),
    "transport-bicycles-bmx": _common_search(
        include_gears=False,
        include_suspension=False,
    ),
    "transport-bicycles-drugie": _common_search(
        include_foldable=True,
        include_gears=True,
    ),
}
