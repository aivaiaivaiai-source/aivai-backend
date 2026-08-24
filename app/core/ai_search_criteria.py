"""Normalized AI search criteria contract (no service-layer imports)."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Any, Literal

Steering = Literal["left", "right"]

# Canonical brand (latin lowercase) <- surface forms.
BRAND_ALIASES: dict[str, str] = {
    "toyota": "toyota",
    "тойота": "toyota",
    "тойоту": "toyota",
    "тойоты": "toyota",
    "honda": "honda",
    "хонда": "honda",
    "хонду": "honda",
    "bmw": "bmw",
    "mercedes": "mercedes",
    "мерседес": "mercedes",
    "мерcedes": "mercedes",
    "hyundai": "hyundai",
    "хендай": "hyundai",
    "хундай": "hyundai",
    "kia": "kia",
    "киа": "kia",
    "nissan": "nissan",
    "ниссан": "nissan",
    "mazda": "mazda",
    "мазда": "mazda",
    "lexus": "lexus",
    "лексус": "lexus",
    "audi": "audi",
    "ауди": "audi",
    "volkswagen": "volkswagen",
    "фольксваген": "volkswagen",
    "chevrolet": "chevrolet",
    "шевроле": "chevrolet",
    "шевролет": "chevrolet",
}

# Surface form -> canonical model slug (latin lowercase).
MODEL_ALIASES: dict[str, str] = {
    "camry": "camry",
    "камри": "camry",
    "corolla": "corolla",
    "королла": "corolla",
    "rav4": "rav4",
    "рав4": "rav4",
    "land cruiser": "land-cruiser",
    "ленд крузер": "land-cruiser",
    "прадо": "prado",
    "prado": "prado",
    "civic": "civic",
    "сивик": "civic",
    "accord": "accord",
    "аккорд": "accord",
    "cr-v": "cr-v",
    "crv": "cr-v",
    "cobalt": "cobalt",
    "кобальт": "cobalt",
    "cruze": "cruze",
    "круз": "cruze",
    "malibu": "malibu",
    "малибу": "malibu",
    "captiva": "captiva",
    "каптива": "captiva",
    "aveo": "aveo",
    "авео": "aveo",
    "lacetti": "lacetti",
    "лачетти": "lacetti",
    "niva": "niva",
    "нива": "niva",
    "spark": "spark",
    "спарк": "spark",
    "sportage": "sportage",
    "спортейдж": "sportage",
    "rio": "rio",
    "рио": "rio",
    "cerato": "cerato",
    "серато": "cerato",
    "tucson": "tucson",
    "туссан": "tucson",
    "тусон": "tucson",
    "elantra": "elantra",
    "элантра": "elantra",
    "sonata": "sonata",
    "соната": "sonata",
    "santa fe": "santa-fe",
    "санта фе": "santa-fe",
    "x-trail": "x-trail",
    "xtrail": "x-trail",
    "икс-трейл": "x-trail",
    "qashqai": "qashqai",
    "кашкай": "qashqai",
    "cx-5": "cx-5",
    "cx5": "cx-5",
    "mazda 3": "mazda3",
    "mazda3": "mazda3",
    "polo": "polo",
    "поло": "polo",
    "passat": "passat",
    "пассат": "passat",
    "tiguan": "tiguan",
    "тигуан": "tiguan",
    "x5": "x5",
    "x3": "x3",
    "e-class": "e-class",
    "e class": "e-class",
    "c-class": "c-class",
    "c class": "c-class",
    "a4": "a4",
    "a6": "a6",
    "rx": "rx",
    "lx": "lx",
    "gx": "gx",
}

MODEL_BRAND_HINT: dict[str, str] = {
    "camry": "toyota",
    "corolla": "toyota",
    "rav4": "toyota",
    "prado": "toyota",
    "land-cruiser": "toyota",
    "civic": "honda",
    "accord": "honda",
    "cr-v": "honda",
    "cobalt": "chevrolet",
    "cruze": "chevrolet",
    "malibu": "chevrolet",
    "captiva": "chevrolet",
    "aveo": "chevrolet",
    "lacetti": "chevrolet",
    "spark": "chevrolet",
    "sportage": "kia",
    "rio": "kia",
    "cerato": "kia",
    "tucson": "hyundai",
    "elantra": "hyundai",
    "sonata": "hyundai",
    "santa-fe": "hyundai",
    "x-trail": "nissan",
    "qashqai": "nissan",
    "cx-5": "mazda",
    "polo": "volkswagen",
    "passat": "volkswagen",
    "tiguan": "volkswagen",
    "x5": "bmw",
    "x3": "bmw",
    "e-class": "mercedes",
    "c-class": "mercedes",
    "a4": "audi",
    "a6": "audi",
    "rx": "lexus",
    "lx": "lexus",
    "gx": "lexus",
}


@dataclass(frozen=True)
class AiSearchCriteria:
    """Hard contract stored in ``ai_search_tasks.criteria_json``."""

    q: str | None = None
    city: str | None = None
    min_price: int | None = None
    max_price: int | None = None
    year_min: int | None = None
    year_max: int | None = None
    brand: str | None = None
    model: str | None = None
    engine_volume: str | None = None
    steering: Steering | None = None
    rooms: int | None = None
    employment: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v is not None and v != ""}

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> AiSearchCriteria:
        raw = data or {}
        steering = raw.get("steering")
        if steering not in (None, "left", "right"):
            steering = None
        return cls(
            q=_str_or_none(raw.get("q")),
            city=_str_or_none(raw.get("city")),
            min_price=_int_or_none(raw.get("min_price")),
            max_price=_int_or_none(raw.get("max_price")),
            year_min=_int_or_none(raw.get("year_min")),
            year_max=_int_or_none(raw.get("year_max")),
            brand=normalize_brand(raw.get("brand")),
            model=normalize_model(raw.get("model")),
            engine_volume=normalize_engine_volume(raw.get("engine_volume")),
            steering=steering,
            rooms=_int_or_none(raw.get("rooms")),
            employment=_str_or_none(raw.get("employment")),
        )


def normalize_brand(value: Any) -> str | None:
    if value is None:
        return None
    key = str(value).strip().lower()
    if not key:
        return None
    return BRAND_ALIASES.get(key, key)


def normalize_model(value: Any) -> str | None:
    if value is None:
        return None
    key = str(value).strip().lower().replace("_", "-")
    key = re.sub(r"\s+", " ", key)
    if not key:
        return None
    if key in MODEL_ALIASES:
        return MODEL_ALIASES[key]
    compact = key.replace(" ", "").replace("-", "")
    for alias, canon in MODEL_ALIASES.items():
        if alias.replace(" ", "").replace("-", "") == compact:
            return canon
    return key.replace(" ", "-")


def normalize_engine_volume(value: Any) -> str | None:
    """Normalize to a compact liters string, e.g. ``1.5``, ``2``."""
    if value is None:
        return None
    raw = str(value).strip().lower().replace(",", ".")
    if not raw:
        return None
    match = re.search(r"(\d+(?:\.\d+)?)", raw)
    if not match:
        return None
    try:
        num = float(match.group(1))
    except ValueError:
        return None
    if num < 0.5 or num > 8.0:
        return None
    text = f"{num:.2f}".rstrip("0").rstrip(".")
    return text or None


def models_match(expected: str | None, actual: Any) -> bool:
    exp = normalize_model(expected)
    act = normalize_model(actual)
    if not exp or not act:
        return False
    return exp == act or exp in act or act in exp


def engine_volumes_match(expected: str | None, actual: Any) -> bool:
    exp = normalize_engine_volume(expected)
    act = normalize_engine_volume(actual)
    if not exp or not act:
        return False
    return exp == act


def _int_or_none(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _str_or_none(value: Any) -> str | None:
    if value is None:
        return None
    s = str(value).strip()
    return s or None
