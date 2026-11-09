# -*- coding: utf-8 -*-
"""Electronics V2 Package A — canonical 19 goods L2 + Create Backend SoT.

Balanced Final: skeleton nodes 961–979. Legacy coarse L2 retired.
Brand/model = Backend scoped enums (not VehicleCatalog).
Climate bare power digits excluded until unit semantics proven.
"""
from __future__ import annotations

import re
from typing import Any

from app.models.category_enums import (
    CategoryEntityType,
    CategoryFieldType,
    CategoryFilterType,
)
from app.seeds.electronics_sections_catalog import ELECTRONICS_SECTIONS

ELECTRONICS_ROOT_SLUG = "electronics"
ELECTRONICS_ROOT_LABEL = "Техника и электроника"

# Final picker order (sort_order).
ELECTRONICS_V2_CANONICAL_LEAVES: tuple[tuple[str, str, int], ...] = (
    ("electronics-smartfony-i-telefony", "Смартфоны и телефоны", 10),
    ("electronics-planshety-i-elektronnye-knigi", "Планшеты и электронные книги", 20),
    ("electronics-noutbuki-i-kompyutery", "Ноутбуки и компьютеры", 30),
    ("electronics-televizory-i-proektory", "Телевизоры и проекторы", 40),
    ("electronics-bytovaya-tehnika", "Бытовая техника", 50),
    ("electronics-kuhonnaya-tehnika", "Кухонная техника", 60),
    ("electronics-klimaticheskaya-tehnika", "Климатическая техника", 70),
    ("electronics-audiotehnika", "Аудиотехника", 80),
    ("electronics-igrovye-pristavki-i-aksessuary", "Игровые приставки и аксессуары", 90),
    ("electronics-umnye-chasy-i-gadzhety", "Умные часы и гаджеты", 100),
    ("electronics-komplektuyuschie-dlya-kompyuterov", "Комплектующие для компьютеров", 110),
    ("electronics-foto-i-videotehnika", "Фото и видеотехника", 120),
    ("electronics-vstraivaemaya-tehnika", "Встраиваемая техника", 130),
    ("electronics-tehnika-dlya-doma", "Техника для дома", 140),
    ("electronics-orgtehnika", "Оргтехника", 150),
    ("electronics-setevoe-oborudovanie", "Сетевое оборудование", 160),
    ("electronics-tehnika-dlya-ofisa", "Техника для офиса", 170),
    ("electronics-zapchasti-i-aksessuary", "Запчасти и аксессуары", 180),
    ("electronics-prochaya-tehnika-i-elektronika", "Прочая техника и электроника", 190),
)

ELECTRONICS_V2_CANONICAL_SLUGS: frozenset[str] = frozenset(
    slug for slug, _label, _sort in ELECTRONICS_V2_CANONICAL_LEAVES
)

ELECTRONICS_V2_RETIRED_SLUGS: frozenset[str] = frozenset(
    {
        "electronics-phones",
        "electronics-computers",
        "electronics-appliances",
        "electronics-tv",
    }
)

# Internal catalog key → canonical DB slug.
ELECTRONICS_V2_SECTION_TO_SLUG: dict[str, str] = {
    key: str(cat["category_slug"]) for key, cat in ELECTRONICS_SECTIONS.items()
}

ELECTRONICS_V2_ENTITY_TYPE = CategoryEntityType.object

_CONTACT_METHODS = (
    "Только чат",
    "Только телефон",
    "Чат + телефон",
    "Чат + Wapp",
    "Телефон + Wapp",
    "Чат + Тел. + Wapp",
)

_NEGOTIABLE = ("Есть торг", "Без торга")

# Labels skipped from Create SoT (unproven semantics).
_SKIP_FILTER_LABELS: frozenset[str] = frozenset({"Мощность"})


def _choices(*labels: str) -> dict[str, Any]:
    return {"choices": [{"value": label, "label": label} for label in labels]}


def _dep_field(
    key: str,
    label: str,
    ftype: CategoryFieldType,
    required: bool,
    sort: int,
    options: dict[str, Any],
    *,
    hint: str | None = None,
) -> tuple:
    return (key, label, ftype, required, sort, options, hint)


def _stable_storage(label: str) -> tuple[str, str]:
    raw = label.strip()
    low = raw.casefold().replace(" ", "")
    m = re.fullmatch(r"(\d+(?:[.,]\d+)?)(гб|тб|gb|tb)", low)
    if not m:
        return raw, raw
    num = m.group(1).replace(",", ".")
    unit = m.group(2)
    if unit in {"тб", "tb"}:
        return f"{num}tb".replace(".0tb", "tb"), raw
    return f"{num}gb".replace(".0gb", "gb"), raw


