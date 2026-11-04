# -*- coding: utf-8 -*-
"""Create-listing core_fields for L1 «Работа» — job_seeking (candidate) SoT.

Shares canonical job_role option identity with hiring. Labels differ.
Sector-specific extras only where approved. Role-dependent fields use
options.depends_on (generic, backend-driven).
"""
from __future__ import annotations

from typing import Any

from app.models.category_enums import CategoryFieldType
from app.models.job_create_intent import JOB_SEEKING
from app.seeds.home_garden_filters import FieldDef
from app.seeds.jobs_create_fields import (
    CONDITIONS,
    CONTACT_METHODS,
    CREATE_EXPERIENCE,
    JOBS_V2_CANONICAL_SLUGS,
    WORK_SCHEDULE,
    _choices,
    _f,
)
from app.seeds.jobs_sections_catalog import JOB_SECTIONS

_E = CategoryFieldType.enum
_MS = CategoryFieldType.multi_select
_P = CategoryFieldType.price

_EMPLOYMENT = ("Полная", "Частичная", "Подработка", "Вахта")
_READY = ("Сразу", "В течение месяца")

_TRANSPORT_DRIVER_ROLES = (
    "Водитель легкового авто",
    "Водитель такси",
    "Водитель Газели",
    "Водитель грузового авто",
    "Водитель фуры",
    "Водитель автобуса",
    "Водитель микроавтобуса",
)
_TRANSPORT_ROUTE_ROLES = _TRANSPORT_DRIVER_ROLES + (
    "Курьер",
    "Экспедитор",
)
_ENTERTAINMENT_CERT_ROLES = (
    "Тренер",
    "Фитнес-тренер",
    "Персональный тренер",
    "Инструктор",
    "Тренер по танцам",
)
_AGRI_LICENSE_ROLES = (
    "Тракторист",
    "Механизатор",
    "Комбайнёр",
)


def _section_by_slug(slug: str) -> dict[str, Any]:
    for section in JOB_SECTIONS.values():
        if section["category_slug"] == slug:
            return section
    raise KeyError(slug)


def _role_opts(section: dict[str, Any]) -> dict[str, Any]:
    return {
        "choices": [
            {"value": r["value"], "label": r["label"]} for r in section["roles"]
        ]
    }


def _dep_choices(
    *labels: str,
    field: str,
    values: tuple[str, ...],
) -> dict[str, Any]:
    opts = _choices(*labels)
    opts["depends_on"] = {"field": field, "values": list(values)}
    return opts


def _common_prefix(section: dict[str, Any]) -> list[FieldDef]:
    return [
        _f(
            "job_role",
            "Желаемая должность",
            _E,
            options=_role_opts(section),
        ),
        _f("price", "Желаемая зарплата", _P, hint="Желаемая сумма зарплаты"),
        _f("employment", "Занятость", _E, options=_choices(*_EMPLOYMENT)),
        _f(
            "experience",
            "Опыт работы",
            _E,
            options=_choices(*CREATE_EXPERIENCE),
        ),
        _f(
            "work_schedule",
            "Желаемый график работы",
            _E,
            options=_choices(*WORK_SCHEDULE),
        ),
        _f(
            "ready_to_start",
            "Готовность выйти",
            _E,
            options=_choices(*_READY),
        ),
    ]


def _common_suffix() -> list[FieldDef]:
    return [
        _f(
            "job_conditions",
            "Условия",
            _MS,
            options=_choices(*CONDITIONS),
        ),
        _f(
            "contact_methods",
            "Способы связи",
            _E,
            options=_choices(*CONTACT_METHODS),
        ),
    ]


