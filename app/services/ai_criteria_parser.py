"""Rule-based criteria extraction → normalized contract dict."""

from __future__ import annotations

import re
from typing import Any

from app.core.ai_search_criteria import (
    BRAND_ALIASES,
    MODEL_ALIASES,
    MODEL_BRAND_HINT,
    AiSearchCriteria,
    Steering,
    normalize_engine_volume,
    normalize_model,
)

_PRICE_RE = re.compile(
    r"(?:до|max|не\s+более)\s*(\d[\d\s]*)\s*(?:сом|som|₸|kgs)?",
    re.IGNORECASE,
)
_PRICE_FROM_RE = re.compile(
    r"(?:от|from|минимум)\s*(\d[\d\s]*)\s*(?:сом|som|₸|kgs)?",
    re.IGNORECASE,
)
_YEAR_RE = re.compile(r"\b(19|20)\d{2}\b")
_ROOMS_RE = re.compile(r"(\d)\s*[-\s]?(?:комн|комнат|room)", re.IGNORECASE)
_ENGINE_EXPLICIT_RE = re.compile(
    r"(?:объ[её]м(?:\s+двигателя)?|двигател\w*|engine(?:\s+volume)?)\s*[:=]?\s*"
    r"(\d(?:[.,]\d{1,2})?)",
    re.IGNORECASE,
)
_ENGINE_LITERS_RE = re.compile(
    r"\b(\d(?:[.,]\d{1,2})?)\s*(?:л|литр(?:а|ов)?|l)\b",
    re.IGNORECASE,
)

_CITIES = (
    "бишкек",
    "ош",
    "каракол",
    "джалал-абад",
    "jalal-abad",
    "талас",
    "нарын",
    "баткен",
    "кант",
    "tokmok",
    "токмок",
)

_CITY_CANON = {
    "бишкек": "Бишкек",
    "ош": "Ош",
    "каракол": "Каракол",
    "джалал-абад": "Джалал-Абад",
    "jalal-abad": "Джалал-Абад",
    "талас": "Талас",
    "нарын": "Нарын",
    "баткен": "Баткен",
    "кант": "Кант",
    "tokmok": "Токмок",
    "токмок": "Токмок",
}


def parse_criteria(text: str, *, agent_type: str) -> dict[str, Any]:
    raw = text.strip()
    lowered = raw.lower()
    q = raw or None
    min_price: int | None = None
    max_price: int | None = None
    year_min: int | None = None
    year_max: int | None = None
    rooms: int | None = None
    city: str | None = None
    brand: str | None = None
    model: str | None = None
    engine_volume: str | None = None
    steering: Steering | None = None
    employment: str | None = None

    max_match = _PRICE_RE.search(lowered)
    if max_match:
        max_price = _digits(max_match.group(1))

    min_match = _PRICE_FROM_RE.search(lowered)
    if min_match:
        min_price = _digits(min_match.group(1))

    if min_price is None and max_price is None:
        plain_price = re.search(r"\b(\d{4,7})\b", lowered)
        if plain_price:
            max_price = _digits(plain_price.group(1))

    years = [int(y.group()) for y in _YEAR_RE.finditer(raw)]
    if years:
        year_min = min(years)
        year_max = max(years)

    rooms_m = _ROOMS_RE.search(lowered)
    if rooms_m:
        rooms = int(rooms_m.group(1))

    for city_key in _CITIES:
        if city_key in lowered:
            city = _CITY_CANON.get(city_key, city_key.title())
            break

    if agent_type == "ai_auto":
        for alias, canon in sorted(BRAND_ALIASES.items(), key=lambda x: -len(x[0])):
            if alias in lowered:
                brand = canon
                break
        model = _extract_model(lowered, brand=brand)
        if model and brand is None:
            brand = MODEL_BRAND_HINT.get(model)
        engine_volume = _extract_engine_volume(lowered)
        if "левый" in lowered or "left" in lowered:
            steering = "left"
        if "правый" in lowered or "right" in lowered:
            steering = "right"

    if agent_type == "ai_hr":
        for kw in ("удалён", "remote", "офис", "part-time", "полная"):
            if kw in lowered:
                employment = kw
                break

    return AiSearchCriteria(
        q=q,
        city=city,
        min_price=min_price,
        max_price=max_price,
        year_min=year_min,
        year_max=year_max,
        brand=brand,
        model=model,
        engine_volume=engine_volume,
        steering=steering,
        rooms=rooms,
        employment=employment,
    ).to_dict()


def _extract_model(lowered: str, *, brand: str | None) -> str | None:
    # Longest alias first so "santa fe" / "land cruiser" win over short tokens.
    candidates: list[tuple[int, str]] = []
    for alias, canon in MODEL_ALIASES.items():
        if alias in lowered:
            hint = MODEL_BRAND_HINT.get(canon)
            if brand and hint and hint != brand:
                continue
            candidates.append((len(alias), canon))
    if not candidates:
        return None
    candidates.sort(key=lambda x: -x[0])
    return normalize_model(candidates[0][1])


def _extract_engine_volume(lowered: str) -> str | None:
    explicit = _ENGINE_EXPLICIT_RE.search(lowered)
    if explicit:
        return normalize_engine_volume(explicit.group(1))
    liters = _ENGINE_LITERS_RE.search(lowered)
    if liters:
        return normalize_engine_volume(liters.group(1))
    return None


def _digits(value: str) -> int:
    return int(re.sub(r"\s+", "", value))


__all__ = (
    "AiSearchCriteria",
    "normalize_brand",
    "normalize_model",
    "normalize_engine_volume",
    "parse_criteria",
)
