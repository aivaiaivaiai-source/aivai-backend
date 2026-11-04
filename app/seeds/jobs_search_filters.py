# -*- coding: utf-8 -*-
"""Jobs Search V2 — Backend SoT for category_filters (hiring / job_seeking).

Hiring filters: same keys as JOB_SECTIONS groups (+ always work_schedule /
job_conditions when present in Jobs V2 create), but experience / work_schedule
options use Jobs V2 create vocabulary (not legacy JOB_SECTIONS ladders).

Job-seeking filters: searchable subset of Jobs V2 create seeking fields
(not a mechanical copy of all create fields — no contact_methods).
"""
from __future__ import annotations

from typing import Any

from app.models.category_enums import CategoryFilterType
from app.models.job_create_intent import HIRING, JOB_SEEKING
from app.seeds.jobs_create_fields import (
    CONDITIONS,
    CREATE_EXPERIENCE,
    JOBS_V2_CANONICAL_SLUGS,
    WORK_MODE,
    WORK_SCHEDULE,
    _FILTER_LABEL_TO_KEY,
)
from app.seeds.jobs_sections_catalog import JOB_SECTIONS
from app.seeds.jobs_seeking_fields import (
    _AGRI_LICENSE_ROLES,
    _EMPLOYMENT,
    _ENTERTAINMENT_CERT_ROLES,
    _READY,
    _TRANSPORT_DRIVER_ROLES,
    _TRANSPORT_ROUTE_ROLES,
    _sector_extras,
)

_MULTI = CategoryFilterType.multi_select

# Legacy search «График» group → stable key (create uses work_schedule separately).
_HIRING_LABEL_TO_KEY = {
    **_FILTER_LABEL_TO_KEY,
    "График": "work_schedule",
}

# Display labels for hiring search (UX clarity; keys unchanged).
_HIRING_DISPLAY_LABELS: dict[str, str] = {
    "employer": "Работодатель",
    "work_format": "Формат работы",
    "work_schedule": "График работы",
    "work_mode": "Режим работы",
    "experience": "Требуемый опыт",
    "pay_type": "Тип оплаты",
    "route": "Маршрут",
    "housing": "Проживание",
    "object_type": "Объект",
    "when_available": "Когда",
    "country": "Страна",
    "formalization": "Оформление",
    "job_conditions": "Условия",
}

# Keys whose search options must match Jobs V2 create vocabulary exactly.
_HIRING_CREATE_VOCAB: dict[str, tuple[str, ...]] = {
    "experience": CREATE_EXPERIENCE,
    "work_schedule": WORK_SCHEDULE,
    "work_mode": WORK_MODE,
    "job_conditions": CONDITIONS,
}


def _opts(*labels: str) -> list[dict[str, str]]:
    return [{"value": label, "label": label} for label in labels]


def _cfg(
    options: list[dict[str, str]],
    *,
    depends_on: dict[str, Any] | None = None,
) -> dict[str, Any]:
    out: dict[str, Any] = {"options": options}
    if depends_on:
        out["depends_on"] = depends_on
    return out


def _filter(
    key: str,
    label: str,
    ftype: CategoryFilterType,
    sort_order: int,
    config: dict[str, Any] | None,
) -> tuple[str, str, CategoryFilterType, int, dict[str, Any] | None]:
    return (key, label, ftype, sort_order, config)


