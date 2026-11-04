"""Jobs V2: hiring | job_seeking create intelligence + parity."""
from __future__ import annotations

import pytest

from app.models.job_create_intent import HIRING, JOB_SEEKING
from app.seeds.jobs_create_fields import (
    JOBS_V2_CANONICAL_SLUGS,
    JOBS_V2_EXCLUDED_FROM_CREATE_PICKER,
    JOBS_V2_INACTIVE_SECTOR_SLUGS,
    build_jobs_create_core_fields,
    build_jobs_hiring_core_fields,
)
from app.seeds.jobs_seeking_fields import build_jobs_seeking_core_fields
from app.seeds.jobs_sections_catalog import JOB_SECTIONS


def test_canonical_sectors_are_exactly_19() -> None:
    assert len(JOBS_V2_CANONICAL_SLUGS) == 19
    assert len(set(JOBS_V2_CANONICAL_SLUGS)) == 19
    assert "jobs-rabota-za-rubezhom" not in JOBS_V2_CANONICAL_SLUGS
    assert "jobs-rabota-za-rubezhom" in JOBS_V2_INACTIVE_SECTOR_SLUGS
    for slug in (
        "jobs-vacancies",
        "jobs-resume",
        "jobs-vakansii-bez-opyta",
        "jobs-rezyume-soiskateley",
        "jobs-rabota-za-rubezhom",
    ):
        assert slug in JOBS_V2_EXCLUDED_FROM_CREATE_PICKER
        assert slug not in JOBS_V2_CANONICAL_SLUGS


def test_hiring_parity_vs_pilot_for_19_sectors() -> None:
    pilot = build_jobs_create_core_fields()
    hiring = build_jobs_hiring_core_fields()
    assert set(hiring.keys()) == set(JOBS_V2_CANONICAL_SLUGS)
    for slug in JOBS_V2_CANONICAL_SLUGS:
        assert hiring[slug] == pilot[slug], slug


def test_job_seeking_common_frame_and_no_employer_fields() -> None:
    seeking = build_jobs_seeking_core_fields()
    assert set(seeking.keys()) == set(JOBS_V2_CANONICAL_SLUGS)
    forbidden = {
        "employer",
        "pay_type",
        "salary_payout",
        "bonuses",
        "work_mode",
        "work_hours_from",
        "work_hours_to",
        "formalization",
    }
    required_common = [
        "job_role",
        "price",
        "employment",
        "experience",
        "work_schedule",
        "ready_to_start",
        "job_conditions",
        "contact_methods",
    ]
    for slug, fields in seeking.items():
        keys = [f[0] for f in fields]
        for k in required_common:
            assert k in keys, f"{slug} missing {k}"
        for k in forbidden:
            assert k not in keys, f"{slug} has employer-side {k}"
        assert fields[0][1] == "Желаемая должность"
        price = next(f for f in fields if f[0] == "price")
        assert price[1] == "Желаемая зарплата"
        cond = next(f for f in fields if f[0] == "job_conditions")
        assert cond[2].value == "multi_select"


def test_job_seeking_sector_extras() -> None:
    seeking = build_jobs_seeking_core_fields()

    def keys(slug: str) -> list[str]:
        return [f[0] for f in seeking[slug]]

    assert "work_format" in keys("jobs-shveynoe-proizvodstvo")
    assert "work_format" in keys("jobs-stroitelstvo-i-remont")
    assert "driver_license" in keys("jobs-transport-i-logistika")
    assert "personal_car" in keys("jobs-transport-i-logistika")
    assert "route" in keys("jobs-transport-i-logistika")
    assert "work_format" in keys("jobs-it-i-tehnologii")
    assert "medical_education" in keys("jobs-meditsina-i-farmatsevtika")
    assert "housing" in keys("jobs-domashniy-personal")
    assert "when_available" in keys("jobs-studenty-i-podrabotka")
    assert "jobs-rabota-za-rubezhom" not in seeking
    # production / sales / hospitality / sto — no extras
    for slug in (
        "jobs-proizvodstvo-i-promyshlennost",
        "jobs-prodazhi-i-torgovlya",
        "jobs-gostinitsy-kafe-i-restorany",
        "jobs-sto-i-avtoservis",
    ):
        extras = set(keys(slug)) - {
            "job_role",
            "price",
            "employment",
            "experience",
            "work_schedule",
            "ready_to_start",
            "job_conditions",
            "contact_methods",
        }
        assert extras == set(), slug


def test_transport_driver_fields_have_depends_on() -> None:
    transport = build_jobs_seeking_core_fields()["jobs-transport-i-logistika"]
    lic = next(f for f in transport if f[0] == "driver_license")
    assert lic[2].value == "multi_select"
    dep = lic[4]["depends_on"]
    assert dep["field"] == "job_role"
    assert "Водитель легкового авто" in dep["values"]


