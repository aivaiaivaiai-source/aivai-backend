# -*- coding: utf-8 -*-
"""Продажа «Медтовары» — active modern catalog (Medical V2 foundation).

Licensed medicines remain OUT. БАДы retired (NO_CANONICAL_DESTINATION).
Clinic installations stay Business Equipment. Kids / Vet / Beauty boundaries preserved.
"""
from __future__ import annotations

from typing import Any

from app.seeds.medical_v2 import (
    build_all_medical_v2_section_catalogs,
    build_medical_v2_section_catalog,
    medical_v2_assert_cleanup_contracts,
)

medical_v2_assert_cleanup_contracts()
MED_SECTIONS: dict[str, dict[str, Any]] = build_all_medical_v2_section_catalogs()


def build_med_section_catalog(section_key: str) -> dict[str, Any] | None:
    return build_medical_v2_section_catalog(section_key)
