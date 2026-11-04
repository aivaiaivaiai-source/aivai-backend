# -*- coding: utf-8 -*-
"""Товары для новорождённых.

Вид — отдельный товар, не размер и не сезон.
Коляски, автокресла и переноски, одежда, обувь, питание, подгузники,
игрушки, кроватки и манежи, радионяни — соседние разделы Детского мира.
"""
from __future__ import annotations

from typing import Any


def _opts(*labels: str) -> list[dict[str, str]]:
    return [{"value": label, "label": label} for label in labels]


def _group(
    label: str,
    options: tuple[str, ...],
    kinds: tuple[str, ...] | None = None,
) -> dict[str, Any]:
    group: dict[str, Any] = {"label": label, "options": _opts(*options)}
    if kinds:
        group["applies_to"] = list(kinds)
    return group


_KINDS = (
    "Конверты на выписку",
    "Пелёнки",
    "Коконы и гнёздышки",
    "Постельное в кроватку",
    "Сумки в роддом",
    "Товары для кормления",
    "Ванночки и купание",
    "Шезлонги и электрокачели",
    "Ходунки",
    "Другие товары для новорождённых",
)


def build_newborn_goods_catalog() -> dict[str, Any]:
    return {
        "category_slug": "kids-tovary-dlya-novorozhdennyh",
        "label": "Товары для новорождённых",
        "question": "Какой товар?",
        "roles": _opts(*_KINDS),
        "filters": [
            _group("Продавец", ("Частное лицо", "Магазин", "Другой")),
            _group("Состояние", ("Новое", "Б/у")),
            _group("Пол", ("Для мальчика", "Для девочки", "Унисекс")),
            _group("Возраст", ("0-3 месяца", "3-6 месяцев", "6-12 месяцев")),
            _group(
                "Сезон",
                ("Лето", "Демисезон", "Зима"),
                ("Конверты на выписку",),
            ),
        ],
    }
