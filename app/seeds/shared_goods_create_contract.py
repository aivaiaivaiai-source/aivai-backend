# -*- coding: utf-8 -*-
"""Canonical shared Create contracts for AiVai goods domains (Backend SoT).

Rule: SHARED FIELD = SHARED CONTRACT.
Matching field key alone is not enough — type, options, stable values, labels,
requiredness, component, and storage/display semantics must match this contract
unless a domain has an *explicit* product-approved override.

Closed-domain evidence (Fashion, Electronics, Home & Garden contacts,
Repair contacts, Services contacts, Transport car_sale): same contact catalog.
Services price/negotiable keep approved Services semantics — not goods.
HG seller uses «Компания»; Repair seller adds «База» — declared overrides.
"""
from __future__ import annotations

from typing import Any

from app.models.category_enums import CategoryFieldType

# --- Canonical goods shared vocabularies ---

GOODS_SELLER_CHOICES: tuple[str, ...] = (
    "Частное лицо",
    "Магазин",
    "Другой",
)

GOODS_NEGOTIABLE_CHOICES: tuple[str, ...] = (
    "Есть торг",
    "Без торга",
)

CONTACT_METHOD_CHOICES: tuple[str, ...] = (
    "Только чат",
    "Только телефон",
    "Чат + телефон",
    "Чат + Wapp",
    "Телефон + Wapp",
    "Чат + Тел. + Wapp",
)

# Alias used by Transport car_sale historically.
NEGOTIABLE_CHOICES = GOODS_NEGOTIABLE_CHOICES


def _choices(*labels: str) -> dict[str, Any]:
    return {"choices": [{"value": label, "label": label} for label in labels]}


# Structural contracts used by parity invariants (key → metadata).
CANONICAL_GOODS_SHARED_FIELD_CONTRACT: dict[str, dict[str, Any]] = {
    "seller_type": {
        "label": "Продавец",
        "field_type": CategoryFieldType.enum,
        "required": True,
        "choices": GOODS_SELLER_CHOICES,
    },
    "price": {
        "label": "Цена",
        "field_type": CategoryFieldType.price,
        "required": True,
        "choices": None,
    },
    "negotiable": {
        "label": "Торг",
        "field_type": CategoryFieldType.enum,
        "required": False,
        "choices": GOODS_NEGOTIABLE_CHOICES,
    },
    "contact_methods": {
        "label": "Способы связи",
        "field_type": CategoryFieldType.enum,
        "required": True,
        "choices": CONTACT_METHOD_CHOICES,
    },
}

# Domains that must follow goods shared contract for these keys (Package A SoT).
GOODS_SHARED_CONTRACT_DOMAINS: tuple[str, ...] = (
    "fashion",
    "electronics",
    "kids",
    "food_agri",
    "animals",
    "stationery",
    "business_equipment",
    "medical",
    "materials",
    "sport",
)

# contact_methods has no approved domain override among closed goods/services.
CONTACT_METHODS_PARITY_BUILDERS: tuple[str, ...] = (
    "fashion",
    "electronics",
    "home_garden",
    "repair",
    "services",
    "kids",
    "car_sale",
    "food_agri",
    "animals",
    "stationery",
    "business_equipment",
    "medical",
    "sport",
)

# Explicit product-approved overrides (do not treat as accidental divergence).
APPROVED_SHARED_FIELD_OVERRIDES: frozenset[tuple[str, str]] = frozenset(
    {
        # Services: «Цена от» / «По договорённости» — approved Services semantics.
        ("services", "price"),
        ("services", "negotiable"),
        ("services", "seller_type"),  # Services often omit goods seller triplet
        # Home & Garden seller third option is «Компания» (approved HG Package A).
        ("home_garden", "seller_type"),
        # Repair seller includes «База» (approved Repair).
        ("repair", "seller_type"),
        # Transport car_sale uses vehicle Create base (seller may differ).
        ("car_sale", "seller_type"),
        ("car_sale", "price"),
        # Products & Agri: seller = Частное лицо/Фермер/Магазин/Другой + label «Кто продаёт».
        ("food_agri", "seller_type"),
        # Animals: seller = Частное лицо/Хозяйство/Питомник/Магазин/Другой + label «Кто продаёт».
        ("animals", "seller_type"),
    }
)


def extract_choice_values(options: dict[str, Any] | None) -> tuple[str, ...] | None:
    if not options or "choices" not in options:
        return None
    raw = options["choices"]
    out: list[str] = []
    for item in raw:
        if isinstance(item, dict):
            out.append(str(item.get("value") or item.get("label") or ""))
        else:
            out.append(str(item))
    return tuple(out)


def field_row_by_key(fields: list, key: str):
    for row in fields:
        if row[0] == key:
            return row
    return None


def options_from_field_row(row) -> dict[str, Any] | None:
    """Normalize options across 6-wide HG FieldDef and 7-wide dep tuples."""
    if row is None:
        return None
    # 7-wide: (key, label, type, required, sort, options, hint)
    if len(row) >= 7 and isinstance(row[4], int):
        opts = row[5]
        return opts if isinstance(opts, dict) else None
    # 6-wide: (key, label, type, required, options, hint)
    if len(row) >= 5 and isinstance(row[4], (dict, type(None))):
        return row[4]
    if len(row) >= 6 and isinstance(row[5], dict):
        return row[5]
    return None


def assert_field_matches_canonical(
    *,
    domain: str,
    field_key: str,
    row,
) -> None:
    """Assert domain field structurally equals canonical goods shared contract."""
    if (domain, field_key) in APPROVED_SHARED_FIELD_OVERRIDES:
        return
    expected = CANONICAL_GOODS_SHARED_FIELD_CONTRACT[field_key]
    assert row is not None, f"{domain}: missing shared field {field_key}"
    key, label, ftype, required = row[0], row[1], row[2], row[3]
    options = options_from_field_row(row)
    assert key == field_key
    assert label == expected["label"], f"{domain}.{field_key} label"
    assert ftype == expected["field_type"], f"{domain}.{field_key} type"
    assert bool(required) == bool(expected["required"]), f"{domain}.{field_key} required"
    exp_choices = expected["choices"]
    if exp_choices is None:
        return
    got = extract_choice_values(options)
    assert got == exp_choices, (
        f"{domain}.{field_key} choices diverge from canonical shared contract:\n"
        f"  expected={exp_choices}\n  got={got}"
    )
