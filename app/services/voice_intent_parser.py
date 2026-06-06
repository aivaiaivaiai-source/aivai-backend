from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation

from app.schemas.voice import VoiceIntent

_SAVE_SEARCH = re.compile(
    r"(?:сохран(?:ить|и)\s+(?:этот\s+)?поиск|запомни(?:ть)?\s+поиск|save\s+(?:this\s+)?search)",
    re.IGNORECASE,
)
_CREATE_LISTING = re.compile(
    r"(?:созда(?:ть|й)\s+объявлени|новое\s+объявлени|добав(?:ить|ь)\s+объявлени"
    r"|create\s+(?:a\s+)?listing|add\s+listing)",
    re.IGNORECASE,
)
_SEARCH_LISTINGS = re.compile(
    r"(?:найди|найти|поиск|покажи\s+объявлен|show\s+listings|search\s+listings|\bfind\s+listings\b)",
    re.IGNORECASE,
)

_CATEGORY_ID = re.compile(
    r"(?:категори[яи]|category)\s*[:#]?\s*(\d+)",
    re.IGNORECASE,
)
_MIN_PRICE = re.compile(
    r"(?:^|\s)(?:от|from)\s+(\d+(?:[.,]\d+)?)",
    re.IGNORECASE,
)
_MAX_PRICE = re.compile(
    r"(?:^|\s)(?:до|to|under)\s+(\d+(?:[.,]\d+)?)",
    re.IGNORECASE,
)
_LISTING_PRICE = re.compile(
    r"(?:цена|price)\s*[:=]?\s*(\d+(?:[.,]\d+)?)",
    re.IGNORECASE,
)
_CURRENCY = re.compile(
    r"\b(USD|KGS|usd|kgs|долл(?:ар(?:ов)?)?|сом)\b",
    re.IGNORECASE,
)
_QUOTED = re.compile(r'["«]([^"»]{1,500})["»]')


def _parse_decimal(raw: str) -> Decimal | None:
    normalized = raw.replace(",", ".")
    try:
        return Decimal(normalized)
    except InvalidOperation:
        return None


def _normalize_currency_token(raw: str) -> str | None:
    t = raw.lower()
    if t in ("usd", "долл", "доллар", "долларов"):
        return "USD"
    if t in ("kgs", "сом"):
        return "KGS"
    if raw.upper() in ("USD", "KGS"):
        return raw.upper()
    return None


def extract_search_and_listing_params(text: str) -> dict[str, object]:
    """Pull structured hints from free-form text (shared across intents)."""
    out: dict[str, object] = {}

    m = _CATEGORY_ID.search(text)
    if m:
        out["category_id"] = int(m.group(1))

    m = _MIN_PRICE.search(text)
    if m:
        d = _parse_decimal(m.group(1))
        if d is not None:
            out["min_price"] = str(d)

    m = _MAX_PRICE.search(text)
    if m:
        d = _parse_decimal(m.group(1))
        if d is not None:
            out["max_price"] = str(d)

    m = _LISTING_PRICE.search(text)
    if m:
        d = _parse_decimal(m.group(1))
        if d is not None:
            out["price"] = str(d)

    m = _CURRENCY.search(text)
    if m:
        cur = _normalize_currency_token(m.group(1))
        if cur:
            out["currency"] = cur

    mq = _QUOTED.search(text)
    if mq:
        q = mq.group(1).strip()
        if q:
            out["q"] = q

    if "q" not in out:
        m_about = re.search(
            r"(?:про|about|for)\s+([^\n.!?]{1,200})",
            text,
            re.IGNORECASE,
        )
        if m_about:
            frag = m_about.group(1).strip()
            if frag:
                out["q"] = frag

    return out


def _extract_listing_title(text: str) -> str | None:
    m = _QUOTED.search(text)
    if m:
        t = m.group(1).strip()
        return t or None
    m2 = re.search(
        r"(?:название|title)\s*[:=]\s*([^\n.!?]{1,200})",
        text,
        re.IGNORECASE,
    )
    if m2:
        t = m2.group(1).strip()
        return t or None
    return None


def parse_voice_command(text: str) -> VoiceIntent:
    """Backward-compatible wrapper; use voice_intent_resolver.resolve_voice_intent."""
    from app.services.voice_intent_resolver import resolve_voice_intent

    return resolve_voice_intent(text).intent
