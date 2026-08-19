from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from typing import Any

from app.models.enums import AiAgentType, Currency


_AGENT_DOMAIN_SLUGS: dict[AiAgentType, tuple[str, ...]] = {
    AiAgentType.ai_realtor: (
        "real-estate-sale",
        "real-estate-rent",
        "real-estate-commercial",
    ),
    AiAgentType.ai_auto: (
        "transport-car-sale",
        "transport-cars",
    ),
    AiAgentType.ai_hr: (
        "jobs-vacancies",
        "jobs-resume",
    ),
}

_PRICE_RE = re.compile(
    r"(?:до|max|не\s+более)\s*[\$]?\s*([\d\s]+(?:[.,]\d+)?)\s*(?:\$|usd|долл)?",
    re.IGNORECASE,
)
_USD_RE = re.compile(r"\$|usd|долл", re.IGNORECASE)
_LEFT_STEER_RE = re.compile(r"лев(?:ый|ого)?\s+рул", re.IGNORECASE)
_RIGHT_STEER_RE = re.compile(r"прав(?:ый|ого)?\s+рул", re.IGNORECASE)
_BRAND_MODEL_PATTERNS = (
    re.compile(r"\b(toyota|camry|bmw|mercedes|honda|hyundai|kia|lexus|nissan|mazda)\b", re.I),
)


def agent_domain_slugs(agent_type: AiAgentType) -> tuple[str, ...]:
    return _AGENT_DOMAIN_SLUGS[agent_type]


def parse_search_criteria(text: str, agent_type: AiAgentType) -> dict[str, Any]:
    """
    Lightweight rule-based parser (no LLM).
    Converts natural language into structured search criteria.
    """
    raw = text.strip()
    lowered = raw.lower()
    criteria: dict[str, Any] = {"q": raw}

    year_matches = re.findall(r"\b((?:19|20)\d{2})\b", raw)
    if year_matches:
        years_int = [int(y) for y in year_matches]
        if "от" in lowered or "from" in lowered or "с " in lowered:
            criteria["year_min"] = min(years_int)
        elif len(years_int) == 1:
            criteria["year_min"] = years_int[0]
        else:
            criteria["year_min"] = min(years_int)
            criteria["year_max"] = max(years_int)

    price_match = _PRICE_RE.search(raw)
    if price_match:
        num_raw = price_match.group(1).replace(" ", "").replace(",", ".")
        try:
            criteria["max_price"] = float(Decimal(num_raw))
        except (InvalidOperation, ValueError):
            pass

    if _USD_RE.search(raw):
        criteria["currency"] = Currency.USD.value
    elif "сом" in lowered or "som" in lowered:
        criteria["currency"] = Currency.KGS.value

    if _LEFT_STEER_RE.search(raw):
        criteria["steering"] = "left"
    elif _RIGHT_STEER_RE.search(raw):
        criteria["steering"] = "right"

    if agent_type == AiAgentType.ai_auto:
        for pat in _BRAND_MODEL_PATTERNS:
            m = pat.search(raw)
            if m:
                token = m.group(1).lower()
                if token == "camry":
                    criteria.setdefault("brand", "Toyota")
                    criteria["model"] = "Camry"
                elif token == "toyota":
                    criteria.setdefault("brand", "Toyota")
                else:
                    criteria.setdefault("brand", token.title())
                criteria["q"] = token
                break

    if agent_type == AiAgentType.ai_realtor:
        for kw in ("квартира", "дом", "участок", "офис", "аренда", "продаж"):
            if kw in lowered:
                criteria["property_hint"] = kw
                break

    if agent_type == AiAgentType.ai_hr:
        if any(w in lowered for w in ("ищу работу", "резюме", "ваканс")):
            criteria["job_mode"] = "seek_job"
        elif any(w in lowered for w in ("ищу сотрудника", "требуется", "найму")):
            criteria["job_mode"] = "seek_employee"

    return criteria


def merge_criteria(existing: dict[str, Any], new: dict[str, Any]) -> dict[str, Any]:
    merged = dict(existing)
    for key, value in new.items():
        if value is None:
            continue
        if isinstance(value, str) and not value.strip():
            continue
        merged[key] = value
    return merged


def criteria_summary(criteria: dict[str, Any], agent_type: AiAgentType) -> str:
    parts: list[str] = []
    q = criteria.get("q")
    if isinstance(q, str) and q.strip():
        parts.append(q.strip())
    if criteria.get("year_min"):
        parts.append(f"от {criteria['year_min']} г.")
    if criteria.get("max_price"):
        cur = criteria.get("currency", "USD")
        parts.append(f"до {criteria['max_price']} {cur}")
    if criteria.get("steering") == "left":
        parts.append("левый руль")
    if criteria.get("brand"):
        parts.append(str(criteria["brand"]))
    if criteria.get("model"):
        parts.append(str(criteria["model"]))
    if not parts:
        agent_labels = {
            AiAgentType.ai_realtor: "недвижимость",
            AiAgentType.ai_auto: "автомобиль",
            AiAgentType.ai_hr: "работу или сотрудника",
        }
        return f"Подбор: {agent_labels.get(agent_type, 'объявления')}"
    return " · ".join(parts)
