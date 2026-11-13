# -*- coding: utf-8 -*-
"""Продажа «Спорт, отдых и хобби» — V2 section catalog (taxonomy mirror).

Вид — сам товар. Одежда/обувь — Fashion. Детский спорт/транспорт — Kids.
Велосипеды / электросамокаты / водный транспорт — Transport.
Коммерческие тренажёры / бильярд — Business Equipment.
Приставки / наушники / общее аудио — Electronics.
Книги / ноты / краски — Stationery. Пряжа / ткани — Materials.
Лошади — Animals; амуниция — здесь.
Эхолоты — Sport/Fishing (marketplace fishing intent).
Охотничьи ножи / оружие — retired / absent.
Юрты / шырдаки — retired (no destination in this cleanup).

Package A Create cores are NOT defined here.
"""
from __future__ import annotations

from typing import Any

from app.seeds.sport_v2 import (
    build_sport_v2_sections,
    sport_v2_assert_cleanup_contracts,
)

sport_v2_assert_cleanup_contracts()

SPORT_SECTIONS: dict[str, dict[str, Any]] = build_sport_v2_sections()


def build_sport_section_catalog(section_key: str) -> dict[str, Any] | None:
    return SPORT_SECTIONS.get(section_key)
