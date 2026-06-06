from __future__ import annotations

import re
from dataclasses import dataclass

from app.schemas.voice import VoiceIntent
from app.services.voice_intent_parser import (
    _CREATE_LISTING,
    _SAVE_SEARCH,
    _SEARCH_LISTINGS,
    _extract_listing_title,
    extract_search_and_listing_params,
)

_SELL_LISTING = re.compile(
    r"(?:прода(?:ю|ть)|продам|сдаю|отдаю|меняю\s+)",
    re.IGNORECASE,
)
_BUY_SEARCH = re.compile(
    r"(?:куплю|ищу|нужен|нужна|надо|хочу\s+купить|want\s+to\s+buy)",
    re.IGNORECASE,
)
_BUY_OBJECT = re.compile(
    r"(?:куплю|ищу|нужен|нужна|надо|хочу\s+купить)\s+(.+)",
    re.IGNORECASE,
)
_AMBIGUOUS_BOTH = re.compile(
    r"(?:прода(?:ю|ть)|продам).*(?:куплю|ищу)|(?:куплю|ищу).*(?:прода(?:ю|ть)|продам)",
    re.IGNORECASE,
)

_AMBIGUITY_MESSAGE = (
    "Уточните, пожалуйста: вы хотите продать своё объявление или найти и купить?"
)


@dataclass(frozen=True)
class ResolvedVoiceIntent:
    intent: VoiceIntent
    ambiguous: bool = False
    ambiguity_message: str | None = None


def resolve_voice_intent(text: str) -> ResolvedVoiceIntent:
    """
    Resolve voice intent with seller vs buyer disambiguation.

    - продаю / продам / сдаю / отдаю / меняю → create_listing
    - куплю / ищу / нужен / нужна / надо → search_listings
    - ambiguous (both cues) → needs_clarification via VoiceService
    """
    raw = text.strip()
    if not raw:
        return ResolvedVoiceIntent(
            VoiceIntent(intent="unknown", confidence=0.0, extracted={}),
        )

    base = extract_search_and_listing_params(raw)

    if _SAVE_SEARCH.search(raw):
        return ResolvedVoiceIntent(
            VoiceIntent(intent="save_search", confidence=0.92, extracted=dict(base)),
        )

    if _CREATE_LISTING.search(raw):
        merged = dict(base)
        title = _extract_listing_title(raw)
        if title:
            merged["title"] = title
        return ResolvedVoiceIntent(
            VoiceIntent(intent="create_listing", confidence=0.9, extracted=merged),
        )

    if _SEARCH_LISTINGS.search(raw):
        return ResolvedVoiceIntent(
            VoiceIntent(intent="search_listings", confidence=0.88, extracted=dict(base)),
        )

    has_sell = bool(_SELL_LISTING.search(raw))
    has_buy = bool(_BUY_SEARCH.search(raw))

    if has_sell and has_buy or _AMBIGUOUS_BOTH.search(raw):
        return ResolvedVoiceIntent(
            VoiceIntent(intent="unknown", confidence=0.35, extracted=dict(base)),
            ambiguous=True,
            ambiguity_message=_AMBIGUITY_MESSAGE,
        )

    if has_buy and not has_sell:
        merged = dict(base)
        mobj = _BUY_OBJECT.search(raw)
        if mobj:
            q = mobj.group(1).strip()
            if q:
                merged["q"] = q
        elif "q" not in merged:
            merged["q"] = raw
        return ResolvedVoiceIntent(
            VoiceIntent(intent="search_listings", confidence=0.82, extracted=merged),
        )

    if has_sell and not has_buy:
        merged = dict(base)
        title = _extract_listing_title(raw)
        if title:
            merged["title"] = title
        return ResolvedVoiceIntent(
            VoiceIntent(intent="create_listing", confidence=0.78, extracted=merged),
        )

    return ResolvedVoiceIntent(
        VoiceIntent(intent="unknown", confidence=0.25, extracted=dict(base)),
    )
