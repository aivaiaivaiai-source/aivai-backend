# -*- coding: utf-8 -*-
"""Transport → Шины и диски V2 — leaf Create/Search SoT.

Parent ``transport-tires-wheels`` (684) is picker-only.
Size compatibility = structured width/profile/diameter (+ PCD for rims).
No vehicle Brand/Model. No free-text size/PCD.
"""
from __future__ import annotations

from typing import Any

from app.models.category_enums import CategoryFieldType, CategoryFilterType
from app.seeds.car_sale_v2 import CONTACT_METHOD_CHOICES, NEGOTIABLE_CHOICES
from app.seeds import tires_wheels_catalog as _legacy

TIRES_PARENT_SLUG = "transport-tires-wheels"
TIRES_PARENT_ID = 684

TIRES_LEAF_ID = 735
RIMS_LEAF_ID = 736
COMPLETE_LEAF_ID = 737
OTHER_LEAF_ID = 738
TPMS_LEAF_ID = 1680
FASTENERS_LEAF_ID = 1681

TIRES_LEAF_SLUG = "transport-tires-wheels-shiny"
RIMS_LEAF_SLUG = "transport-tires-wheels-diski"
COMPLETE_LEAF_SLUG = "transport-tires-wheels-kolesa-v-sbore"
OTHER_LEAF_SLUG = "transport-tires-wheels-drugoe"
TPMS_LEAF_SLUG = "transport-tires-wheels-tpms"
FASTENERS_LEAF_SLUG = "transport-tires-wheels-krepezh"

# Legacy slug retained on 738 until migration renames.
OTHER_LEGACY_SLUG = "transport-tires-wheels-aksessuary-dlya-shin-i-diskov"

LEAF_SLUGS: tuple[str, ...] = (
    TIRES_LEAF_SLUG,
    RIMS_LEAF_SLUG,
    COMPLETE_LEAF_SLUG,
    TPMS_LEAF_SLUG,
    FASTENERS_LEAF_SLUG,
    OTHER_LEAF_SLUG,
)

LEAF_LABELS: dict[str, str] = {
    TIRES_LEAF_SLUG: "Шины",
    RIMS_LEAF_SLUG: "Диски",
    COMPLETE_LEAF_SLUG: "Колёса в сборе",
    TPMS_LEAF_SLUG: "Датчики давления (TPMS)",
    FASTENERS_LEAF_SLUG: "Крепёж для колёс",
    OTHER_LEAF_SLUG: "Другое для шин и дисков",
}

LEAF_IDS: dict[str, int] = {
    TIRES_LEAF_SLUG: TIRES_LEAF_ID,
    RIMS_LEAF_SLUG: RIMS_LEAF_ID,
    COMPLETE_LEAF_SLUG: COMPLETE_LEAF_ID,
    TPMS_LEAF_SLUG: TPMS_LEAF_ID,
    FASTENERS_LEAF_SLUG: FASTENERS_LEAF_ID,
    OTHER_LEAF_SLUG: OTHER_LEAF_ID,
}

LEAF_SORT: dict[str, int] = {
    TIRES_LEAF_SLUG: 10,
    RIMS_LEAF_SLUG: 20,
    COMPLETE_LEAF_SLUG: 30,
    TPMS_LEAF_SLUG: 40,
    FASTENERS_LEAF_SLUG: 50,
    OTHER_LEAF_SLUG: 60,
}

# Stable machine values → RU labels
VEHICLE_CLASS_OPTIONS: tuple[tuple[str, str], ...] = (
    ("passenger", "Легковой"),
    ("cargo", "Грузовой"),
    ("bus", "Автобус"),
    ("special", "Спецтехника"),
    ("farm", "Сельхозтехника"),
    ("moto", "Мото"),
    ("trailer", "Прицеп"),
)

PCD_APPLICABLE_CLASSES = ("passenger", "cargo", "bus", "trailer")

SEASON_CHOICES = ("Летние", "Зимние", "Всесезонные")
STUDDED_CHOICES = ("Да", "Нет")
WHEEL_CONDITION_CHOICES = ("Новые", "Б/у")
SELLER_TYPE_CHOICES = ("Частное лицо", "Магазин")
QUANTITY_CHOICES = ("1", "2", "3", "4")
RIM_MATERIAL_CHOICES = ("Стальные", "Литые", "Кованые")
FASTENER_TYPE_CHOICES = ("Болты", "Гайки", "Секретки")
OTHER_TYPE_CHOICES = ("Колпаки", "Камеры", "Проставки", "Другое")