def _sector_extras(slug: str) -> list[FieldDef]:
    if slug == "jobs-shveynoe-proizvodstvo":
        return [
            _f(
                "work_format",
                "Формат работы",
                _E,
                options=_choices("В цехе", "На дому"),
            ),
        ]
    if slug == "jobs-stroitelstvo-i-remont":
        return [
            _f(
                "work_format",
                "Формат работы",
                _E,
                options=_choices(
                    "В бригаде",
                    "Самостоятельно",
                    "Не имеет значения",
                ),
            ),
        ]
    if slug == "jobs-transport-i-logistika":
        return [
            _f(
                "driver_license",
                "Водительские права",
                _MS,
                options=_dep_choices(
                    "A",
                    "B",
                    "C",
                    "D",
                    "BE",
                    "CE",
                    "DE",
                    "Нет",
                    field="job_role",
                    values=_TRANSPORT_DRIVER_ROLES,
                ),
            ),
            _f(
                "personal_car",
                "Личный автомобиль",
                _E,
                options=_dep_choices(
                    "Есть",
                    "Нет",
                    field="job_role",
                    values=_TRANSPORT_DRIVER_ROLES,
                ),
            ),
            _f(
                "route",
                "Маршрут",
                _E,
                options=_dep_choices(
                    "По городу",
                    "Межгород",
                    "Вахта",
                    field="job_role",
                    values=_TRANSPORT_ROUTE_ROLES,
                ),
            ),
        ]
    if slug in {
        "jobs-ofis-i-administratsiya",
        "jobs-buhgalteriya-i-finansy",
        "jobs-marketing-reklama-i-media",
        "jobs-it-i-tehnologii",
    }:
        return [
            _f(
                "work_format",
                "Формат работы",
                _E,
                options=_choices("В офисе", "Удалённо", "Гибрид"),
            ),
        ]
    if slug == "jobs-obrazovanie-i-obuchenie":
        return [
            _f(
                "education_level",
                "Образование",
                _E,
                options=_choices(
                    "Среднее специальное",
                    "Высшее",
                    "Неоконченное высшее",
                ),
            ),
            _f(
                "work_format",
                "Формат работы",
                _E,
                options=_choices("Очно", "Онлайн", "Не имеет значения"),
            ),
        ]
    if slug == "jobs-meditsina-i-farmatsevtika":
        return [
            _f(
                "medical_education",
                "Медицинское образование",
                _E,
                options=_choices("Среднее специальное", "Высшее"),
            ),
            _f(
                "certificate",
                "Сертификат",
                _E,
                options=_choices("Есть", "Нет"),
            ),
        ]
    if slug == "jobs-krasota-i-zdorove":
        return [
            _f(
                "work_format",
                "Формат работы",
                _E,
                options=_choices(
                    "В салоне",
                    "В частном кабинете",
                    "Выезд",
                ),
            ),
            _f(
                "certificate",
                "Сертификат / обучение",
                _E,
                options=_choices("Есть", "Нет"),
            ),
        ]
    if slug == "jobs-razvlecheniya-i-sport":
        return [
            _f(
                "certificate",
                "Сертификат / квалификация",
                _E,
                options=_dep_choices(
                    "Есть",
                    "Нет",
                    field="job_role",
                    values=_ENTERTAINMENT_CERT_ROLES,
                ),
            ),
        ]
    if slug == "jobs-domashniy-personal":
        return [
            _f(
                "housing",
                "Проживание",
                _E,
                options=_choices("С проживанием", "Без проживания"),
            ),
        ]
    if slug == "jobs-ohrana-i-bezopasnost":
        return [
            _f(
                "object_type",
                "Объект",
                _E,
                options=_choices(
                    "Офис",
                    "Магазин",
                    "Стройка",
                    "Жилой комплекс",
                    "Другой",
                ),
            ),
        ]
    if slug == "jobs-selskoe-hozyaystvo":
        return [
            _f(
                "housing",
                "Проживание",
                _E,
                options=_choices("Нужно", "Не нужно"),
            ),
            _f(
                "driver_license",
                "Водительские права",
                _MS,
                options=_dep_choices(
                    "A",
                    "B",
                    "C",
                    "D",
                    "BE",
                    "CE",
                    "DE",
                    "Нет",
                    field="job_role",
                    values=_AGRI_LICENSE_ROLES,
                ),
            ),
        ]
    if slug == "jobs-studenty-i-podrabotka":
        return [
            _f(
                "when_available",
                "Когда могу работать",
                _E,
                options=_choices(
                    "Вечером",
                    "В выходные",
                    "Несколько часов",
                    "По договорённости",
                ),
            ),
        ]
    # Abroad sector is inactive in Jobs V2; foreign work uses geo country picker.
    return []


def fields_for_job_seeking(slug: str) -> list[FieldDef]:
    section = _section_by_slug(slug)
    out = _common_prefix(section)
    out.extend(_sector_extras(slug))
    out.extend(_common_suffix())
    return out


def build_jobs_seeking_core_fields() -> dict[str, list[FieldDef]]:
    """slug → job_seeking FieldDef for 20 canonical sectors."""
    return {slug: fields_for_job_seeking(slug) for slug in JOBS_V2_CANONICAL_SLUGS}


JOB_SEEKING_INTENT = JOB_SEEKING