def _stable_screen(label: str) -> tuple[str, str]:
    raw = label.strip()
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*\"?", raw)
    if not m:
        return raw, raw
    num = m.group(1).replace(",", ".")
    if num.endswith(".0"):
        num = num[:-2]
    return f"{num}in", raw


def _option(
    *,
    value: str,
    label: str,
    for_kinds: list[str] | None = None,
    parent: str | None = None,
) -> dict[str, Any]:
    row: dict[str, Any] = {"value": value, "label": label}
    if for_kinds:
        row["for_kinds"] = list(for_kinds)
        row["when"] = {"electronics_kind": list(for_kinds)}
    if parent:
        row["parent"] = parent
        when = dict(row.get("when") or {})
        when["electronics_brand"] = [parent]
        row["when"] = when
    return row


def _labels(items: list[dict[str, Any]]) -> tuple[str, ...]:
    return tuple(str(i["label"]) for i in items)


def _normalize_extra_key(label: str, section_key: str) -> str | None:
    if label in _SKIP_FILTER_LABELS:
        return None
    if label == "Продавец":
        return "seller_type"
    if label == "Состояние":
        return "condition"
    if label == "Марка":
        return "electronics_brand"
    if label == "Модель":
        return "electronics_model"
    if label in {"Память", "Накопитель"}:
        return "storage"
    if label == "ОЗУ":
        return "ram"
    if label in {"Экран", "Диагональ"}:
        return "screen_size"
    if label == "Объём":
        if section_key == "parts":
            return "capacity_gb"
        if section_key == "appliances":
            return "volume_l"
        return "volume_l"
    if label == "Печать":
        return "print_type"
    if label == "Разрешение":
        return "resolution"
    if label == "Подключение":
        return "connection"
    if label == "Диапазон":
        return "band"
    if label == "Загрузка":
        return "load_capacity"
    if label == "Тип":
        return "device_type"
    if label == "Ширина":
        return "width"
    return None


def _display_label_for_key(key: str, section_key: str, source_label: str) -> str:
    if key == "storage":
        return "Накопитель" if section_key in {"computers", "parts"} else "Память"
    if key == "screen_size":
        return "Диагональ"
    if key == "capacity_gb":
        return "Объём"
    if key == "volume_l":
        return "Объём"
    return source_label


def _stabilize_choice(key: str, label: str) -> tuple[str, str]:
    if key in {"storage", "capacity_gb", "ram"}:
        return _stable_storage(label)
    if key == "screen_size":
        return _stable_screen(label)
    return label, label


def build_electronics_v2_core_fields() -> dict[str, list]:
    out: dict[str, list] = {}
    for section_key, slug in ELECTRONICS_V2_SECTION_TO_SLUG.items():
        catalog = ELECTRONICS_SECTIONS[section_key]
        assert catalog["category_slug"] == slug, (section_key, catalog["category_slug"], slug)
        kinds = _labels(catalog["roles"])
        fields: list = [
            _dep_field(
                "electronics_kind",
                "Вид товара",
                CategoryFieldType.enum,
                True,
                10,
                _choices(*kinds),
                hint=str(catalog.get("question") or "Какой товар?"),
            ),
        ]
        sort = 20

        brands_group = next(
            (g for g in catalog.get("filters") or [] if g.get("label") == "Марка"),
            None,
        )
        models_group = next(
            (g for g in catalog.get("filters") or [] if g.get("label") == "Модель"),
            None,
        )

        kinds_with_brand: set[str] = set()
        brands_with_model: set[str] = set()
        brand_choices: list[dict[str, Any]] = []
        model_choices: list[dict[str, Any]] = []

        if brands_group:
            for opt in brands_group.get("options") or []:
                label = str(opt["label"])
                value = str(opt.get("value") or label)
                for_kinds = opt.get("for_kinds")
                fk = list(for_kinds) if for_kinds else None
                if fk:
                    kinds_with_brand.update(fk)
                else:
                    kinds_with_brand.update(kinds)
                brand_choices.append(
                    _option(value=value, label=label, for_kinds=fk)
                )

        if models_group:
            for opt in models_group.get("options") or []:
                label = str(opt["label"])
                value = str(opt.get("value") or label)
                parent = opt.get("parent")
                for_kinds = opt.get("for_kinds")
                fk = list(for_kinds) if for_kinds else None
                # Real brands + brands that expose other_model. Never other_brand.
                if parent and str(parent) != "other_brand":
                    brands_with_model.add(str(parent))
                model_choices.append(
                    _option(
                        value=value,
                        label=label,
                        for_kinds=fk,
                        parent=str(parent) if parent else None,
                    )
                )

        if brand_choices:
            brand_opts: dict[str, Any] = {"choices": brand_choices}
            brand_opts["depends_on"] = {
                "field": "electronics_kind",
                "values": sorted(kinds_with_brand),
            }
            fields.append(
                _dep_field(
                    "electronics_brand",
                    "Марка",
                    CategoryFieldType.enum,
                    False,
                    sort,
                    brand_opts,
                )
            )
            sort += 10

        if model_choices:
            model_opts: dict[str, Any] = {"choices": model_choices}
            model_opts["depends_on"] = {
                "field": "electronics_brand",
                "values": sorted(brands_with_model),
            }
            fields.append(
                _dep_field(
                    "electronics_model",
                    "Модель",
                    CategoryFieldType.enum,
                    False,
                    sort,
                    model_opts,
                )
            )
            sort += 10

        # Seller / condition / extras (skip brand/model — already handled).
        for group in catalog.get("filters") or []:
            label = str(group["label"])
            if label in {"Марка", "Модель"}:
                continue
            key = _normalize_extra_key(label, section_key)
            if key is None:
                continue
            display = _display_label_for_key(key, section_key, label)
            option_rows: list[dict[str, Any]] = []
            for opt in group.get("options") or []:
                raw_label = str(opt["label"])
                value, show = _stabilize_choice(key, raw_label)
                for_kinds = opt.get("for_kinds")
                fk = list(for_kinds) if for_kinds else None
                applies = group.get("applies_to")
                if applies and not fk:
                    fk = list(applies)
                option_rows.append(
                    _option(value=value, label=show, for_kinds=fk)
                )
            opts: dict[str, Any] = {"choices": option_rows}
            applies = group.get("applies_to")
            if applies:
                opts["depends_on"] = {
                    "field": "electronics_kind",
                    "values": list(applies),
                }
                required = False
            else:
                required = key in {"seller_type", "condition"}
            fields.append(
                _dep_field(
                    key,
                    display,
                    CategoryFieldType.enum,
                    required,
                    sort,
                    opts,
                )
            )
            sort += 10

        fields.extend(
            [
                (
                    "price",
                    "Цена",
                    CategoryFieldType.price,
                    True,
                    200,
                    None,
                    "Цена товара",
                ),
                _dep_field(
                    "negotiable",
                    "Торг",
                    CategoryFieldType.enum,
                    False,
                    210,
                    _choices(*_NEGOTIABLE),
                ),
                _dep_field(
                    "contact_methods",
                    "Способы связи",
                    CategoryFieldType.enum,
                    True,
                    220,
                    _choices(*_CONTACT_METHODS),
                ),
            ]
        )
        out[slug] = fields

    assert set(out) == ELECTRONICS_V2_CANONICAL_SLUGS
    return out


