# -*- coding: utf-8 -*-
"""Jobs Search V2 — filter schema + job_intent feed filtering."""
from __future__ import annotations

import json
from decimal import Decimal

import pytest
from sqlalchemy import select, text

from app.db.session import async_session_maker, engine
from app.models.category import Category
from app.models.enums import Currency, ListingStatus
from app.models.job_create_intent import HIRING, JOB_SEEKING
from app.models.listing import Listing
from app.models.listing_field_value import ListingFieldValue
from app.models.user import User
from app.seeds.jobs_create_fields import (
    CONDITIONS,
    CREATE_EXPERIENCE,
    JOBS_V2_CANONICAL_SLUGS,
    WORK_SCHEDULE,
    _FILTER_LABEL_TO_KEY,
)
from app.seeds.jobs_search_filters import (
    build_jobs_search_filters,
    hiring_filters_for_section,
)
from app.seeds.jobs_sections_catalog import JOB_SECTIONS

_HIRING_LABEL_TO_KEY = {**_FILTER_LABEL_TO_KEY, "График": "work_schedule"}


def test_search_filter_builder_covers_19_sectors() -> None:
    built = build_jobs_search_filters()
    assert set(built.keys()) == set(JOBS_V2_CANONICAL_SLUGS)
    for slug, intents in built.items():
        assert set(intents.keys()) == {HIRING, JOB_SEEKING}
        assert intents[HIRING]
        assert intents[JOB_SEEKING]
        seeking_keys = {f[0] for f in intents[JOB_SEEKING]}
        hiring_keys = {f[0] for f in intents[HIRING]}
        assert "employment" in seeking_keys
        assert "employer" not in seeking_keys
        # UX: no salary filters in Jobs Search V2
        assert "price" not in hiring_keys
        assert "price" not in seeking_keys


def test_hiring_search_keys_include_section_plus_create_parity() -> None:
    """Section groups + always work_schedule + work_mode + job_conditions; no salary."""
    from app.seeds.jobs_create_fields import (
        CREATE_EXPERIENCE,
        CONDITIONS,
        WORK_MODE,
        WORK_SCHEDULE,
    )

    for section in JOB_SECTIONS.values():
        slug = section["category_slug"]
        if slug not in JOBS_V2_CANONICAL_SLUGS:
            continue
        old_labels = [g["label"] for g in section.get("filters") or []]
        expected_keys = [
            _HIRING_LABEL_TO_KEY[lab]
            for lab in old_labels
            if lab in _HIRING_LABEL_TO_KEY
        ]
        if "work_schedule" not in expected_keys:
            expected_keys.append("work_schedule")
        if "work_mode" not in expected_keys:
            expected_keys.append("work_mode")
        if "job_conditions" not in expected_keys:
            expected_keys.append("job_conditions")
        new = hiring_filters_for_section(section)
        assert [f[0] for f in new] == expected_keys, slug
        by_key = {f[0]: f for f in new}
        if "experience" in by_key:
            opts = [o["value"] for o in (by_key["experience"][4] or {}).get("options") or []]
            assert opts == list(CREATE_EXPERIENCE), slug
        sched = [o["value"] for o in (by_key["work_schedule"][4] or {}).get("options") or []]
        assert sched == list(WORK_SCHEDULE), slug
        mode = [o["value"] for o in (by_key["work_mode"][4] or {}).get("options") or []]
        assert mode == list(WORK_MODE), slug
        cond = [o["value"] for o in (by_key["job_conditions"][4] or {}).get("options") or []]
        assert cond == list(CONDITIONS), slug
        assert all(f[0] != "price" for f in new)


def test_it_hiring_and_seeking_ux_labels() -> None:
    built = build_jobs_search_filters()["jobs-it-i-tehnologii"]
    hiring = {f[0]: f[1] for f in built[HIRING]}
    seeking = {f[0]: f[1] for f in built[JOB_SEEKING]}
    assert hiring == {
        "employer": "Работодатель",
        "work_format": "Формат работы",
        "work_schedule": "График работы",
        "experience": "Требуемый опыт",
        "pay_type": "Тип оплаты",
        "work_mode": "Режим работы",
        "job_conditions": "Условия",
    }
    assert "price" not in hiring
    assert "price" not in seeking
    assert seeking["employment"] == "Занятость"
    assert seeking["experience"] == "Опыт работы"
    assert seeking["work_schedule"] == "Желаемый график работы"
    assert seeking["ready_to_start"] == "Готовность выйти"
    assert seeking["job_conditions"] == "Условия"
    assert seeking["work_format"] == "Формат работы"
    assert "employer" not in seeking
    assert "pay_type" not in seeking


