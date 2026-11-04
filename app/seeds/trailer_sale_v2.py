# -*- coding: utf-8 -*-
"""Transport → Прицепы и полуприцепы V2 — leaf Create/Search SoT.

Parent ``transport-trailers`` is picker-only.
Hybrid taxonomy:
- Прицепы → trailer_purpose
- Полуприцепы → semi_body_type (+ conditional tank/dump/lowbed fields)
- Жилые → separate leaf (sleeping_places / amenities)
Specialty L3 stay inactive. Boat/Farm remaps → Прицепы 1226.
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
from app.seeds.cargo_sale_v2 import TANKER_PURPOSES

TRAILER_PARENT_SLUG = "transport-trailers"

TRAILER_LEAF_SLUGS: tuple[str, ...] = (
    "transport-trailers-pritsepy",
    "transport-trailers-polupritsepy",
    "transport-trailers-zhilye-pritsepy-kempery",
)

TRAILER_LEAF_LABELS: dict[str, str] = {
    "transport-trailers-pritsepy": "Прицепы",
    "transport-trailers-polupritsepy": "Полуприцепы",
    "transport-trailers-zhilye-pritsepy-kempery": "Жилые прицепы / кемперы",
}

TRAILER_LEAF_SORT: dict[str, int] = {
    "transport-trailers-pritsepy": 10,
    "transport-trailers-polupritsepy": 20,
    "transport-trailers-zhilye-pritsepy-kempery": 30,
}

TRAILER_LEAF_VEHICLE_TYPE: dict[str, str] = {
    "transport-trailers-pritsepy": "drawbar_trailer",
    "transport-trailers-polupritsepy": "semi_trailer",
    "transport-trailers-zhilye-pritsepy-kempery": "camper_trailer",
}

TRAILER_INACTIVE_LEGACY_SLUGS: tuple[str, ...] = (
    "transport-trailers-dlya-legkovyh-avtomobiley",
    "transport-trailers-gruzovye-pritsepy",
    "transport-trailers-samosvalnye-pritsepy",
    "transport-trailers-tentovannye-pritsepy",
    "transport-trailers-refrizheratornye-pritsepy",
    "transport-trailers-tsisterny",
    "transport-trailers-traly-i-nizkoramnye",
    "transport-trailers-spetsializirovannye-pritsepy",
    "transport-trailers-zapchasti-i-komplektuyuschie",
    "transport-trailers-remont-i-obsluzhivanie",
    "transport-watercraft-pritsepy-dlya-vodnogo-transporta",
    "transport-farm-machinery-pritsepy-dlya-selhoztehniki",
)

# Canonical remap targets (source stays inactive).
TRAILER_REMAP_TARGETS: dict[str, str] = {
    "transport-watercraft-pritsepy-dlya-vodnogo-transporta": (
        "transport-trailers-pritsepy"
    ),
    "transport-farm-machinery-pritsepy-dlya-selhoztehniki": (
        "transport-trailers-pritsepy"
    ),
}

TRAILER_LEAF_ALIASES: dict[str, str] = {
    "прицеп": "transport-trailers-pritsepy",
    "легковое прицеп": "transport-trailers-pritsepy",
    "лодочный прицеп": "transport-trailers-pritsepy",
    "прицеп для лодки": "transport-trailers-pritsepy",
    "сельхозприцеп": "transport-trailers-pritsepy",
    "полуприцеп": "transport-trailers-polupritsepy",
    "шторный полуприцеп": "transport-trailers-polupritsepy",
    "трал": "transport-trailers-polupritsepy",
    "низкорамный": "transport-trailers-polupritsepy",
    "жилой прицеп": "transport-trailers-zhilye-pritsepy-kempery",
    "караван": "transport-trailers-zhilye-pritsepy-kempery",
    "кемпер прицеп": "transport-trailers-zhilye-pritsepy-kempery",
}

TRAILER_PARENT_ALIASES: dict[str, str] = {
    "прицепы": TRAILER_PARENT_SLUG,
    "прицепы и полуприцепы": TRAILER_PARENT_SLUG,
}

_SELLER = ("Частное лицо", "Компания", "Дилер")

TRAILER_PURPOSES: tuple[str, ...] = (
    "Для легкового автомобиля",
    "Грузовой",
    "Для лодки",
    "Для мототехники",
    "Для спецтехники",
    "Сельскохозяйственный",
    "Другой",
)

SEMI_BODY_TYPES: tuple[str, ...] = (
    "Тентованный / шторный",
    "Рефрижератор",
    "Цистерна",
    "Самосвальный",
    "Контейнеровоз",
    "Автовоз",
    "Трал / низкорамный",
    "Платформа",
    "Другой",
)

# Canonical stored values (ASCII ints as strings). Labels are RU display.
AXLE_COUNT_VALUES: tuple[str, ...] = ("1", "2", "3", "4", "5")
AXLE_COUNT_LABELS: dict[str, str] = {
    "1": "1 ось",
    "2": "2 оси",
    "3": "3 оси",
    "4": "4 оси",
    "5": "5 и более",  # sentinel: 5+
}
AXLE_COUNT_SENTINEL_5_PLUS = "5"

SUSPENSION_OPTIONS: tuple[str, ...] = (
    "Пневматическая",
    "Рессорная",
    "Другая",
)

BRAKES_OPTIONS: tuple[str, ...] = ("Есть", "Нет")

CARAVAN_AMENITIES: tuple[str, ...] = (
    "Кухня",
    "Туалет",
    "Душ",
    "Холодильник",
    "Отопление",
    "Кондиционер",
)

TRAILER_OTHER_BRAND_TYPES: tuple[str, ...] = (
    "drawbar_trailer",
    "semi_trailer",
    "camper_trailer",
)

TRAILER_YEAR_MIN = 1970
LOAD_KG_MAX = 500_000
BODY_M3_MAX = 200
TANK_L_MAX = 80_000
LENGTH_M_MAX = 50
SLEEPING_MAX = 12


def _choices(*labels: str) -> dict[str, Any]:
    items = [{"value": x, "label": x} for x in labels]
    return {"choices": items, "values": items}


def _axle_choices() -> dict[str, Any]:
    items = [
        {"value": v, "label": AXLE_COUNT_LABELS[v]} for v in AXLE_COUNT_VALUES
    ]
    return {"choices": items, "values": items}


def _axle_opt_cfg() -> dict[str, Any]:
    return {
        "options": [
            {"value": v, "label": AXLE_COUNT_LABELS[v]}
            for v in AXLE_COUNT_VALUES
        ]
    }


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
            {"min": TRAILER_YEAR_MIN, "max_offset_years": 1},
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


def _axle_count(sort: int) -> list:
    return [
        _field(
            "axle_count",
            "Количество осей",
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


def _length(
    sort: int,
    *,
    depends_on_lowbed: bool = False,
) -> list:
    opts: dict[str, Any] = {
        "min": 0,
        "max": LENGTH_M_MAX,
        "unit": "m",
    }
    if depends_on_lowbed:
        opts["depends_on"] = {
            "field": "semi_body_type",
            "values": ["Трал / низкорамный"],
        }
    return [
        _field(
            "length_m",
            "Длина",
            CategoryFieldType.decimal,
            False,
            sort,
            opts,
            "Длина в метрах",
        ),
    ]


def _body_volume(sort: int, *, depends_on_dump: bool = False) -> list:
    opts: dict[str, Any] = {
        "min": 0,
        "max": BODY_M3_MAX,
        "unit": "m³",
    }
    if depends_on_dump:
        opts["depends_on"] = {
            "field": "semi_body_type",
            "values": ["Самосвальный"],
        }
    return [
        _field(
            "body_volume_m3",
            "Объём кузова",
            CategoryFieldType.decimal,
            False,
            sort,
            opts,
            "Объём кузова в м³",
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
            {
                "min": 0,
                "max": TANK_L_MAX,
                "unit": "L",
                "integer": True,
                "depends_on": {
                    "field": "semi_body_type",
                    "values": ["Цистерна"],
                },
            },
            "Объём цистерны в литрах",
        ),
    ]


def _tanker_purpose(sort: int) -> list:
    opts = _choices(*TANKER_PURPOSES)
    opts = {
        **opts,
        "depends_on": {
            "field": "semi_body_type",
            "values": ["Цистерна"],
        },
    }
    return [
        _field(
            "tanker_purpose",
            "Назначение цистерны",
            CategoryFieldType.enum,
            False,
            sort,
            opts,
        ),
    ]


def _drawbar_fields() -> list:
    return [
        *_geo_head(),
        _field(
            "trailer_purpose",
            "Назначение прицепа",
            CategoryFieldType.enum,
            False,
            8,
            _choices(*TRAILER_PURPOSES),
        ),
        *_brand_model(10),
        *_year(25),
        *_axle_count(30),
        *_load_capacity(40),
        *_length(50),
        _field(
            "brakes",
            "Тормоза",
            CategoryFieldType.enum,
            False,
            60,
            _choices(*BRAKES_OPTIONS),
        ),
        *_condition_block(100),
        *_commerce(120),
    ]


def _semi_fields() -> list:
    return [
        *_geo_head(),
        _field(
            "semi_body_type",
            "Тип полуприцепа",
            CategoryFieldType.enum,
            False,
            8,
            _choices(*SEMI_BODY_TYPES),
        ),
        *_brand_model(10),
        *_year(25),
        *_axle_count(30),
        *_load_capacity(40),
        _field(
            "suspension",
            "Подвеска",
            CategoryFieldType.enum,
            False,
            45,
            _choices(*SUSPENSION_OPTIONS),
        ),
        *_tank_capacity(50),
        *_tanker_purpose(55),
        *_body_volume(60, depends_on_dump=True),
        *_length(70, depends_on_lowbed=True),
        *_condition_block(100),
        *_commerce(120),
    ]


def _camper_fields() -> list:
    return [
        *_geo_head(),
        *_brand_model(10),
        *_year(25),
        *_axle_count(30),
        _field(
            "sleeping_places",
            "Спальных мест",
            CategoryFieldType.number,
            False,
            40,
            {
                "min": 1,
                "max": SLEEPING_MAX,
                "unit": "мест",
                "integer": True,
            },
        ),
        *_length(50),
        _field(
            "amenities",
            "Оснащение",
            CategoryFieldType.multi_select,
            False,
            60,
            _choices(*CARAVAN_AMENITIES),
        ),
        *_condition_block(100),
        *_commerce(120),
    ]


TRAILER_CORE_FIELDS_BY_SLUG: dict[str, list] = {
    "transport-trailers-pritsepy": _drawbar_fields(),
    "transport-trailers-polupritsepy": _semi_fields(),
    "transport-trailers-zhilye-pritsepy-kempery": _camper_fields(),
}


def _common_search_head(*, sort: int = 10) -> list:
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


def _drawbar_search() -> list:
    return [
        *_common_search_head(),
        *_condition_seller_sort(100),
        _filt(
            "trailer_purpose",
            "Назначение прицепа",
            CategoryFilterType.multi_select,
            200,
            _opt_cfg(*TRAILER_PURPOSES),
        ),
        _filt(
            "axle_count",
            "Количество осей",
            CategoryFilterType.multi_select,
            210,
            _axle_opt_cfg(),
        ),
        _filt(
            "load_capacity_kg",
            "Грузоподъёмность",
            CategoryFilterType.range,
            220,
            {"unit": "kg", "mode": "min"},
        ),
        _filt(
            "length_m",
            "Длина",
            CategoryFilterType.range,
            230,
            {"unit": "m"},
        ),
    ]


def _semi_search() -> list:
    return [
        *_common_search_head(),
        *_condition_seller_sort(100),
        _filt(
            "semi_body_type",
            "Тип полуприцепа",
            CategoryFilterType.multi_select,
            200,
            _opt_cfg(*SEMI_BODY_TYPES),
        ),
        _filt(
            "axle_count",
            "Количество осей",
            CategoryFilterType.multi_select,
            210,
            _axle_opt_cfg(),
        ),
        _filt(
            "load_capacity_kg",
            "Грузоподъёмность",
            CategoryFilterType.range,
            220,
            {"unit": "kg", "mode": "min"},
        ),
        _filt(
            "suspension",
            "Подвеска",
            CategoryFilterType.multi_select,
            230,
            _opt_cfg(*SUSPENSION_OPTIONS),
        ),
        _filt(
            "tank_capacity_l",
            "Объём цистерны",
            CategoryFilterType.range,
            240,
            {
                "unit": "L",
                "mode": "min",
                "depends_on": {
                    "field": "semi_body_type",
                    "values": ["Цистерна"],
                },
            },
        ),
        _filt(
            "tanker_purpose",
            "Назначение цистерны",
            CategoryFilterType.multi_select,
            250,
            _opt_cfg(
                *TANKER_PURPOSES,
                depends_on={
                    "field": "semi_body_type",
                    "values": ["Цистерна"],
                },
            ),
        ),
        _filt(
            "body_volume_m3",
            "Объём кузова",
            CategoryFilterType.range,
            260,
            {
                "unit": "m³",
                "mode": "min",
                "depends_on": {
                    "field": "semi_body_type",
                    "values": ["Самосвальный"],
                },
            },
        ),
        _filt(
            "length_m",
            "Длина",
            CategoryFilterType.range,
            270,
            {
                "unit": "m",
                "depends_on": {
                    "field": "semi_body_type",
                    "values": ["Трал / низкорамный"],
                },
            },
        ),
    ]


def _camper_search() -> list:
    return [
        *_common_search_head(),
        *_condition_seller_sort(100),
        _filt(
            "sleeping_places",
            "Спальных мест",
            CategoryFilterType.range,
            200,
            {"unit": "мест", "mode": "min"},
        ),
        _filt(
            "length_m",
            "Длина",
            CategoryFilterType.range,
            210,
            {"unit": "m"},
        ),
        _filt(
            "amenities",
            "Оснащение",
            CategoryFilterType.multi_select,
            220,
            _opt_cfg(*CARAVAN_AMENITIES),
        ),
        _filt(
            "axle_count",
            "Количество осей",
            CategoryFilterType.multi_select,
            230,
            _axle_opt_cfg(),
        ),
    ]


TRAILER_SEARCH_FILTERS_BY_SLUG: dict[str, list] = {
    "transport-trailers-pritsepy": _drawbar_search(),
    "transport-trailers-polupritsepy": _semi_search(),
    "transport-trailers-zhilye-pritsepy-kempery": _camper_search(),
}


def trailer_other_brands() -> list[tuple[str, str, str | None, str]]:
    out: list[tuple[str, str, str | None, str]] = []
    for vt in TRAILER_OTHER_BRAND_TYPES:
        out.append((f"other-{vt.replace('_', '-')}", "Другая марка", None, vt))
    return out


def trailer_other_models() -> dict[str, list[tuple[str, str]]]:
    return {
        f"other-{vt.replace('_', '-')}": [("other-model", "Другая модель")]
        for vt in TRAILER_OTHER_BRAND_TYPES
    }