# Practical starter PCD set (expand Backend-side later).
PCD_BY_CLASS: dict[str, tuple[str, ...]] = {
    "passenger": (
        "4x100",
        "4x108",
        "4x114.3",
        "5x100",
        "5x105",
        "5x108",
        "5x110",
        "5x112",
        "5x114.3",
        "5x115",
        "5x120",
        "5x127",
        "5x130",
        "6x114.3",
        "6x139.7",
    ),
    "cargo": (
        "5x112",
        "5x114.3",
        "5x120",
        "6x114.3",
        "6x130",
        "6x139.7",
        "6x170",
        "8x165.1",
        "8x170",
        "8x180",
        "8x200",
        "8x210",
        "8x275",
        "10x225",
    ),
    "bus": (
        "6x130",
        "6x170",
        "8x165.1",
        "8x170",
        "8x180",
        "8x200",
        "8x210",
        "8x275",
        "10x225",
    ),
    "trailer": (
        "4x100",
        "5x112",
        "5x114.3",
        "6x170",
        "8x165.1",
        "8x170",
        "8x200",
        "8x210",
    ),
}


def _choices_labeled(pairs: tuple[tuple[str, str], ...]) -> dict[str, Any]:
    items = [{"value": v, "label": lab} for v, lab in pairs]
    return {"choices": items, "values": items}


def _choices(*labels: str) -> dict[str, Any]:
    items = [{"value": x, "label": x} for x in labels]
    return {"choices": items, "values": items}


