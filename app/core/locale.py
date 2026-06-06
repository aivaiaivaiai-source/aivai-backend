from __future__ import annotations

from enum import Enum


class SupportedLocale(str, Enum):
    """Locales prepared for multilingual aliases and rules (no translations yet)."""

    ru = "ru"
    kg = "kg"
    en = "en"


DEFAULT_LOCALE = SupportedLocale.ru


def normalize_locale(value: str | None) -> str:
    if not value:
        return DEFAULT_LOCALE.value
    lowered = value.strip().lower()
    if lowered in {e.value for e in SupportedLocale}:
        return lowered
    return DEFAULT_LOCALE.value