def test_all_option_jobs_search_filters_are_multi_select() -> None:
    """Hiring + seeking option filters use multi_select (Условия pattern)."""
    from app.models.category_enums import CategoryFilterType

    built = build_jobs_search_filters()
    for slug, intents in built.items():
        for intent, filters in intents.items():
            for key, _label, ftype, _sort, config in filters:
                assert ftype == CategoryFilterType.multi_select, (
                    f"{slug}/{intent}/{key} expected multi_select, got {ftype}"
                )
                opts = (config or {}).get("options") or []
                assert opts, f"{slug}/{intent}/{key} missing options"


def test_hiring_create_search_option_parity_all_sectors() -> None:
    """Hiring search experience/schedule/conditions match Jobs V2 create."""
    from app.seeds.jobs_create_fields import build_jobs_hiring_core_fields

    create_by_slug = build_jobs_hiring_core_fields()
    search_by_slug = build_jobs_search_filters()

    def create_opts(slug: str, key: str) -> list[str] | None:
        for field in create_by_slug[slug]:
            if field[0] != key:
                continue
            choices = (field[4] or {}).get("choices") or []
            return [c["value"] if isinstance(c, dict) else str(c) for c in choices]
        return None

    def search_opts(slug: str, key: str) -> list[str] | None:
        for f in search_by_slug[slug][HIRING]:
            if f[0] != key:
                continue
            return [o["value"] for o in (f[4] or {}).get("options") or []]
        return None

    from app.seeds.jobs_create_fields import WORK_MODE

    for slug in JOBS_V2_CANONICAL_SLUGS:
        for key, expected in (
            ("experience", list(CREATE_EXPERIENCE)),
            ("work_schedule", list(WORK_SCHEDULE)),
            ("work_mode", list(WORK_MODE)),
            ("job_conditions", list(CONDITIONS)),
        ):
            c_opts = create_opts(slug, key)
            s_opts = search_opts(slug, key)
            if c_opts is None:
                # NOT APPLICABLE — search must not invent the filter either.
                assert s_opts is None, f"{slug} search has {key} without create"
                continue
            assert s_opts == c_opts == expected, f"{slug}/{key} parity"


@pytest.mark.asyncio
async def test_db_has_intent_scoped_filters_for_19_sectors(client) -> None:
    await engine.dispose()
    tree = (await client.get("/api/v1/categories/tree")).json()

    def walk(nodes, out):
        for n in nodes:
            out.append(n)
            walk(n.get("children") or [], out)

    flat: list[dict] = []
    walk(tree, flat)
    by_slug = {n["slug"]: n for n in flat}
    for slug in JOBS_V2_CANONICAL_SLUGS:
        node = by_slug[slug]
        for intent in (HIRING, JOB_SEEKING):
            resp = await client.get(
                f"/api/v1/categories/intelligence/{node['id']}",
                params={"intent": intent},
            )
            assert resp.status_code == 200, slug
            filters = resp.json()["filters"]
            assert filters, f"{slug}/{intent} empty filters"
            keys = [f["filter_key"] for f in filters]
            assert "price" not in keys, f"{slug}/{intent} still has salary filter"
            for f in filters:
                assert f["filter_type"] == "multi_select", (
                    f"{slug}/{intent}/{f['filter_key']} not multi_select"
                )
            for k in keys:
                assert " " not in k
                assert k.isascii()