@pytest.mark.asyncio
async def test_intelligence_intent_required_and_schemas(client) -> None:
    from app.db.session import engine

    await engine.dispose()
    tree = (await client.get("/api/v1/categories/tree")).json()

    def walk(nodes, out):
        for n in nodes:
            out.append(n)
            walk(n.get("children") or [], out)

    flat: list[dict] = []
    walk(tree, flat)
    by_slug = {n["slug"]: n for n in flat}

    # Soft-deactivated meta/legacy/abroad must not appear as active tree leaves.
    for slug in JOBS_V2_EXCLUDED_FROM_CREATE_PICKER:
        node = by_slug.get(slug)
        if node is not None:
            assert False, f"excluded slug still in tree: {slug}"

    hiring_expected = build_jobs_hiring_core_fields()
    seeking_expected = build_jobs_seeking_core_fields()

    for slug in JOBS_V2_CANONICAL_SLUGS:
        node = by_slug.get(slug)
        assert node is not None, slug
        cat_id = node["id"]

        missing = await client.get(f"/api/v1/categories/intelligence/{cat_id}")
        assert missing.status_code == 400, slug

        bad = await client.get(
            f"/api/v1/categories/intelligence/{cat_id}",
            params={"intent": "Ищу работу"},
        )
        assert bad.status_code == 400, slug

        hire = await client.get(
            f"/api/v1/categories/intelligence/{cat_id}",
            params={"intent": HIRING},
        )
        assert hire.status_code == 200, slug
        hire_data = hire.json()
        assert hire_data["create_intent"] == HIRING
        hire_keys = [f["field_key"] for f in sorted(
            hire_data["core_fields"],
            key=lambda f: (f.get("sort_order", 0), f["field_key"]),
        )]
        assert hire_keys == [f[0] for f in hiring_expected[slug]], slug
        assert "employer" in hire_keys

        seek = await client.get(
            f"/api/v1/categories/intelligence/{cat_id}",
            params={"intent": JOB_SEEKING},
        )
        assert seek.status_code == 200, slug
        seek_data = seek.json()
        assert seek_data["create_intent"] == JOB_SEEKING
        seek_keys = [f["field_key"] for f in sorted(
            seek_data["core_fields"],
            key=lambda f: (f.get("sort_order", 0), f["field_key"]),
        )]
        assert seek_keys == [f[0] for f in seeking_expected[slug]], slug
        assert "employer" not in seek_keys
        assert "bonuses" not in seek_keys
        assert "salary_payout" not in seek_keys


def test_non_jobs_slug_does_not_require_intent() -> None:
    from app.seeds.jobs_create_fields import is_jobs_create_intent_required

    assert is_jobs_create_intent_required("jobs-it-i-tehnologii") is True
    assert is_jobs_create_intent_required("transport-car-sale") is False
    assert is_jobs_create_intent_required("home-garden") is False
    assert is_jobs_create_intent_required(None) is False


def test_listing_create_schema_accepts_job_intent() -> None:
    from decimal import Decimal

    from app.schemas.listing import ListingCreate

    ok = ListingCreate(
        title="Seeking IT",
        price=Decimal("1000"),
        category_id=881,
        job_intent=JOB_SEEKING,
        fields={"job_role": "Программист"},
    )
    assert ok.job_intent == JOB_SEEKING

    with pytest.raises(Exception):
        ListingCreate(
            title="Bad",
            price=Decimal("1"),
            category_id=881,
            job_intent="Ищу работу",
        )


def test_roles_shared_between_intents() -> None:
    hiring = build_jobs_hiring_core_fields()["jobs-it-i-tehnologii"]
    seeking = build_jobs_seeking_core_fields()["jobs-it-i-tehnologii"]
    h_roles = next(f for f in hiring if f[0] == "job_role")[4]["choices"]
    s_roles = next(f for f in seeking if f[0] == "job_role")[4]["choices"]
    assert [c["value"] for c in h_roles] == [c["value"] for c in s_roles]
    assert next(f for f in hiring if f[0] == "job_role")[1] == "Вакансия"
    assert next(f for f in seeking if f[0] == "job_role")[1] == "Желаемая должность"


def test_job_sections_catalog_still_has_meta_for_browse() -> None:
    slugs = {s["category_slug"] for s in JOB_SECTIONS.values()}
    assert "jobs-vakansii-bez-opyta" in slugs
    assert "jobs-rezyume-soiskateley" in slugs
    assert "jobs-rabota-za-rubezhom" in slugs  # historical row catalog kept
