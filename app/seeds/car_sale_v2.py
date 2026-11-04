# -*- coding: utf-8 -*-
"""Transport → Продажа авто V2 — Create/Search vocabulary (Backend SoT)."""
from __future__ import annotations

from typing import Any

from app.models.category_enums import CategoryFieldType, CategoryFilterType

CAR_SALE_SLUG = "transport-car-sale"

_STEERING = ("Левый руль", "Правый руль")
_TRANSMISSION = (
    "Автомат",
    "Механика",
    "Вариатор (CVT)",
    "Робот",
    "Типтроник",
)
_DRIVE = ("Передний", "Задний", "Полный")
_FUEL = (
    "Бензин",
    "Дизель",
    "Газ",
    "Бензин + Газ",
    "Гибрид",
    "Plug-in Hybrid",
    "Электро",
    "Водород",
)
_COLOR = (
    "Белый",
    "Чёрный",
    "Серый",
    "Серебристый",
    "Синий",
    "Красный",
    "Зелёный",
    "Бежевый",
    "Коричневый",
    "Жёлтый",
    "Оранжевый",
    "Фиолетовый",
    "Золотистый",
    "Другой",
)
_CONDITION = ("Новое", "Отличное", "Хорошее", "Удовлетворительное")
# Shared vehicle vocabularies for other Transport V2 leaves (Moto, …).
VEHICLE_COLOR_CHOICES = _COLOR
CONDITION_V2_CHOICES = _CONDITION
YES_NO_CHOICES = ("Да", "Нет")
NEGOTIABLE_CHOICES = ("Есть торг", "Без торга")
EXCHANGE_CHOICES = ("Возможно", "Обмена нет")
INSTALLMENT_CHOICES = ("Есть", "Нет")
CONTACT_METHOD_CHOICES = (
    "Только чат",
    "Только телефон",
    "Чат + телефон",
    "Чат + Wapp",
    "Телефон + Wapp",
    "Чат + Тел. + Wapp",
)
_YES_NO = YES_NO_CHOICES
_REGISTRATION = (
    "Кыргызстан",
    "Казахстан",
    "Россия",
    "Грузия",
    "Армения",
    "Узбекистан",
    "Германия",
    "Япония",
    "Корея",
    "США",
    "Китай",
    "ОАЭ",
    "Другая",
)
_AVAILABLE = ("В наличии", "В пути", "На заказ")
_TAXES = ("Оплачены", "Не оплачены")
_NEGOTIABLE = NEGOTIABLE_CHOICES
_EXCHANGE = EXCHANGE_CHOICES
_INSTALLMENT = INSTALLMENT_CHOICES
_SELLER = ("Собственник", "Автоброкер", "Автосалон", "Дилер")
_CONTACTS = CONTACT_METHOD_CHOICES

# Allowed only to keep historical edit payloads from being rejected when the
# client re-sends an already-stored legacy condition/steering spelling.
# Canonical V2 Create options remain the SoT for NEW values — do NOT add
# "Полный (4WD/AWD)" here (must reject as a new stored drive identity).
LEGACY_ENUM_ALLOW: dict[str, frozenset[str]] = {
    "condition": frozenset(
        {"Идеальное", "Нужен ремонт", "После ДТП", "Новое", "Хорошее"}
    ),
    "steering_side": frozenset({"Левый", "Правый", "left", "right"}),
}

DEPRECATED_CREATE_KEYS: frozenset[str] = frozenset({"fresh_import"})


def _choices(*labels: str) -> dict[str, Any]:
    items = [{"value": x, "label": x} for x in labels]
    return {"choices": items, "values": items}


# Canonical numeric sentinel for Create option «Более 5.0».
# Stored as value_decimal 5.1 so Search range queries stay numeric
# (e.g. engine_volume__min=5.1 → FOUND; __max=5.0 → NOT FOUND).
ENGINE_VOLUME_OVER_5_VALUE = "5.1"
ENGINE_VOLUME_OVER_5_LABEL = "Более 5.0"
ENGINE_VOLUME_MIN = "0.3"
ENGINE_VOLUME_EXACT_MAX = "5.0"


def _engine_volume_choice_items() -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    tenths = 3  # 0.3
    while tenths <= 50:  # 5.0 inclusive
        value = f"{tenths / 10:.1f}"
        items.append({"value": value, "label": value})
        tenths += 1
    items.append(
        {
            "value": ENGINE_VOLUME_OVER_5_VALUE,
            "label": ENGINE_VOLUME_OVER_5_LABEL,
        }
    )
    return items


