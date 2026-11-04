"""Jobs create-listing intelligence pilot — Backend SoT for sector leaves."""
from __future__ import annotations

import pytest

from app.seeds.jobs_create_fields import (
    build_jobs_create_core_fields,
    expected_job_create_slugs,
)
from app.seeds.jobs_sections_catalog import JOB_SECTIONS


def test_jobs_create_covers_all_job_sections() -> None:
    built = build_jobs_create_core_fields()
    assert len(built) == 22
    assert expected_job_create_slugs() == frozenset(
        s["category_slug"] for s in JOB_SECTIONS.values()
    )
    for section in JOB_SECTIONS.values():
        slug = section["category_slug"]
        fields = built[slug]
        keys = [f[0] for f in fields]
        assert "job_role" in keys
        assert "job_conditions" in keys
        assert "salary_payout" in keys
        assert "price" in keys
        assert "bonuses" in keys
        assert "contact_methods" in keys
        assert "city" not in keys
        # multi_select conditions
        cond = next(f for f in fields if f[0] == "job_conditions")
        assert cond[2].value == "multi_select"
        assert cond[4] and cond[4]["choices"]
        if slug == "jobs-rezyume-soiskateley":
            assert "work_schedule" not in keys
            assert "work_mode" not in keys
            assert "work_hours_from" not in keys
            assert fields[0][1] == "Сфера"
        else:
            assert "work_schedule" in keys
            assert "work_mode" in keys
            assert "work_hours_from" in keys
            hours = next(f for f in fields if f[0] == "work_hours_from")
            assert hours[2].value == "time"
            assert hours[3] is False  # optional
            assert fields[0][1] == "Вакансия"


def test_jobs_create_experience_uses_flutter_ladder_not_browse() -> None:
    sewing = build_jobs_create_core_fields()["jobs-shveynoe-proizvodstvo"]
    exp = next(f for f in sewing if f[0] == "experience")
    labels = [c["label"] for c in exp[4]["choices"]]
    assert "До 1 года" in labels
    assert "1–2 года" in labels
    assert "До 3 лет" not in labels


def test_jobs_create_skips_browse_schedule_filter() -> None:
    sewing = build_jobs_create_core_fields()["jobs-shveynoe-proizvodstvo"]
    keys = [f[0] for f in sewing]
    # Browse «График» must not become a create field_key.
    assert "schedule" not in keys
    assert keys.count("work_schedule") == 1


@pytest.mark.asyncio
async def test_all_job_sector_leaves_have_intelligence(client) -> None:
    """Runtime: every JOB_SECTIONS leaf returns non-empty create core_fields."""
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
    expected = build_jobs_create_core_fields()
    from app.models.job_create_intent import HIRING
    from app.seeds.jobs_create_fields import JOBS_V2_CANONICAL_SLUGS

    rows = []
    for slug in JOBS_V2_CANONICAL_SLUGS:
        node = by_slug.get(slug)
        assert node is not None, slug
        rows.append((node["id"], slug))
    assert len(rows) == 19

    for cat_id, slug in rows:
        resp = await client.get(
            f"/api/v1/categories/intelligence/{cat_id}",
            params={"intent": HIRING},
        )
        assert resp.status_code == 200, slug
        data = resp.json()
        core = sorted(
            data["core_fields"],
            key=lambda f: (f.get("sort_order", 0), f["field_key"]),
        )
        assert core, f"empty core_fields for {slug}"
        keys = [f["field_key"] for f in core]
        assert keys == [f[0] for f in expected[slug]], slug
        for field in core:
            if field["field_type"] in {"enum", "multi_select", "time"}:
                opts = field.get("options") or {}
                choices = opts.get("choices") or opts.get("values") or []
                assert choices, f"{slug}.{field['field_key']} missing options"
            if field["field_key"] == "job_conditions":
                assert field["field_type"] == "multi_select"
            if field["field_key"] == "work_hours_from":
                assert field["field_type"] == "time"
                assert field["is_required"] is False
            assert field["field_key"] != "city"


def test_legacy_job_slugs_excluded_from_create_seed() -> None:
    """Create seed must not redefine legacy jobs-vacancies / jobs-resume."""
    slugs = expected_job_create_slugs()
    assert "jobs-vacancies" not in slugs
    assert "jobs-resume" not in slugs
    assert len(slugs) == 22
