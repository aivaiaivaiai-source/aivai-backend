# -*- coding: utf-8 -*-
"""Create-listing core_fields for L1 «Работа» — hiring (employer) SoT.

Jobs V2: hiring schema is the former Jobs Backend Pilot, scoped with
create_intent='hiring'. Canonical sectors = 20 industry leaves.
Meta leaves (без опыта / резюме) keep seed definitions for DB rows but are
excluded from Jobs V2 create picker.
"""
from __future__ import annotations

from typing import Any

from app.models.category_enums import CategoryFieldType
from app.models.job_create_intent import HIRING
from app.seeds.home_garden_filters import FieldDef
from app.seeds.jobs_sections_catalog import JOB_SECTIONS

_E = CategoryFieldType.enum
_MS = CategoryFieldType.multi_select
_T = CategoryFieldType.time
_P = CategoryFieldType.price

_FILTER_LABEL_TO_KEY: dict[str, str] = {
    "Работодатель": "employer",
    "Формат": "work_format",
    "Опыт": "experience",
    "Оплата": "pay_type",
    "Маршрут": "route",
    "Проживание": "housing",
    "Объект": "object_type",
    "Когда": "when_available",
    "Страна": "country",
    "Оформление": "formalization",
    "Занятость": "employment",
    "Готовность выйти": "ready_to_start",
}

_SALARY_PAYOUT = (
    "Ежедневно",
    "Еженедельно",
    "2 раза в месяц",
    "Ежемесячно",
)
_BONUSES = ("Есть", "Нет")
_CREATE_EXPERIENCE = (
    "Без опыта",
    "До 1 года",
    "1–2 года",
    "2–4 года",
    "4–6 лет",
    "Более 6 лет",
)
_CONDITIONS = (
    "Обучение",
    "Развоз",
    "Бесплатное питание",
    "Проживание",
    "Спецодежда",
    "Оплачиваемая стажировка",
    "Официальное трудоустройство",
    "Соцпакет",
    "Оплата переработок",
    "Карьерный рост",
)
_WORK_SCHEDULE = (
    "Полный день",
    "Сменный график",
    "Гибкий график",
    "Неполный день",
    "Вахтовый метод",
)
_WORK_MODE = (
    "5/2",
    "6/1",
    "4/3",
    "3/3",
    "2/2",
    "2/1",
    "1/2",
    "3/1",
    "По договорённости",
)
_WORK_HOURS = tuple(
    [f"{h}:00" for h in range(6, 24)] + [f"{h}:00" for h in range(0, 6)]
)
_CONTACT_METHODS = (
    "Только чат",
    "Только телефон",
    "Чат + телефон",
    "Чат + Wapp",
    "Телефон + Wapp",
    "Чат + Тел. + Wapp",
)

# Jobs V2 create picker — exactly 19 industry sectors (abroad = geography, not sector).
JOBS_V2_CANONICAL_SLUGS: tuple[str, ...] = (
    "jobs-shveynoe-proizvodstvo",
    "jobs-proizvodstvo-i-promyshlennost",
    "jobs-stroitelstvo-i-remont",
    "jobs-transport-i-logistika",
    "jobs-prodazhi-i-torgovlya",
    "jobs-ofis-i-administratsiya",
    "jobs-buhgalteriya-i-finansy",
    "jobs-marketing-reklama-i-media",
    "jobs-it-i-tehnologii",
    "jobs-obrazovanie-i-obuchenie",
    "jobs-meditsina-i-farmatsevtika",
    "jobs-krasota-i-zdorove",
    "jobs-gostinitsy-kafe-i-restorany",
    "jobs-sto-i-avtoservis",
    "jobs-razvlecheniya-i-sport",
    "jobs-domashniy-personal",
    "jobs-ohrana-i-bezopasnost",
    "jobs-selskoe-hozyaystvo",
    "jobs-studenty-i-podrabotka",
)

JOBS_V2_META_SLUGS: frozenset[str] = frozenset(
    {
        "jobs-vakansii-bez-opyta",
        "jobs-rezyume-soiskateley",
    }
)

JOBS_V2_LEGACY_SLUGS: frozenset[str] = frozenset(
    {
        "jobs-vacancies",
        "jobs-resume",
    }
)

# Vacancy/resume buckets are not profession sectors. Kept as rows, not publishable.
JOBS_V2_RETIRED_LEGACY_SLUGS: frozenset[str] = (
    JOBS_V2_META_SLUGS | JOBS_V2_LEGACY_SLUGS
)

# Soft-inactive: abroad is geography, not a profession. Legacy vacancy/resume
# nodes are not canonical sectors. jobs root is not in this set.
JOBS_V2_INACTIVE_SECTOR_SLUGS: frozenset[str] = frozenset(
    {
        "jobs-rabota-za-rubezhom",
    }
) | JOBS_V2_RETIRED_LEGACY_SLUGS

