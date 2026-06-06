from __future__ import annotations

import re
import unicodedata

# Common Cyrillic → Latin for automotive / marketplace matching
_CYRILLIC_TO_LATIN: dict[str, str] = {
    "а": "a",
    "б": "b",
    "в": "v",
    "г": "g",
    "д": "d",
    "е": "e",
    "ё": "e",
    "ж": "zh",
    "з": "z",
    "и": "i",
    "й": "y",
    "к": "k",
    "л": "l",
    "м": "m",
    "н": "n",
    "о": "o",
    "п": "p",
    "р": "r",
    "с": "s",
    "т": "t",
    "у": "u",
    "ф": "f",
    "х": "h",
    "ц": "c",
    "ч": "ch",
    "ш": "sh",
    "щ": "sch",
    "ъ": "",
    "ы": "y",
    "ь": "",
    "э": "e",
    "ю": "yu",
    "я": "ya",
}

# Spoken / colloquial token normalizations (applied before compact pass)
_COLLOQUIAL_REPLACEMENTS: tuple[tuple[str, str], ...] = (
    (r"\bешка\b", "e class"),
    (r"\bцешка\b", "c class"),
    (r"\bешку\b", "e class"),
    (r"\bсемидесятка\b", "70"),
    (r"\bлексус\b", "lexus"),
    (r"лх", "lx"),
    (r"\bмерс\b", "mercedes"),
    (r"\bбид\b", "byd"),
    (r"\bлисян\b", "lixiang"),
    (r"\bджили\b", "geely"),
    (r"\bджеили\b", "geely"),
    (r"\bкамри\b", "camry"),
)

_MULTI_SEPARATOR = re.compile(r"[\s\-_./\\]+")
_DUPLICATE_SEP = re.compile(r"[-\s]{2,}")


def transliterate_to_latin(text: str) -> str:
    out: list[str] = []
    for ch in text:
        low = ch.lower()
        if low in _CYRILLIC_TO_LATIN:
            out.append(_CYRILLIC_TO_LATIN[low])
        else:
            out.append(ch)
    return "".join(out)


def normalize_text(text: str) -> str:
    """
    Canonical spaced form for display matching:
    lower → trim → NFKD → collapse separators → colloquial hints.
    """
    lowered = text.lower().strip()
    nfkd = unicodedata.normalize("NFKD", lowered)
    ascii_like = "".join(c for c in nfkd if not unicodedata.combining(c))
    spaced = _MULTI_SEPARATOR.sub(" ", ascii_like)
    spaced = _DUPLICATE_SEP.sub(" ", spaced)
    spaced = re.sub(r"\s+", " ", spaced).strip()
    for pattern, replacement in _COLLOQUIAL_REPLACEMENTS:
        spaced = re.sub(pattern, replacement, spaced, flags=re.IGNORECASE)
    spaced = re.sub(r"\s+", " ", spaced).strip()
    return spaced


def normalize_alias_compact(text: str) -> str:
    """
    Compact lookup key: no spaces/hyphens, latinized.
    "LX 570" / "лх570" / "lx570" → "lx570"
    """
    base = normalize_text(text)
    latin = transliterate_to_latin(base)
    return re.sub(r"[^a-z0-9]", "", latin)


def normalize_alias_keys(text: str) -> tuple[str, str]:
    """Return (spaced_normalized, compact_normalized) for dual-index lookup."""
    spaced = normalize_text(text)
    compact = normalize_alias_compact(text)
    return spaced, compact


def slugify(value: str) -> str:
    normalized = normalize_text(value)
    slug = re.sub(r"[^a-z0-9]+", "-", normalized).strip("-")
    return slug[:160] or "item"


def alias_lookup_variants(text: str) -> list[str]:
    """Generate normalized keys to try when resolving aliases from user text."""
    spaced, compact = normalize_alias_keys(text)
    variants: list[str] = []
    for key in (compact, spaced):
        if key and key not in variants:
            variants.append(key)
    for token in spaced.split():
        if len(token) < 2:
            continue
        t_compact = normalize_alias_compact(token)
        for key in (t_compact, token):
            if key and key not in variants:
                variants.append(key)
    return variants