@pytest.mark.asyncio
async def test_job_intent_invalid(client) -> None:
    r = await client.get("/api/v1/listings", params={"job_intent": "Ищу работу"})
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_feed_job_intent_and_role_and_null_policy(client) -> None:
    # Dispose pooled connections from prior event loops (Windows/asyncpg flake).
    await engine.dispose()

    cat_id = 0
    ids: list[int] = []
    async with async_session_maker() as session:
        it = (
            await session.execute(
                select(Category).where(Category.slug == "jobs-it-i-tehnologii")
            )
        ).scalar_one()
        cat_id = it.id
        user = (
            await session.execute(select(User).order_by(User.id).limit(1))
        ).scalar_one()

        async def add(
            *,
            title: str,
            intent: str | None,
            status: ListingStatus = ListingStatus.active,
            fields: dict[str, str] | None = None,
            price: Decimal = Decimal("5000"),
        ) -> int:
            row = Listing(
                title=title,
                description="jobs-search-v2-test",
                price=price,
                currency=Currency.KGS,
                status=status,
                owner_id=user.id,
                category_id=cat_id,
                job_intent=intent,
            )
            session.add(row)
            await session.flush()
            for k, v in (fields or {}).items():
                session.add(
                    ListingFieldValue(
                        listing_id=row.id,
                        field_key=k,
                        value_text=v,
                    )
                )
            await session.flush()
            return row.id

        ids.append(
            await add(
                title="JSV2 hiring",
                intent=HIRING,
                fields={"job_role": "Программист", "employer": "Компания"},
            )
        )
        ids.append(
            await add(
                title="JSV2 seeking",
                intent=JOB_SEEKING,
                fields={"job_role": "Программист", "employment": "Полная"},
            )
        )
        ids.append(
            await add(
                title="JSV2 null",
                intent=None,
                fields={"job_role": "Программист"},
            )
        )
        ids.append(
            await add(
                title="JSV2 draft",
                intent=HIRING,
                status=ListingStatus.draft,
                fields={"job_role": "Программист"},
            )
        )
        ids.append(
            await add(
                title="JSV2 qa",
                intent=HIRING,
                fields={"job_role": "Тестировщик"},
            )
        )
        await session.commit()

    try:
        r = await client.get(
            "/api/v1/listings",
            params={"category_id": cat_id, "job_intent": HIRING, "limit": 100},
        )
        assert r.status_code == 200
        titles = {i["title"] for i in r.json()["items"]}
        assert "JSV2 hiring" in titles
        assert "JSV2 qa" in titles
        assert "JSV2 seeking" not in titles
        assert "JSV2 null" not in titles
        assert "JSV2 draft" not in titles

        r2 = await client.get(
            "/api/v1/listings",
            params={
                "category_id": cat_id,
                "job_intent": HIRING,
                "attrs": json.dumps({"job_role": "Программист"}),
                "limit": 100,
            },
        )
        titles2 = {i["title"] for i in r2.json()["items"]}
        assert "JSV2 hiring" in titles2
        assert "JSV2 qa" not in titles2

        # count/total parity
        c = await client.get(
            "/api/v1/listings",
            params={
                "category_id": cat_id,
                "job_intent": HIRING,
                "attrs": json.dumps({"job_role": "Программист"}),
                "limit": 1,
            },
        )
        f = await client.get(
            "/api/v1/listings",
            params={
                "category_id": cat_id,
                "job_intent": HIRING,
                "attrs": json.dumps({"job_role": "Программист"}),
                "limit": 40,
            },
        )
        assert c.json()["total"] == f.json()["total"]

        ms = await client.get(
            "/api/v1/listings",
            params={
                "category_id": cat_id,
                "job_intent": JOB_SEEKING,
                "attrs": json.dumps(
                    {"job_conditions": "Обучение||Карьерный рост"},
                    ensure_ascii=False,
                ),
                "limit": 50,
            },
        )
        assert ms.status_code == 200

        # ANY/OR within one filter: schedule A||B matches either listing.
        async with async_session_maker() as session:
            user = (
                await session.execute(select(User).order_by(User.id).limit(1))
            ).scalar_one()

            async def add_sched(title: str, schedule: str) -> int:
                row = Listing(
                    title=title,
                    description="jobs-search-v2-or",
                    price=Decimal("1000"),
                    currency=Currency.KGS,
                    status=ListingStatus.active,
                    owner_id=user.id,
                    category_id=cat_id,
                    job_intent=HIRING,
                )
                session.add(row)
                await session.flush()
                session.add(
                    ListingFieldValue(
                        listing_id=row.id,
                        field_key="work_schedule",
                        value_text=schedule,
                    )
                )
                await session.flush()
                return row.id

            sid_full = await add_sched("JSV2 full day", "Полный день")
            sid_shift = await add_sched("JSV2 shift", "Сменный график")
            ids.extend([sid_full, sid_shift])
            await session.commit()

        or_resp = await client.get(
            "/api/v1/listings",
            params={
                "category_id": cat_id,
                "job_intent": HIRING,
                "attrs": json.dumps(
                    {"work_schedule": "Полный день||Сменный график"},
                    ensure_ascii=False,
                ),
                "limit": 100,
            },
        )
        assert or_resp.status_code == 200
        or_titles = {i["title"] for i in or_resp.json()["items"]}
        assert "JSV2 full day" in or_titles
        assert "JSV2 shift" in or_titles
    finally:
        async with async_session_maker() as session:
            for lid in ids:
                await session.execute(
                    text("DELETE FROM listing_field_values WHERE listing_id = :id"),
                    {"id": lid},
                )
                await session.execute(
                    text("DELETE FROM listings WHERE id = :id"),
                    {"id": lid},
                )
            await session.commit()


