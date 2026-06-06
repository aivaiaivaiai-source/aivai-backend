from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from typing import Any

from app.services.category_text import normalize_text

_YEAR = re.compile(r"\b((?:19|20)\d{2})\b")
_PRICE = re.compile(r"(\d[\d\s]{3,12})")
_STEERING = re.compile(r"\b(левый|правый|left|right)\b", re.I)
_YES_NO = re.compile(r"\b(да|нет|yes|no)\b", re.I)
_CITY_NAMES = re.compile(
    r"^(?:в\s+)?([a-zа-яё][a-zа-яё\-\s]{1,40})$",
    re.I,
)

_FIELD_CONTINUATION: dict[str, re.Pattern[str]] = {
    "year": _YEAR,
    "price": _PRICE,
    "salary": _PRICE,
    "rooms": re.compile(r"(\d+)\s*-?\s*комнат", re.I),
    "memory": re.compile(r"(\d+)\s*(?:гб|gb)", re.I),
    "size": re.compile(r"\b([xsml\d]{1,6}|размер\s*\d+)\b", re.I),
    "steering_side": _STEERING,
    "purpose": _YES_NO,
    "condition": re.compile(r"\b(новое|б/у|бу|отличн)\b", re.I),
    "deal_type": re.compile(r"\b(продажа|аренда|куплю)\b", re.I),
}


def extract_field_answer(field_key: str, text: str) -> Any | None:
    """Map user reply to a CORE field value when continuing dialogue."""
    raw = text.strip()
    if not raw:
        return None

    if field_key == "city":
        m = re.search(r"(?:в|город)\s+([a-zа-яё\-]{2,40})", raw, re.I)
        if m:
            return m.group(1).strip()
        m2 = _CITY_NAMES.match(raw)
        if m2:
            return m2.group(1).strip()
        if len(raw.split()) <= 3 and not re.search(r"\d{4}", raw):
            return raw.strip()

    pattern = _FIELD_CONTINUATION.get(field_key)
    if pattern is not None:
        m = pattern.search(raw) or pattern.search(normalize_text(raw))
        if m:
            if m.lastindex:
                return m.group(1).strip()
            return m.group(0).strip()

    if field_key in ("brand", "model", "item_type", "animal_type", "material_type", "product_type", "service_type", "position", "business_type"):
        if len(raw) <= 80:
            return raw.strip()

    return raw.strip() if len(raw) <= 120 else None


def parse_price_value(text: str) -> str | None:
    m = _PRICE.search(text.replace(" ", ""))
    if not m:
        return None
    try:
        d = Decimal(m.group(1).replace(" ", ""))
        return str(d)
    except InvalidOperation:
        return None