JOBS_V2_EXCLUDED_FROM_CREATE_PICKER: frozenset[str] = (
    JOBS_V2_META_SLUGS | JOBS_V2_LEGACY_SLUGS | JOBS_V2_INACTIVE_SECTOR_SLUGS
)


def _choices(*labels: str) -> dict[str, Any]:
    return {"choices": [{"value": label, "label": label} for label in labels]}


def _f(
    key: str,
    label: str,
    ftype: CategoryFieldType,
    *,
    required: bool = True,
    options: dict[str, Any] | None = None,
    hint: str | None = None,
) -> FieldDef:
    return (key, label, ftype, required, options, hint)


def _is_resumes(slug: str) -> bool:
    return slug == "jobs-rezyume-soiskateley"


def fields_for_job_section(section: dict[str, Any]) -> list[FieldDef]:
    """Build hiring create core_fields for one JOB_SECTIONS entry (pilot parity)."""
    slug = section["category_slug"]
    role_label = "Сфера" if _is_resumes(slug) else "Вакансия"
    role_opts = {
        "choices": [
            {"value": r["value"], "label": r["label"]} for r in section["roles"]
        ]
    }
    out: list[FieldDef] = [
        _f("job_role", role_label, _E, options=role_opts),
    ]

    for group in section.get("filters") or []:
        label = group["label"]
        key = _FILTER_LABEL_TO_KEY.get(label)
        if key is None:
            continue  # skip «График»
        if key == "experience":
            out.append(
                _f(
                    "experience",
                    "Опыт",
                    _MS,
                    options=_choices(*_CREATE_EXPERIENCE),
                )
            )
            continue
        opts = {
            "choices": [
                {"value": o["value"], "label": o["label"]}
                for o in group["options"]
            ]
        }
        out.append(_f(key, label, _E, options=opts))

    if not _is_resumes(slug):
        out.extend(
            [
                _f(
                    "work_schedule",
                    "График работы",
                    _E,
                    options=_choices(*_WORK_SCHEDULE),
                ),
                _f(
                    "work_mode",
                    "Режим работы",
                    _E,
                    options=_choices(*_WORK_MODE),
                ),
                _f(
                    "work_hours_from",
                    "Часы работы С",
                    _T,
                    required=False,
                    options=_choices(*_WORK_HOURS),
                ),
                _f(
                    "work_hours_to",
                    "Часы работы До",
                    _T,
                    required=False,
                    options=_choices(*_WORK_HOURS),
                ),
            ]
        )

    out.extend(
        [
            _f(
                "job_conditions",
                "Условия",
                _MS,
                options=_choices(*_CONDITIONS),
            ),
            _f(
                "salary_payout",
                "Выплата зарплаты",
                _E,
                options=_choices(*_SALARY_PAYOUT),
            ),
            _f("price", "Зарплата", _P, hint="Сумма зарплаты"),
            _f(
                "bonuses",
                "Премии и бонусы",
                _E,
                options=_choices(*_BONUSES),
            ),
            _f(
                "contact_methods",
                "Способы связи",
                _E,
                options=_choices(*_CONTACT_METHODS),
            ),
        ]
    )
    return out


def build_jobs_create_core_fields() -> dict[str, list[FieldDef]]:
    """slug → hiring FieldDef list for all JOB_SECTIONS leaves (incl. meta)."""
    result: dict[str, list[FieldDef]] = {}
    for section in JOB_SECTIONS.values():
        slug = section["category_slug"]
        result[slug] = fields_for_job_section(section)
    return result


def build_jobs_hiring_core_fields() -> dict[str, list[FieldDef]]:
    """Jobs V2 hiring SoT for 19 canonical sectors only."""
    all_fields = build_jobs_create_core_fields()
    return {slug: all_fields[slug] for slug in JOBS_V2_CANONICAL_SLUGS}


def expected_job_create_slugs() -> frozenset[str]:
    """All JOB_SECTIONS slugs (pilot + meta) — used by seed/loader."""
    return frozenset(build_jobs_create_core_fields().keys())


def expected_jobs_v2_canonical_slugs() -> frozenset[str]:
    return frozenset(JOBS_V2_CANONICAL_SLUGS)


def is_jobs_v2_sector_slug(slug: str | None) -> bool:
    if not slug:
        return False
    return slug in JOBS_V2_CANONICAL_SLUGS or slug in JOBS_V2_META_SLUGS


def is_jobs_create_intent_required(slug: str | None) -> bool:
    """True when intelligence must be requested with hiring|job_seeking."""
    return bool(slug) and (
        slug in JOBS_V2_CANONICAL_SLUGS or slug in JOBS_V2_META_SLUGS
    )


# Re-export shared option tuples for seeking seed / tests.
CREATE_EXPERIENCE = _CREATE_EXPERIENCE
CONDITIONS = _CONDITIONS
WORK_SCHEDULE = _WORK_SCHEDULE
WORK_MODE = _WORK_MODE
CONTACT_METHODS = _CONTACT_METHODS
HIRING_INTENT = HIRING