@pytest.mark.asyncio
async def test_jobs_catalog_route_live(client) -> None:
    r = await client.get("/api/v1/categories/jobs/section/it")
    assert r.status_code == 200
    data = r.json()
    assert data["category_slug"] == "jobs-it-i-tehnologii"
    assert data["roles"]


@pytest.mark.asyncio
async def test_hiring_create_search_findability_experience_schedule_conditions(
    client,
) -> None:
    """Create→search with Jobs V2 create vocabulary (not legacy ladders)."""
    await engine.dispose()
    cat_id = 0
    ids: list[int] = []
    async with async_session_maker() as session:
        it = (
            await session.execute(
                select(Category).where(Category.slug == "jobs-it-i-tehnologii")
            )
        ).scalar_one()
        cat_id = it.id
        user = (
            await session.execute(select(User).order_by(User.id).limit(1))
        ).scalar_one()

        row = Listing(
            title="ALIGN hire IT",
            description="create-search-align",
            price=Decimal("7000"),
            currency=Currency.KGS,
            status=ListingStatus.active,
            owner_id=user.id,
            category_id=cat_id,
            job_intent=HIRING,
        )
        session.add(row)
        await session.flush()
        for k, v in {
            "job_role": "Программист",
            "experience": "До 1 года",
            "work_schedule": "Сменный график",
            "job_conditions": "Обучение||Развоз",
        }.items():
            session.add(
                ListingFieldValue(listing_id=row.id, field_key=k, value_text=v)
            )
        ids.append(row.id)

        seek = Listing(
            title="ALIGN seek IT",
            description="create-search-align",
            price=Decimal("5000"),
            currency=Currency.KGS,
            status=ListingStatus.active,
            owner_id=user.id,
            category_id=cat_id,
            job_intent=JOB_SEEKING,
        )
        session.add(seek)
        await session.flush()
        session.add(
            ListingFieldValue(
                listing_id=seek.id, field_key="job_role", value_text="Программист"
            )
        )
        ids.append(seek.id)
        await session.commit()

    try:
        async def titles(**params):
            r = await client.get("/api/v1/listings", params={**params, "limit": 100})
            assert r.status_code == 200
            return {i["title"] for i in r.json()["items"]}

        # Experience FOUND / NOT FOUND
        t = await titles(
            category_id=cat_id,
            job_intent=HIRING,
            attrs=json.dumps({"experience": "До 1 года"}, ensure_ascii=False),
        )
        assert "ALIGN hire IT" in t
        t = await titles(
            category_id=cat_id,
            job_intent=HIRING,
            attrs=json.dumps({"experience": "Более 6 лет"}, ensure_ascii=False),
        )
        assert "ALIGN hire IT" not in t

        # Schedule FOUND / NOT FOUND
        t = await titles(
            category_id=cat_id,
            job_intent=HIRING,
            attrs=json.dumps(
                {"work_schedule": "Сменный график"}, ensure_ascii=False
            ),
        )
        assert "ALIGN hire IT" in t
        t = await titles(
            category_id=cat_id,
            job_intent=HIRING,
            attrs=json.dumps({"work_schedule": "Полный день"}, ensure_ascii=False),
        )
        assert "ALIGN hire IT" not in t

        # Conditions single + multi ANY
        t = await titles(
            category_id=cat_id,
            job_intent=HIRING,
            attrs=json.dumps({"job_conditions": "Обучение"}, ensure_ascii=False),
        )
        assert "ALIGN hire IT" in t
        t = await titles(
            category_id=cat_id,
            job_intent=HIRING,
            attrs=json.dumps({"job_conditions": "Развоз"}, ensure_ascii=False),
        )
        assert "ALIGN hire IT" in t
        t = await titles(
            category_id=cat_id,
            job_intent=HIRING,
            attrs=json.dumps(
                {"job_conditions": "Обучение||Бесплатное питание"},
                ensure_ascii=False,
            ),
        )
        assert "ALIGN hire IT" in t  # ANY: Обучение matches

        # Cross-intent isolation
        t = await titles(category_id=cat_id, job_intent=HIRING)
        assert "ALIGN hire IT" in t and "ALIGN seek IT" not in t
        t = await titles(category_id=cat_id, job_intent=JOB_SEEKING)
        assert "ALIGN seek IT" in t and "ALIGN hire IT" not in t
    finally:
        async with async_session_maker() as session:
            for lid in ids:
                await session.execute(
                    text("DELETE FROM listing_field_values WHERE listing_id = :id"),
                    {"id": lid},
                )
                await session.execute(
                    text("DELETE FROM listings WHERE id = :id"),
                    {"id": lid},
                )
            await session.commit()
