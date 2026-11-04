# -*- coding: utf-8 -*-
"""Transport → Мототехника V2 — leaf Create/Search vocabulary (Backend SoT).

Active leaves only. Parent ``transport-moto-tech`` is picker-only
(no live Create/Search SoT on the parent).
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

MOTO_PARENT_SLUG = "transport-moto-tech"

# Stable IDs/slugs preserved; display labels may be renamed.
MOTO_LEAF_SLUGS: tuple[str, ...] = (
    "transport-moto-tech-mototsikly",
    "transport-moto-tech-skutery-i-mopedy",
    "transport-moto-tech-motorollery-muravey",
    "transport-moto-tech-kvadrotsikly",
    "transport-moto-tech-baggi",
    "transport-moto-tech-tritsikly",
    "transport-moto-tech-snegohody",
    "transport-moto-tech-karty",
    "transport-moto-tech-drugaya-mototehnika",
)

MOTO_LEAF_LABELS: dict[str, str] = {
    "transport-moto-tech-mototsikly": "Мотоциклы",
    "transport-moto-tech-skutery-i-mopedy": "Скутеры и мопеды",
    "transport-moto-tech-motorollery-muravey": "Мотороллеры «Муравей»",
    "transport-moto-tech-kvadrotsikly": "Квадроциклы",
    "transport-moto-tech-baggi": "Багги",
    "transport-moto-tech-tritsikly": "Трициклы",
    "transport-moto-tech-snegohody": "Снегоходы",
    "transport-moto-tech-karty": "Картинги",
    "transport-moto-tech-drugaya-mototehnika": "Другая мототехника",
}

MOTO_LEAF_VEHICLE_TYPE: dict[str, str] = {
    "transport-moto-tech-mototsikly": "motorcycle",
    "transport-moto-tech-skutery-i-mopedy": "scooter",
    "transport-moto-tech-motorollery-muravey": "motoroller",
    "transport-moto-tech-kvadrotsikly": "atv",
    "transport-moto-tech-baggi": "buggy",
    "transport-moto-tech-tritsikly": "tricycle",
    "transport-moto-tech-snegohody": "snowmobile",
    "transport-moto-tech-karty": "kart",
    "transport-moto-tech-drugaya-mototehnika": "other_moto",
}

# Parts / services / duplicate e-scooter remain inactive under Moto.
# E-motorcycle / e-ATV live under Electric V2 (same slug IDs, re-parented).
MOTO_INACTIVE_LEGACY_SLUGS: frozenset[str] = frozenset(
    {
        "transport-moto-tech-elektroskutery",
        "transport-moto-tech-zapchasti-dlya-mototehniki",
        "transport-moto-tech-ekipirovka-i-aksessuary",
        "transport-moto-tech-motouslugi",
    }
)

# ICE-only active Moto V2: electric motorcycles/scooters stay under Электротранспорт.
# No ``fuel`` field on Moto leaves (would be single-option «Бензин» or taxonomy overlap).

_TRANSMISSION = ("Механика", "Автомат", "Вариатор")
_DRIVE = ("2WD", "4WD")
_DOCUMENTS = ("Есть", "Нет")
_SELLER = ("Частное лицо", "Мотосалон", "Дилер")

# Discrete cc picker. Sentinel 1501 = «Более 1500 см³» (numeric range compatible).
ENGINE_CC_VALUES: tuple[int, ...] = (
    50,
    70,
    90,
    110,
    125,
    150,
    200,
    250,
    300,
    400,
    500,
    600,
    650,
    750,
    800,
    900,
    1000,
    1200,
    1500,
)
ENGINE_CC_OVER_MAX_VALUE = 1501
ENGINE_CC_OVER_MAX_LABEL = "Более 1500 см³"
ENGINE_CC_EXACT_MAX = 1500
# Year floor aligned with shared vehicle year hard validation (1960).
MOTO_YEAR_MIN = 1960


def _choices(*labels: str) -> dict[str, Any]:
    items = [{"value": x, "label": x} for x in labels]
    return {"choices": items, "values": items}


def _engine_cc_choice_items() -> list[dict[str, str]]:
    items = [
        {"value": str(v), "label": f"{v} см³"} for v in ENGINE_CC_VALUES
    ]
    items.append(
        {
            "value": str(ENGINE_CC_OVER_MAX_VALUE),
            "label": ENGINE_CC_OVER_MAX_LABEL,
        }
    )
    return items


def _engine_cc_options() -> dict[str, Any]:
    items = _engine_cc_choice_items()
    return {
        "choices": items,
        "values": items,
        "min": ENGINE_CC_VALUES[0],
        "max": ENGINE_CC_OVER_MAX_VALUE,
        "unit": "cc",
        "over_max_value": str(ENGINE_CC_OVER_MAX_VALUE),
        "over_max_label": ENGINE_CC_OVER_MAX_LABEL,
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


def _base_head(*, engine_cc_required: bool) -> list:
    return [
        _field("region", "Регион", CategoryFieldType.string, True, 0),
        _field("city", "Город", CategoryFieldType.city, True, 1),
        _field("brand", "Марка", CategoryFieldType.brand, True, 10),
        _field("model", "Модель", CategoryFieldType.model, True, 20),
        _field(
            "year",
            "Год выпуска",
            CategoryFieldType.year,
            True,
            30,
            {"min": MOTO_YEAR_MIN, "max_offset_years": 1},
        ),
        _field(
            "engine_cc",
            "Объём двигателя",
            CategoryFieldType.number,
            engine_cc_required,
            40,
            _engine_cc_options(),
            "Объём в см³",
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
            True,
            sort + 10,
            _choices(*YES_NO_CHOICES),
        ),
    ]


def _commerce_full(sort: int) -> list:
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
            True,
            sort + 20,
            _choices(*EXCHANGE_CHOICES),
        ),
        _field(
            "installment",
            "Возможность рассрочки",
            CategoryFieldType.enum,
            True,
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


def _commerce_minimal(sort: int) -> list:
    """Kart / other — no exchange/installment."""
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
            "seller_type",
            "Кто продаёт",
            CategoryFieldType.enum,
            True,
            sort + 20,
            _choices(*_SELLER),
        ),
        _field(
            "contact_methods",
            "Способы связи",
            CategoryFieldType.enum,
            True,
            sort + 30,
            _choices(*CONTACT_METHOD_CHOICES),
        ),
    ]


def _docs_accident(sort: int) -> list:
    return [
        _field(
            "after_accident",
            "После ДТП",
            CategoryFieldType.enum,
            True,
            sort,
            _choices(*YES_NO_CHOICES),
        ),
        _field(
            "documents",
            "Документы",
            CategoryFieldType.enum,
            True,
            sort + 10,
            _choices(*_DOCUMENTS),
        ),
    ]


def _motorcycle_fields() -> list:
    return [
        *_base_head(engine_cc_required=True),
        _field(
            "transmission",
            "Коробка передач",
            CategoryFieldType.enum,
            True,
            50,
            _choices(*_TRANSMISSION),
        ),
        _field(
            "color",
            "Цвет",
            CategoryFieldType.enum,
            True,
            60,
            _choices(*VEHICLE_COLOR_CHOICES),
        ),
        *_condition_block(70),
        *_docs_accident(90),
        *_commerce_full(110),
    ]


def _scooter_fields() -> list:
    return [
        *_base_head(engine_cc_required=True),
        _field(
            "color",
            "Цвет",
            CategoryFieldType.enum,
            True,
            50,
            _choices(*VEHICLE_COLOR_CHOICES),
        ),
        *_condition_block(60),
        *_docs_accident(80),
        *_commerce_full(100),
    ]


def _muravey_fields() -> list:
    return _scooter_fields()


def _atv_or_buggy_fields() -> list:
    return [
        *_base_head(engine_cc_required=True),
        _field(
            "drive",
            "Привод",
            CategoryFieldType.enum,
            True,
            50,
            _choices(*_DRIVE),
        ),
        _field(
            "color",
            "Цвет",
            CategoryFieldType.enum,
            True,
            60,
            _choices(*VEHICLE_COLOR_CHOICES),
        ),
        *_condition_block(70),
        *_commerce_full(90),
    ]


def _tricycle_fields() -> list:
    return _scooter_fields()


def _snowmobile_fields() -> list:
    return [
        *_base_head(engine_cc_required=True),
        _field(
            "color",
            "Цвет",
            CategoryFieldType.enum,
            True,
            50,
            _choices(*VEHICLE_COLOR_CHOICES),
        ),
        *_condition_block(60),
        *_commerce_full(80),
    ]


def _kart_fields() -> list:
    return [
        *_base_head(engine_cc_required=True),
        *_condition_block(50),
        *_commerce_minimal(70),
    ]


def _other_moto_fields() -> list:
    return [
        *_base_head(engine_cc_required=False),
        _field(
            "color",
            "Цвет",
            CategoryFieldType.enum,
            True,
            50,
            _choices(*VEHICLE_COLOR_CHOICES),
        ),
        *_condition_block(60),
        *_commerce_minimal(80),
    ]


MOTO_CORE_FIELDS_BY_SLUG: dict[str, list] = {
    "transport-moto-tech-mototsikly": _motorcycle_fields(),
    "transport-moto-tech-skutery-i-mopedy": _scooter_fields(),
    "transport-moto-tech-motorollery-muravey": _muravey_fields(),
    "transport-moto-tech-kvadrotsikly": _atv_or_buggy_fields(),
    "transport-moto-tech-baggi": _atv_or_buggy_fields(),
    "transport-moto-tech-tritsikly": _tricycle_fields(),
    "transport-moto-tech-snegohody": _snowmobile_fields(),
    "transport-moto-tech-karty": _kart_fields(),
    "transport-moto-tech-drugaya-mototehnika": _other_moto_fields(),
}


def _common_search_filters(
    *,
    include_engine_cc: bool = True,
    extra: list | None = None,
) -> list:
    rows = [
        _filt("brand", "Марка", CategoryFilterType.select, 10, {}),
        _filt("model", "Модель", CategoryFilterType.select, 20, {}),
        _filt("price", "Цена", CategoryFilterType.range, 30, {"unit": "KGS"}),
        _filt("year", "Год выпуска", CategoryFilterType.range, 40, {}),
        _filt("region", "Регион", CategoryFilterType.select, 50, {}),
        _filt("city", "Город", CategoryFilterType.select, 60, {}),
    ]
    sort_n = 70
    if include_engine_cc:
        rows.append(
            _filt(
                "engine_cc",
                "Объём двигателя",
                CategoryFilterType.range,
                sort_n,
                {"unit": "cc"},
            )
        )
        sort_n += 10
    if extra:
        for item in extra:
            key, label, ftype, _ignored_sort, config = item
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
                "needs_investment",
                "Требует вложений",
                CategoryFilterType.select,
                sort_n + 10,
                _opt_cfg(*YES_NO_CHOICES),
            ),
            _filt(
                "seller_type",
                "Кто продаёт",
                CategoryFilterType.multi_select,
                sort_n + 20,
                _opt_cfg(*_SELLER),
            ),
            _filt(
                "sort",
                "Сортировка",
                CategoryFilterType.select,
                sort_n + 40,
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


MOTO_SEARCH_FILTERS_BY_SLUG: dict[str, list] = {
    "transport-moto-tech-mototsikly": _common_search_filters(
        extra=[
            _filt(
                "transmission",
                "Коробка передач",
                CategoryFilterType.multi_select,
                0,
                _opt_cfg(*_TRANSMISSION),
            ),
        ]
    ),
    "transport-moto-tech-skutery-i-mopedy": _common_search_filters(),
    "transport-moto-tech-motorollery-muravey": _common_search_filters(),
    "transport-moto-tech-kvadrotsikly": _common_search_filters(
        extra=[
            _filt(
                "drive",
                "Привод",
                CategoryFilterType.multi_select,
                0,
                _opt_cfg(*_DRIVE),
            ),
        ]
    ),
    "transport-moto-tech-baggi": _common_search_filters(
        extra=[
            _filt(
                "drive",
                "Привод",
                CategoryFilterType.multi_select,
                0,
                _opt_cfg(*_DRIVE),
            ),
        ]
    ),
    "transport-moto-tech-tritsikly": _common_search_filters(),
    "transport-moto-tech-snegohody": _common_search_filters(),
    "transport-moto-tech-karty": _common_search_filters(),
    "transport-moto-tech-drugaya-mototehnika": _common_search_filters(),
}

# Keys that must never appear on any Moto V2 leaf.
MOTO_FORBIDDEN_FIELD_KEYS: frozenset[str] = frozenset(
    {
        "mileage",
        "mileage_unit",
        "engine_hours",
        "moto_hours",
        "engine_volume",
        "powertrain",
        "registration_country",
        "available_in_kg",
        "customs_cleared_kg",
        "taxes_paid",
        "steering_side",
        "fresh_import",
    }
)
