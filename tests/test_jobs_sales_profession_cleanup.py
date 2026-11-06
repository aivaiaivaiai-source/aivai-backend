"""Approved sales-profession cleanup. Stable values stay the Russian labels."""
from __future__ import annotations

from app.seeds.jobs_create_fields import (
    JOBS_V2_CANONICAL_SLUGS,
    build_jobs_hiring_core_fields,
)
from app.seeds.jobs_sections_catalog import JOB_SECTIONS, build_job_section_catalog
from app.seeds.jobs_seeking_fields import build_jobs_seeking_core_fields

_SALES = "jobs-prodazhi-i-torgovlya"
_STAFF = "jobs-domashniy-personal"
_REMOVED = ("Продавец", "Продавец-кассир", "Торговый агент")
_KEPT_SALES = ("Продавец-консультант", "Кассир", "Торговый представитель")
_KEPT_STAFF = ("Домработница", "Помощник по хозяйству")


def _roles(slug: str) -> list[str]:
    for section in JOB_SECTIONS.values():
        if section["category_slug"] == slug:
            return [role["value"] for role in section["roles"]]
    raise KeyError(slug)


def _job_role_choices(fields) -> list[str]:
    for field in fields:
        if field[0] == "job_role":
            return [choice["value"] for choice in field[4]["choices"]]
    raise AssertionError("job_role missing")


def test_removed_sales_professions_absent() -> None:
    roles = _roles(_SALES)
    assert set(_REMOVED).isdisjoint(roles)


def test_kept_sales_and_housekeeper_roles_present() -> None:
    roles = _roles(_SALES)
    for label in _KEPT_SALES:
        assert label in roles
    staff = _roles(_STAFF)
    for label in _KEPT_STAFF:
        assert label in staff


def test_catalog_size_245_across_19_sectors() -> None:
    assert len(JOBS_V2_CANONICAL_SLUGS) == 19
    assert "jobs-rabota-za-rubezhom" not in JOBS_V2_CANONICAL_SLUGS
    total = sum(len(_roles(slug)) for slug in JOBS_V2_CANONICAL_SLUGS)
    assert total == 245
    fallbacks = [
        role
        for slug in JOBS_V2_CANONICAL_SLUGS
        for role in _roles(slug)
        if role.startswith("Другие")
    ]
    assert len(fallbacks) == 19


def test_create_search_parity_both_intents() -> None:
    hiring = _job_role_choices(build_jobs_hiring_core_fields()[_SALES])
    seeking = _job_role_choices(build_jobs_seeking_core_fields()[_SALES])
    search = [
        role["value"] for role in build_job_section_catalog("sales")["roles"]
    ]
    assert hiring == seeking == search == _roles(_SALES)
    assert set(_REMOVED).isdisjoint(hiring)


def test_seed_builders_twice_do_not_restore_or_duplicate() -> None:
    first_hiring = _job_role_choices(build_jobs_hiring_core_fields()[_SALES])
    second_hiring = _job_role_choices(build_jobs_hiring_core_fields()[_SALES])
    first_seeking = _job_role_choices(build_jobs_seeking_core_fields()[_SALES])
    second_seeking = _job_role_choices(build_jobs_seeking_core_fields()[_SALES])
    assert first_hiring == second_hiring == first_seeking == second_seeking
    assert len(first_hiring) == len(set(first_hiring))
    assert set(_REMOVED).isdisjoint(first_hiring)