def _choices_when(
    values: tuple[str, ...],
    *,
    vehicle_classes: tuple[str, ...],
    label_fn=None,
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for v in values:
        lab = label_fn(v) if label_fn else v
        out.append(
            {
                "value": v,
                "label": lab,
                "when": {"vehicle_class": list(vehicle_classes)},
            }
        )
    return out


def _merge_choice_lists(*lists: list[dict[str, Any]]) -> dict[str, Any]:
    # Deduplicate by value; union vehicle_class when sets.
    by_val: dict[str, dict[str, Any]] = {}
    for lst in lists:
        for item in lst:
            v = str(item["value"])
            if v not in by_val:
                by_val[v] = {
                    "value": v,
                    "label": item.get("label", v),
                    "when": {
                        "vehicle_class": list(
                            (item.get("when") or {}).get("vehicle_class") or []
                        )
                    },
                }
            else:
                existing = by_val[v]["when"]["vehicle_class"]
                for c in (item.get("when") or {}).get("vehicle_class") or []:
                    if c not in existing:
                        existing.append(c)
    items = list(by_val.values())
    return {"choices": items, "values": items}


def _depends(field: str, *values: str) -> dict[str, Any]:
    return {"depends_on": {"field": field, "values": list(values)}}


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


def _diameter_value(raw: str) -> str:
    s = raw.strip()
    if s.upper().startswith("R"):
        s = s[1:]
    # Drop C commercial suffix for storage (R16C → 16); label keeps R16C via raw
    if s.upper().endswith("C") and s[:-1].replace(".", "", 1).isdigit():
        return s[:-1]
    return s


def _diameter_label(raw: str) -> str:
    s = raw.strip()
    if s.upper().startswith("R"):
        return s if s[0] == "R" else "R" + s[1:]
    if '"' in s:
        return s  # non-automotive leftover — should not appear
    return f"R{s}"


def _rim_width_value(raw: str) -> str:
    s = raw.strip()
    if s.upper().endswith("J"):
        return s[:-1]
    return s


def _rim_width_label(raw: str) -> str:
    v = _rim_width_value(raw)
    return f"{v}J"


def _size_options_for_class(
    widths: tuple[str, ...],
    heights: tuple[str, ...],
    diameters: tuple[str, ...],
    *,
    vehicle_class: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    w = _choices_when(widths, vehicle_classes=(vehicle_class,))
    h = _choices_when(heights, vehicle_classes=(vehicle_class,))
    d_fixed: list[dict[str, Any]] = []
    for raw in diameters:
        val = _diameter_value(raw)
        label_src = raw if raw.upper().startswith("R") else f"R{raw}"
        d_fixed.append(
            {
                "value": val,
                "label": _diameter_label(label_src),
                "when": {"vehicle_class": [vehicle_class]},
            }
        )
    return w, h, d_fixed


def _build_width_profile_diameter_options() -> tuple[
    dict[str, Any], dict[str, Any], dict[str, Any]
]:
    mapping = {
        "passenger": (_legacy._PASSENGER_W, _legacy._PASSENGER_H, _legacy._PASSENGER_D),
        "cargo": (_legacy._TRUCK_W, _legacy._TRUCK_H, _legacy._TRUCK_D),
        "bus": (_legacy._TRUCK_W, _legacy._TRUCK_H, _legacy._TRUCK_D),
        "special": (_legacy._OTR_W, _legacy._OTR_H, _legacy._OTR_D),
        "farm": (_legacy._FARM_W, _legacy._FARM_H, _legacy._FARM_D),
        "moto": (_legacy._MOTO_W, _legacy._MOTO_H, _legacy._MOTO_D),
        "trailer": (_legacy._TRAILER_W, _legacy._TRAILER_H, _legacy._TRAILER_D),
    }
    w_lists: list[list[dict[str, Any]]] = []
    h_lists: list[list[dict[str, Any]]] = []
    d_lists: list[list[dict[str, Any]]] = []
    for cls, (ww, hh, dd) in mapping.items():
        w, h, d = _size_options_for_class(ww, hh, dd, vehicle_class=cls)
        w_lists.append(w)
        h_lists.append(h)
        d_lists.append(d)
    return (
        _merge_choice_lists(*w_lists),
        _merge_choice_lists(*h_lists),
        _merge_choice_lists(*d_lists),
    )


WIDTH_OPTIONS, PROFILE_OPTIONS, DIAMETER_OPTIONS = (
    _build_width_profile_diameter_options()
)


def _rim_width_options() -> dict[str, Any]:
    mapping = {
        "passenger": _legacy._PASSENGER_RIM_W,
        "cargo": _legacy._TRUCK_RIM_W,
        "bus": _legacy._TRUCK_RIM_W,
        "special": ("8.00", "10.00", "14.00", "17.00", "19.50"),
        "farm": ("W8", "W10", "W12", "DW15", "DW16", "DW18"),
        "moto": ("1.85", "2.15", "2.50", "3.00", "3.50", "4.00", "5.50"),
        "trailer": ("4.5J", "5J", "5.5J", "6.00", "11.75"),
    }
    lists: list[list[dict[str, Any]]] = []
    for cls, widths in mapping.items():
        items = []
        for raw in widths:
            # Keep farm letter codes as-is (value=label)
            if raw.startswith("W") or raw.startswith("DW"):
                items.append(
                    {
                        "value": raw,
                        "label": raw,
                        "when": {"vehicle_class": [cls]},
                    }
                )
            else:
                val = _rim_width_value(raw)
                items.append(
                    {
                        "value": val,
                        "label": _rim_width_label(raw),
                        "when": {"vehicle_class": [cls]},
                    }
                )
        lists.append(items)
    return _merge_choice_lists(*lists)


RIM_WIDTH_OPTIONS = _rim_width_options()


def _pcd_options() -> dict[str, Any]:
    lists: list[list[dict[str, Any]]] = []
    for cls, vals in PCD_BY_CLASS.items():
        lists.append(_choices_when(vals, vehicle_classes=(cls,)))
    return _merge_choice_lists(*lists)


PCD_OPTIONS = _pcd_options()


def _tire_brand_options() -> dict[str, Any]:
    mapping = {
        "passenger": _legacy._PASSENGER_BRANDS,
        "cargo": _legacy._TRUCK_BRANDS,
        "bus": _legacy._TRUCK_BRANDS,
        "special": _legacy._OTR_BRANDS,
        "farm": _legacy._FARM_BRANDS,
        "moto": _legacy._MOTO_BRANDS,
        "trailer": _legacy._TRAILER_BRANDS,
    }
    lists = [
        _choices_when(brands, vehicle_classes=(cls,))
        for cls, brands in mapping.items()
    ]
    return _merge_choice_lists(*lists)


def _rim_brand_options() -> dict[str, Any]:
    mapping = {
        "passenger": _legacy._PASSENGER_RIM_BRANDS,
        "cargo": _legacy._TRUCK_RIM_BRANDS,
        "bus": _legacy._TRUCK_RIM_BRANDS,
        "special": _legacy._OTR_BRANDS,
        "farm": _legacy._FARM_BRANDS,
        "moto": ("Excel", "DID", "Morad", "Takasago"),
        "trailer": _legacy._TRAILER_BRANDS,
    }
    lists = [
        _choices_when(brands, vehicle_classes=(cls,))
        for cls, brands in mapping.items()
    ]
    return _merge_choice_lists(*lists)


TIRE_BRAND_OPTIONS = _tire_brand_options()
RIM_BRAND_OPTIONS = _rim_brand_options()


def _geo() -> list:
    return [
        _field("region", "Регион", CategoryFieldType.string, True, 0),
        _field("city", "Город", CategoryFieldType.city, True, 1),
    ]


def _vehicle_class_field(sort: int = 10) -> tuple:
    return _field(
        "vehicle_class",
        "Тип транспорта",
        CategoryFieldType.enum,
        True,
        sort,
        _choices_labeled(VEHICLE_CLASS_OPTIONS),
    )


def _commerce(sort: int = 200) -> list:
    return [
        _field("price", "Цена", CategoryFieldType.price, True, sort),
        _field(
            "negotiable",
            "Торг",
            CategoryFieldType.enum,
            False,
            sort + 5,
            _choices(*NEGOTIABLE_CHOICES),
        ),
        _field(
            "seller_type",
            "Кто продаёт",
            CategoryFieldType.enum,
            True,
            sort + 10,
            _choices(*SELLER_TYPE_CHOICES),
        ),
        _field(
            "contact_methods",
            "Способы связи",
            CategoryFieldType.enum,
            True,
            sort + 20,
            _choices(*CONTACT_METHOD_CHOICES),
        ),
    ]


def _quantity_field(sort: int) -> tuple:
    return _field(
        "quantity",
        "Количество",
        CategoryFieldType.enum,
        False,
        sort,
        _choices(*QUANTITY_CHOICES),
    )


def _condition_field(sort: int, *, required: bool) -> tuple:
    return _field(
        "wheel_condition",
        "Состояние",
        CategoryFieldType.enum,
        required,
        sort,
        _choices(*WHEEL_CONDITION_CHOICES),
    )


def _season_fields(sort: int = 70) -> list:
    season_opts = _choices(*SEASON_CHOICES)
    studded_opts = _choices(*STUDDED_CHOICES)
    studded_opts.update(_depends("season", "Зимние"))
    return [
        _field("season", "Сезон", CategoryFieldType.enum, True, sort, season_opts),
        _field(
            "studded",
            "Шипованные",
            CategoryFieldType.enum,
            False,
            sort + 5,
            studded_opts,
        ),
    ]


def _tire_size_fields(sort: int = 20) -> list:
    return [
        _field(
            "tire_width",
            "Ширина",
            CategoryFieldType.enum,
            True,
            sort,
            WIDTH_OPTIONS,
        ),
        _field(
            "tire_profile",
            "Профиль",
            CategoryFieldType.enum,
            True,
            sort + 5,
            PROFILE_OPTIONS,
        ),
        _field(
            "rim_diameter",
            "Диаметр",
            CategoryFieldType.enum,
            True,
            sort + 10,
            DIAMETER_OPTIONS,
        ),
    ]


def _pcd_field(sort: int = 50, *, required: bool = True) -> tuple:
    opts = dict(PCD_OPTIONS)
    opts.update(_depends("vehicle_class", *PCD_APPLICABLE_CLASSES))
    return _field(
        "pcd",
        "Разболтовка",
        CategoryFieldType.enum,
        required,
        sort,
        opts,
    )


def _tires_schema() -> list:
    fields: list = [*_geo(), _vehicle_class_field(10)]
    fields.extend(_tire_size_fields(20))
    fields.extend(_season_fields(70))
    fields.append(_condition_field(90, required=True))
    fields.append(
        _field(
            "tire_brand",
            "Бренд",
            CategoryFieldType.enum,
            False,
            100,
            TIRE_BRAND_OPTIONS,
        )
    )
    fields.append(_quantity_field(110))
    fields.extend(_commerce(200))
    return fields


def _rims_schema() -> list:
    fields: list = [
        *_geo(),
        _vehicle_class_field(10),
        _field(
            "rim_diameter",
            "Диаметр",
            CategoryFieldType.enum,
            True,
            20,
            DIAMETER_OPTIONS,
        ),
        _pcd_field(30, required=True),
        _condition_field(40, required=True),
        _field(
            "rim_width",
            "Ширина диска",
            CategoryFieldType.enum,
            False,
            50,
            RIM_WIDTH_OPTIONS,
        ),
        _field(
            "rim_material",
            "Материал",
            CategoryFieldType.enum,
            False,
            60,
            _choices(*RIM_MATERIAL_CHOICES),
        ),
        _field(
            "rim_brand",
            "Бренд",
            CategoryFieldType.enum,
            False,
            70,
            RIM_BRAND_OPTIONS,
        ),
        _quantity_field(80),
        *_commerce(200),
    ]
    return fields


def _complete_schema() -> list:
    fields: list = [*_geo(), _vehicle_class_field(10)]
    fields.extend(_tire_size_fields(20))
    fields.extend(_season_fields(70))
    fields.append(_pcd_field(85, required=True))
    fields.append(_condition_field(90, required=True))
    fields.append(
        _field(
            "rim_material",
            "Материал диска",
            CategoryFieldType.enum,
            False,
            100,
            _choices(*RIM_MATERIAL_CHOICES),
        )
    )
    fields.append(
        _field(
            "tire_brand",
            "Бренд",
            CategoryFieldType.enum,
            False,
            110,
            TIRE_BRAND_OPTIONS,
        )
    )
    fields.append(_quantity_field(120))
    fields.extend(_commerce(200))
    return fields


def _tpms_schema() -> list:
    return [
        *_geo(),
        _condition_field(20, required=False),
        _field(
            "product_brand",
            "Бренд",
            CategoryFieldType.enum,
            False,
            30,
            _choices(*_legacy._PASSENGER_BRANDS[:12]),
        ),
        _quantity_field(40),
        *_commerce(200),
    ]


def _fasteners_schema() -> list:
    return [
        *_geo(),
        _field(
            "wheel_fastener_type",
            "Тип товара",
            CategoryFieldType.enum,
            True,
            20,
            _choices(*FASTENER_TYPE_CHOICES),
        ),
        _quantity_field(30),
        *_commerce(200),
    ]


def _other_schema() -> list:
    return [
        *_geo(),
        _field(
            "wheel_other_type",
            "Тип товара",
            CategoryFieldType.enum,
            True,
            20,
            _choices(*OTHER_TYPE_CHOICES),
        ),
        _quantity_field(30),
        *_commerce(200),
    ]


def _search_filters_tires() -> list:
    return [
        _filt("region", "Регион", CategoryFilterType.text, 10, {}),
        _filt("city", "Город", CategoryFilterType.text, 20, {}),
        _filt(
            "vehicle_class",
            "Тип транспорта",
            CategoryFilterType.select,
            30,
            _choices_labeled(VEHICLE_CLASS_OPTIONS),
        ),
        _filt("tire_width", "Ширина", CategoryFilterType.select, 40, WIDTH_OPTIONS),
        _filt(
            "tire_profile", "Профиль", CategoryFilterType.select, 50, PROFILE_OPTIONS
        ),
        _filt(
            "rim_diameter", "Диаметр", CategoryFilterType.select, 60, DIAMETER_OPTIONS
        ),
        _filt("season", "Сезон", CategoryFilterType.select, 70, _choices(*SEASON_CHOICES)),
        _filt(
            "wheel_condition",
            "Состояние",
            CategoryFilterType.select,
            80,
            _choices(*WHEEL_CONDITION_CHOICES),
        ),
        _filt(
            "seller_type",
            "Кто продаёт",
            CategoryFilterType.select,
            90,
            _choices(*SELLER_TYPE_CHOICES),
        ),
        _filt(
            "tire_brand", "Бренд", CategoryFilterType.select, 100, TIRE_BRAND_OPTIONS
        ),
        _filt(
            "studded", "Шипованные", CategoryFilterType.select, 110, _choices(*STUDDED_CHOICES)
        ),
        _filt("price", "Цена", CategoryFilterType.range, 200, {}),
    ]


def _search_filters_rims() -> list:
    return [
        _filt("region", "Регион", CategoryFilterType.text, 10, {}),
        _filt("city", "Город", CategoryFilterType.text, 20, {}),
        _filt(
            "vehicle_class",
            "Тип транспорта",
            CategoryFilterType.select,
            30,
            _choices_labeled(VEHICLE_CLASS_OPTIONS),
        ),
        _filt(
            "rim_diameter", "Диаметр", CategoryFilterType.select, 40, DIAMETER_OPTIONS
        ),
        _filt("pcd", "Разболтовка", CategoryFilterType.select, 50, PCD_OPTIONS),
        _filt(
            "wheel_condition",
            "Состояние",
            CategoryFilterType.select,
            60,
            _choices(*WHEEL_CONDITION_CHOICES),
        ),
        _filt(
            "seller_type",
            "Кто продаёт",
            CategoryFilterType.select,
            70,
            _choices(*SELLER_TYPE_CHOICES),
        ),
        _filt(
            "rim_width", "Ширина диска", CategoryFilterType.select, 80, RIM_WIDTH_OPTIONS
        ),
        _filt(
            "rim_material",
            "Материал",
            CategoryFilterType.select,
            90,
            _choices(*RIM_MATERIAL_CHOICES),
        ),
        _filt("rim_brand", "Бренд", CategoryFilterType.select, 100, RIM_BRAND_OPTIONS),
        _filt("price", "Цена", CategoryFilterType.range, 200, {}),
    ]


def _search_filters_complete() -> list:
    return [
        _filt("region", "Регион", CategoryFilterType.text, 10, {}),
        _filt("city", "Город", CategoryFilterType.text, 20, {}),
        _filt(
            "vehicle_class",
            "Тип транспорта",
            CategoryFilterType.select,
            30,
            _choices_labeled(VEHICLE_CLASS_OPTIONS),
        ),
        _filt("tire_width", "Ширина", CategoryFilterType.select, 40, WIDTH_OPTIONS),
        _filt(
            "tire_profile", "Профиль", CategoryFilterType.select, 50, PROFILE_OPTIONS
        ),
        _filt(
            "rim_diameter", "Диаметр", CategoryFilterType.select, 60, DIAMETER_OPTIONS
        ),
        _filt("season", "Сезон", CategoryFilterType.select, 70, _choices(*SEASON_CHOICES)),
        _filt("pcd", "Разболтовка", CategoryFilterType.select, 80, PCD_OPTIONS),
        _filt(
            "wheel_condition",
            "Состояние",
            CategoryFilterType.select,
            90,
            _choices(*WHEEL_CONDITION_CHOICES),
        ),
        _filt(
            "seller_type",
            "Кто продаёт",
            CategoryFilterType.select,
            100,
            _choices(*SELLER_TYPE_CHOICES),
        ),
        _filt(
            "studded", "Шипованные", CategoryFilterType.select, 110, _choices(*STUDDED_CHOICES)
        ),
        _filt(
            "rim_material",
            "Материал диска",
            CategoryFilterType.select,
            120,
            _choices(*RIM_MATERIAL_CHOICES),
        ),
        _filt("price", "Цена", CategoryFilterType.range, 200, {}),
    ]


def _search_filters_tpms() -> list:
    return [
        _filt("region", "Регион", CategoryFilterType.text, 10, {}),
        _filt("city", "Город", CategoryFilterType.text, 20, {}),
        _filt(
            "wheel_condition",
            "Состояние",
            CategoryFilterType.select,
            30,
            _choices(*WHEEL_CONDITION_CHOICES),
        ),
        _filt(
            "seller_type",
            "Кто продаёт",
            CategoryFilterType.select,
            40,
            _choices(*SELLER_TYPE_CHOICES),
        ),
        _filt("price", "Цена", CategoryFilterType.range, 200, {}),
    ]


def _search_filters_fasteners() -> list:
    return [
        _filt("region", "Регион", CategoryFilterType.text, 10, {}),
        _filt("city", "Город", CategoryFilterType.text, 20, {}),
        _filt(
            "wheel_fastener_type",
            "Тип товара",
            CategoryFilterType.select,
            30,
            _choices(*FASTENER_TYPE_CHOICES),
        ),
        _filt(
            "seller_type",
            "Кто продаёт",
            CategoryFilterType.select,
            40,
            _choices(*SELLER_TYPE_CHOICES),
        ),
        _filt("price", "Цена", CategoryFilterType.range, 200, {}),
    ]


def _search_filters_other() -> list:
    return [
        _filt("region", "Регион", CategoryFilterType.text, 10, {}),
        _filt("city", "Город", CategoryFilterType.text, 20, {}),
        _filt(
            "wheel_other_type",
            "Тип товара",
            CategoryFilterType.select,
            30,
            _choices(*OTHER_TYPE_CHOICES),
        ),
        _filt(
            "seller_type",
            "Кто продаёт",
            CategoryFilterType.select,
            40,
            _choices(*SELLER_TYPE_CHOICES),
        ),
        _filt("price", "Цена", CategoryFilterType.range, 200, {}),
    ]


TIRES_CORE_FIELDS_BY_SLUG: dict[str, list] = {
    TIRES_PARENT_SLUG: [],
    TIRES_LEAF_SLUG: _tires_schema(),
    RIMS_LEAF_SLUG: _rims_schema(),
    COMPLETE_LEAF_SLUG: _complete_schema(),
    TPMS_LEAF_SLUG: _tpms_schema(),
    FASTENERS_LEAF_SLUG: _fasteners_schema(),
    OTHER_LEAF_SLUG: _other_schema(),
}

TIRES_SEARCH_FILTERS_BY_SLUG: dict[str, list] = {
    TIRES_PARENT_SLUG: [],
    TIRES_LEAF_SLUG: _search_filters_tires(),
    RIMS_LEAF_SLUG: _search_filters_rims(),
    COMPLETE_LEAF_SLUG: _search_filters_complete(),
    TPMS_LEAF_SLUG: _search_filters_tpms(),
    FASTENERS_LEAF_SLUG: _search_filters_fasteners(),
    OTHER_LEAF_SLUG: _search_filters_other(),
}

TIRES_LEAF_ALIASES: dict[str, str] = {
    "шины": TIRES_LEAF_SLUG,
    "резина": TIRES_LEAF_SLUG,
    "диски": RIMS_LEAF_SLUG,
    "колёса в сборе": COMPLETE_LEAF_SLUG,
    "колеса в сборе": COMPLETE_LEAF_SLUG,
    "датчики давления": TPMS_LEAF_SLUG,
    "tpms": TPMS_LEAF_SLUG,
    "секретки": FASTENERS_LEAF_SLUG,
    "колпаки": OTHER_LEAF_SLUG,
    "камеры": OTHER_LEAF_SLUG,
    "проставки": OTHER_LEAF_SLUG,
    "разболтовка": RIMS_LEAF_SLUG,
}

TIRES_PARENT_ALIASES: dict[str, str] = {
    "шины и диски": TIRES_PARENT_SLUG,
}

TIRES_SERVICE_BOUNDARY_ALIASES: dict[str, str] = {
    "шиномонтаж": "transport-auto-services-shinomontazh",
}


def format_tire_size(
    width: str | None, profile: str | None, diameter: str | None
) -> str:
    """Canonical display: 205/55 R16."""
    w = (width or "").strip()
    p = (profile or "").strip()
    d = (diameter or "").strip()
    if not w or not p or not d:
        return ""
    d_disp = d if d.upper().startswith("R") else f"R{d}"
    return f"{w}/{p} {d_disp}"


def format_rim_identity(diameter: str | None, pcd: str | None) -> str:
    """Canonical display: R17 · 5x114.3."""
    d = (diameter or "").strip()
    p = (pcd or "").strip()
    if not d and not p:
        return ""
    d_disp = ""
    if d:
        d_disp = d if d.upper().startswith("R") else f"R{d}"
    if d_disp and p:
        return f"{d_disp} · {p}"
    return d_disp or p


def format_complete_wheel(
    width: str | None,
    profile: str | None,
    diameter: str | None,
    pcd: str | None,
) -> str:
    size = format_tire_size(width, profile, diameter)
    p = (pcd or "").strip()
    if size and p:
        return f"{size} · {p}"
    return size or format_rim_identity(diameter, pcd)