def _engine_volume_options() -> dict[str, Any]:
    """Picker SoT: 0.3–5.0 step 0.1 + «Более 5.0»→5.1; hide when fuel=Электро."""
    items = _engine_volume_choice_items()
    return {
        "depends_on": {
            "field": "fuel",
            "hide_values": ["Электро"],
            "show_when_empty": True,
        },
        "choices": items,
        "values": items,
        "min": float(ENGINE_VOLUME_MIN),
        "max": float(ENGINE_VOLUME_OVER_5_VALUE),
        "step": 0.1,
        "over_max_value": ENGINE_VOLUME_OVER_5_VALUE,
        "over_max_label": ENGINE_VOLUME_OVER_5_LABEL,
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


CAR_SALE_CORE_FIELDS: list[
    tuple[str, str, CategoryFieldType, bool, int, dict[str, Any] | None, str | None]
] = [
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
        {"min": 1960, "max_offset_years": 1},
    ),
    _field(
        "steering_side",
        "Руль",
        CategoryFieldType.enum,
        True,
        40,
        _choices(*_STEERING),
    ),
    _field(
        "engine_volume",
        "Объём двигателя",
        CategoryFieldType.decimal,
        True,
        50,
        _engine_volume_options(),
        "Объём в литрах (шаг 0.1)",
    ),
    _field(
        "transmission",
        "Коробка передач",
        CategoryFieldType.enum,
        True,
        60,
        _choices(*_TRANSMISSION),
    ),
    _field("drive", "Привод", CategoryFieldType.enum, True, 70, _choices(*_DRIVE)),
    _field("fuel", "Топливо", CategoryFieldType.enum, True, 80, _choices(*_FUEL)),
    _field("color", "Цвет", CategoryFieldType.enum, True, 90, _choices(*_COLOR)),
    _field(
        "mileage",
        "Пробег, км",
        CategoryFieldType.number,
        True,
        100,
        {"min": 0, "max": 2_000_000},
        "Пробег в километрах",
    ),
    _field(
        "condition",
        "Состояние",
        CategoryFieldType.enum,
        True,
        110,
        _choices(*_CONDITION),
    ),
    _field(
        "needs_investment",
        "Требует вложений",
        CategoryFieldType.enum,
        True,
        120,
        _choices(*_YES_NO),
    ),
    _field(
        "after_accident",
        "После ДТП",
        CategoryFieldType.enum,
        True,
        130,
        _choices(*_YES_NO),
    ),
    _field(
        "registration_country",
        "Страна учёта",
        CategoryFieldType.enum,
        True,
        140,
        _choices(*_REGISTRATION),
    ),
    _field(
        "available_in_kg",
        "Наличие в КР",
        CategoryFieldType.enum,
        True,
        150,
        _choices(*_AVAILABLE),
    ),
    _field(
        "customs_cleared_kg",
        "Растаможен в КР",
        CategoryFieldType.enum,
        True,
        160,
        _choices(*_YES_NO),
    ),
    _field(
        "taxes_paid",
        "Налог и штрафы",
        CategoryFieldType.enum,
        True,
        170,
        _choices(*_TAXES),
    ),
    _field("price", "Цена", CategoryFieldType.price, True, 180),
    _field(
        "negotiable",
        "Возможность торга",
        CategoryFieldType.enum,
        True,
        190,
        _choices(*_NEGOTIABLE),
    ),
    _field(
        "exchange",
        "Возможность обмена",
        CategoryFieldType.enum,
        True,
        200,
        _choices(*_EXCHANGE),
    ),
    _field(
        "installment",
        "Возможность рассрочки",
        CategoryFieldType.enum,
        True,
        210,
        _choices(*_INSTALLMENT),
    ),
    _field(
        "seller_type",
        "Кто продаёт",
        CategoryFieldType.enum,
        True,
        220,
        _choices(*_SELLER),
    ),
    _field(
        "contact_methods",
        "Способы связи",
        CategoryFieldType.enum,
        True,
        230,
        _choices(*_CONTACTS),
    ),
]


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


CAR_SALE_SEARCH_FILTERS: list[
    tuple[str, str, CategoryFilterType, int, dict[str, Any] | None]
] = [
    _filt("brand", "Марка", CategoryFilterType.select, 10, {}),
    _filt("model", "Модель", CategoryFilterType.select, 20, {}),
    _filt("price", "Цена", CategoryFilterType.range, 30, {"unit": "KGS"}),
    _filt("year", "Год выпуска", CategoryFilterType.range, 40, {}),
    _filt("region", "Регион", CategoryFilterType.select, 50, {}),
    _filt("city", "Город", CategoryFilterType.select, 60, {}),
    _filt(
        "steering_side",
        "Руль",
        CategoryFilterType.multi_select,
        70,
        _opt_cfg(*_STEERING),
    ),
    _filt(
        "transmission",
        "Коробка передач",
        CategoryFilterType.multi_select,
        80,
        _opt_cfg(*_TRANSMISSION),
    ),
    _filt("fuel", "Топливо", CategoryFilterType.multi_select, 90, _opt_cfg(*_FUEL)),
    _filt("drive", "Привод", CategoryFilterType.multi_select, 100, _opt_cfg(*_DRIVE)),
    _filt(
        "engine_volume",
        "Объём двигателя",
        CategoryFilterType.range,
        110,
        {"unit": "L"},
    ),
    _filt(
        "mileage",
        "Пробег до",
        CategoryFilterType.range,
        120,
        {"unit": "km", "mode": "max"},
    ),
    _filt(
        "condition",
        "Состояние",
        CategoryFilterType.multi_select,
        130,
        _opt_cfg(*_CONDITION),
    ),
    _filt(
        "needs_investment",
        "Требует вложений",
        CategoryFilterType.select,
        140,
        _opt_cfg(*_YES_NO),
    ),
    _filt(
        "seller_type",
        "Кто продаёт",
        CategoryFilterType.multi_select,
        150,
        _opt_cfg(*_SELLER),
    ),
    _filt(
        "sort",
        "Сортировка",
        CategoryFilterType.select,
        170,
        {
            "options": [
                {"value": "newest", "label": "Сначала новые"},
                {"value": "price_asc", "label": "Сначала дешевле"},
                {"value": "price_desc", "label": "Сначала дороже"},
            ]
        },
    ),
]