def electronics_v2_kind_count() -> int:
    total = 0
    seen: set[str] = set()
    for cat in ELECTRONICS_SECTIONS.values():
        for role in cat["roles"]:
            label = str(role["label"])
            assert label not in seen, label
            seen.add(label)
            total += 1
    return total


# ---------------------------------------------------------------------------
# Package B — Search filter usefulness
# SEARCH YES: electronics_kind, electronics_brand, electronics_model,
#   seller_type, condition, and useful kind-scoped characteristics.
# SEARCH NO (Create-only): price, negotiable, contact_methods
# ---------------------------------------------------------------------------

_SEARCH_YES_KEYS: frozenset[str] = frozenset(
    {
        "electronics_kind",
        "electronics_brand",
        "electronics_model",
        "seller_type",
        "condition",
        "storage",
        "ram",
        "screen_size",
        "capacity_gb",
        "print_type",
        "resolution",
        "connection",
        "band",
        "volume_l",
        "load_capacity",
        "device_type",
        "width",
    }
)


def _search_filter(
    key: str,
    label: str,
    ftype: CategoryFilterType,
    sort: int,
    config: dict[str, Any] | None,
) -> tuple:
    return (key, label, ftype, sort, config)


def build_electronics_v2_search_filters() -> dict[str, list]:
    """Search SoT per canonical Electronics L2 — Backend filter metadata.

    Derived from Create cores for Create↔Search parity. Multi-select so facets
    share the generic ``A||B`` attrs contract. Price / negotiable / contacts
    omitted. Option-level ``for_kinds`` / ``parent`` preserved for Brand/Model.
    """
    cores = build_electronics_v2_core_fields()
    out: dict[str, list] = {}
    for slug, fields in cores.items():
        filters: list = []
        for key, label, _ftype, _required, sort, options, _hint in fields:
            if key not in _SEARCH_YES_KEYS:
                continue
            cfg: dict[str, Any] | None = None
            if options:
                cfg = dict(options)
                # CategoryFilterDto reads options/choices/values.
                if "choices" in cfg and "options" not in cfg:
                    cfg["options"] = list(cfg["choices"])
            filters.append(
                _search_filter(
                    key,
                    label,
                    CategoryFilterType.multi_select,
                    int(sort),
                    cfg,
                )
            )
        out[slug] = filters
    assert set(out) == ELECTRONICS_V2_CANONICAL_SLUGS
    return out
