"""Beauty Package A — narrow AI medical/therapeutic claim guard.

Deterministic filter at the AI/content-generation boundary.
Does not ban ordinary marketplace wording (крем, уход, увлажнение, косметика).
Closes the Package A DOCUMENTED_GAP for unsupported AI-invented claims.
"""
from __future__ import annotations

import re
from typing import Iterable

from app.seeds.beauty_v2 import BEAUTY_AI_MEDICAL_CLAIM_FORBIDDEN_PATTERNS

# Normalized regex fragments for therapeutic claim detection.
# Keep narrow: only efficacy/disease-cure language, not ordinary care words.
_CLAIM_REGEXES: tuple[re.Pattern[str], ...] = (
    re.compile(r"лечит(?:ся)?", re.I),
    re.compile(r"лечебн\w*", re.I),
    re.compile(r"излечив\w*", re.I),
    re.compile(r"устраняет\s+заболевани\w*", re.I),
    re.compile(r"гарантирует\s+медицинск\w*", re.I),
    re.compile(r"медицинск\w*\s+результат\w*", re.I),
    re.compile(r"лечит\s+акне", re.I),
    re.compile(r"лечит\s+дерматит", re.I),
    re.compile(r"лечит\s+выпадение\s+волос", re.I),
    re.compile(r"dermatologically\s+proven", re.I),
    re.compile(r"cures?\b", re.I),
    re.compile(r"\btherapeutic\b", re.I),
)

_ORDINARY_ALLOWED = frozenset(
    {
        "крем",
        "уход",
        "увлажнение",
        "косметика",
        "шампунь",
        "маска",
        "гель",
        "сыворотка",
        "тоник",
        "бальзам",
    }
)


def normalize_claim_text(text: str) -> str:
    t = (text or "").casefold()
    t = re.sub(r"\s+", " ", t).strip()
    return t


def is_beauty_category_slug(slug: str | None) -> bool:
    if not slug:
        return False
    return slug == "beauty" or slug.startswith("beauty-")


def contains_unsupported_medical_claim(text: str) -> bool:
    """True when text includes unsupported therapeutic/medical efficacy language."""
    norm = normalize_claim_text(text)
    if not norm:
        return False
    for pat in _CLAIM_REGEXES:
        if pat.search(norm):
            return True
    for phrase in BEAUTY_AI_MEDICAL_CLAIM_FORBIDDEN_PATTERNS:
        if normalize_claim_text(phrase) in norm:
            return True
    return False


def claim_phrases_in(text: str) -> list[str]:
    """Return matched claim snippets for diagnostics/tests."""
    norm = normalize_claim_text(text)
    found: list[str] = []
    for pat in _CLAIM_REGEXES:
        for m in pat.finditer(norm):
            found.append(m.group(0))
    return found


def user_already_stated_claim(*, user_seed: str, claim_snippet: str) -> bool:
    """Allow pass-through only when the user already wrote the same claim language."""
    seed = normalize_claim_text(user_seed)
    snippet = normalize_claim_text(claim_snippet)
    if not seed or not snippet:
        return False
    return snippet in seed


def scrub_ai_invented_medical_claims(
    *,
    user_seed: str,
    generated: str,
) -> str:
    """Drop AI-invented therapeutic claims not present in user seed.

    If the whole generated string is an invented claim and seed is neutral,
    return the user seed (or empty). Otherwise strip claim-bearing sentences.
    """
    generated = (generated or "").strip()
    if not generated:
        return generated
    if not contains_unsupported_medical_claim(generated):
        return generated

    seed = (user_seed or "").strip()
    # If every claim phrase already exists in user text — keep generated.
    phrases = claim_phrases_in(generated)
    if phrases and all(
        user_already_stated_claim(user_seed=seed, claim_snippet=p) for p in phrases
    ):
        return generated

    # Strip sentences that introduce claims.
    parts = re.split(r"(?<=[.!?])\s+", generated)
    kept: list[str] = []
    for part in parts:
        if contains_unsupported_medical_claim(part):
            # Keep only if user already stated that claim language.
            part_phrases = claim_phrases_in(part)
            if part_phrases and all(
                user_already_stated_claim(user_seed=seed, claim_snippet=p)
                for p in part_phrases
            ):
                kept.append(part)
            continue
        kept.append(part)
    scrubbed = " ".join(kept).strip()
    if scrubbed:
        return scrubbed
    # Fall back to neutral user seed (never strengthen).
    if seed and not contains_unsupported_medical_claim(seed):
        return seed
    return ""


def assert_ordinary_words_not_banned(words: Iterable[str] | None = None) -> None:
    sample = tuple(words) if words is not None else tuple(_ORDINARY_ALLOWED)
    for w in sample:
        if contains_unsupported_medical_claim(w):
            raise AssertionError(f"ordinary Beauty word incorrectly banned: {w}")
