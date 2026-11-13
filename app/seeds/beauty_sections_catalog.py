# -*- coding: utf-8 -*-
"""Продажа «Красота и личный уход» — V2 section catalog (taxonomy mirror).

Вид — сам товар. Услуги парикмахера, маникюра, бровей, косметологии,
депиляции, массажа и тату остаются в «Услугах».
Подгузники / влажные салфетки / детский крем — Kids.
БАДы / лекарства / medical devices — Medical (БАДы retired, no Beauty move).
Кресла / мойки / лазерные установки салона — Business Equipment.
Фены / плойки / эпиляторы и др. персональные устройства — Beauty (не Electronics).
Парики — Beauty. Косметички / украшения для пирсинга — Fashion (GAP if no exact kind).

V2 structured target: seller + semantic Condition (durable allowlist only).
Brand / model / volume / SPF / skin / hair / package_state → Description.
Package A Create cores are NOT defined here.
"""
from __future__ import annotations

from typing import Any

from app.seeds.beauty_v2 import (
    build_beauty_v2_sections,
    beauty_v2_assert_cleanup_contracts,
)

beauty_v2_assert_cleanup_contracts()

BEAUTY_SECTIONS: dict[str, dict[str, Any]] = build_beauty_v2_sections()


def build_beauty_section_catalog(section_key: str) -> dict[str, Any] | None:
    return BEAUTY_SECTIONS.get(section_key)
