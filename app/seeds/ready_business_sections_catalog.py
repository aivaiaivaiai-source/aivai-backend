# -*- coding: utf-8 -*-
"""Продажа «Готовый бизнес и франшизы».

Вид — форма точки: магазин, бутик, островок, цех. Не ассортимент внутри неё.
Оборудование, витрины и станки остаются в «Оборудовании для бизнеса».
Помещения сами по себе — Коммерческая недвижимость.
Лекарства остаются вне каталога: аптека здесь — действующая точка, не полка.

Shares/Investment, Crypto, Ready OsOO, Turnkey L2 — retired from active catalog.
Package A Create cores are NOT defined here (taxonomy / product identity only).
"""
from __future__ import annotations

from typing import Any

from app.seeds.ready_business_v2 import (
    build_ready_business_v2_sections,
    ready_business_v2_assert_cleanup_contracts,
)

ready_business_v2_assert_cleanup_contracts()

READY_BUSINESS_SECTIONS: dict[str, dict[str, Any]] = build_ready_business_v2_sections()


def build_ready_business_section_catalog(section_key: str) -> dict[str, Any] | None:
    return READY_BUSINESS_SECTIONS.get(section_key)