def hiring_filters_for_section(section: dict[str, Any]) -> list[
    tuple[str, str, CategoryFilterType, int, dict[str, Any] | None]
]:
    """Sector-aware hiring search filters aligned with Jobs V2 create values."""
    out: list[tuple[str, str, CategoryFilterType, int, dict[str, Any] | None]] = []
    sort_i = 0
    seen: set[str] = set()
    for group in section.get("filters") or []:
        source_label = group["label"]
        key = _HIRING_LABEL_TO_KEY.get(source_label)
        if key is None:
            continue
        if key in _HIRING_CREATE_VOCAB:
            options = _opts(*_HIRING_CREATE_VOCAB[key])
        else:
            options = [
                {"value": o["value"], "label": o["label"]}
                for o in group.get("options") or []
            ]
        display = _HIRING_DISPLAY_LABELS.get(key, source_label)
        out.append(_filter(key, display, _MULTI, sort_i, _cfg(options)))
        seen.add(key)
        sort_i += 1

    # Create always adds work_schedule for canonical hiring (not from legacy «График»).
    if "work_schedule" not in seen:
        out.append(
            _filter(
                "work_schedule",
                _HIRING_DISPLAY_LABELS["work_schedule"],
                _MULTI,
                sort_i,
                _cfg(_opts(*WORK_SCHEDULE)),
            )
        )
        sort_i += 1
        seen.add("work_schedule")

    # Create always has work_mode; hiring search must expose it (multi_select).
    if "work_mode" not in seen:
        out.append(
            _filter(
                "work_mode",
                _HIRING_DISPLAY_LABELS["work_mode"],
                _MULTI,
                sort_i,
                _cfg(_opts(*WORK_MODE)),
            )
        )
        sort_i += 1
        seen.add("work_mode")

    # Create always has job_conditions; hiring search must expose it.
    if "job_conditions" not in seen:
        out.append(
            _filter(
                "job_conditions",
                _HIRING_DISPLAY_LABELS["job_conditions"],
                _MULTI,
                sort_i,
                _cfg(_opts(*CONDITIONS)),
            )
        )
    return out


def _seeking_common() -> list[
    tuple[str, str, CategoryFilterType, int, dict[str, Any] | None]
]:
    # No desired-salary search filter (UX); create listing price unchanged.
    # All option-based seeking filters are multi_select (same UX as Условия).
    return [
        _filter(
            "employment",
            "Занятость",
            _MULTI,
            0,
            _cfg(_opts(*_EMPLOYMENT)),
        ),
        _filter(
            "experience",
            "Опыт работы",
            _MULTI,
            1,
            _cfg(_opts(*CREATE_EXPERIENCE)),
        ),
        _filter(
            "work_schedule",
            "Желаемый график работы",
            _MULTI,
            2,
            _cfg(_opts(*WORK_SCHEDULE)),
        ),
        _filter(
            "ready_to_start",
            "Готовность выйти",
            _MULTI,
            3,
            _cfg(_opts(*_READY)),
        ),
        _filter(
            "job_conditions",
            "Условия",
            _MULTI,
            4,
            _cfg(_opts(*CONDITIONS)),
        ),
    ]


def _seeking_extras_as_filters(
    slug: str,
) -> list[tuple[str, str, CategoryFilterType, int, dict[str, Any] | None]]:
    """Map seeking create FieldDefs → searchable filters (skip non-searchable)."""
    extras = _sector_extras(slug)
    out: list[tuple[str, str, CategoryFilterType, int, dict[str, Any] | None]] = []
    sort_base = 10
    for i, field in enumerate(extras):
        key, label, _ftype, _req, options, _hint = field
        choices = (options or {}).get("choices") or []
        opt_list = [
            {"value": c["value"], "label": c["label"]}
            if isinstance(c, dict)
            else {"value": str(c), "label": str(c)}
            for c in choices
        ]
        depends = (options or {}).get("depends_on")
        # Search: option-based extras are always multi_select (OR/ANY).
        # Create field_type may still be select — search UX is independent.
        out.append(
            _filter(
                key,
                label,
                _MULTI,
                sort_base + i,
                _cfg(opt_list, depends_on=depends),
            )
        )
    return out


def seeking_filters_for_slug(
    slug: str,
) -> list[tuple[str, str, CategoryFilterType, int, dict[str, Any] | None]]:
    return _seeking_common() + _seeking_extras_as_filters(slug)


def build_jobs_search_filters() -> dict[
    str, dict[str, list[tuple[str, str, CategoryFilterType, int, dict[str, Any] | None]]]
]:
    """slug → {hiring|job_seeking → filter defs}."""
    by_slug: dict[
        str,
        dict[
            str,
            list[tuple[str, str, CategoryFilterType, int, dict[str, Any] | None]],
        ],
    ] = {}
    for section in JOB_SECTIONS.values():
        slug = section["category_slug"]
        if slug not in JOBS_V2_CANONICAL_SLUGS:
            continue
        by_slug[slug] = {
            HIRING: hiring_filters_for_section(section),
            JOB_SEEKING: seeking_filters_for_slug(slug),
        }
    return by_slug


# Silence unused-import lint for depends role constants used via _sector_extras.
_ = (
    _TRANSPORT_DRIVER_ROLES,
    _TRANSPORT_ROUTE_ROLES,
    _ENTERTAINMENT_CERT_ROLES,
    _AGRI_LICENSE_ROLES,
)
