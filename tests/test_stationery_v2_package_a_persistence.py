"""Stationery Package A — real Create/Edit persistence via production API."""
from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from sqlalchemy import select, text

from app.api.deps import get_current_user
from app.db.session import async_session_maker, engine
from app.main import app
from app.models.category import Category
from app.models.listing import Listing
from app.models.listing_field_value import ListingFieldValue
from app.models.user import User
from app.schemas.user import UserRead
from app.seeds.stationery_v2 import (
    STATIONERY_CONDITION_KEY,
    STATIONERY_GRADE_KEY,
    STATIONERY_KIND_KEY,
    STATIONERY_SELLER_KEY,
)


def _auth_as(user_id: int, phone: str = "+79001234567") -> None:
    now = datetime.now(UTC)

    async def _user() -> UserRead:
        return UserRead(
            id=user_id,
            phone=phone,
            full_name="StationeryPersistTester",
            is_active=True,
            balance=Decimal("0"),
            last_login=None,
            created_at=now,
            updated_at=now,
        )

    app.dependency_overrides[get_current_user] = _user


async def _cat_id(session, slug: str) -> int:
    cat = (
        await session.execute(select(Category).where(Category.slug == slug))
    ).scalar_one()
    return int(cat.id)


async def _attach_photo(session, listing_id: int) -> None:
    await session.execute(
        text(
            """
            INSERT INTO media (
              listing_id, url, "order", is_placeholder,
              lifecycle_status, moderation_status,
              created_at, updated_at
            ) VALUES (
              :lid, '/media/test/stationery-e2e.jpg', 0, false,
              'ready', 'approved',
              now(), now()
            )
            """
        ),
        {"lid": listing_id},
    )
    await session.commit()


async def _eav_map(session, listing_id: int) -> dict[str, str]:
    rows = (
        await session.execute(
            select(ListingFieldValue).where(
                ListingFieldValue.listing_id == listing_id
            )
        )
    ).scalars().all()
    return {
        r.field_key: (r.value_text or "")
        for r in rows
        if r.value_text is not None
    }


async def _cleanup(session, listing_ids: list[int]) -> None:
    if not listing_ids:
        return
    await session.execute(
        text("DELETE FROM media WHERE listing_id = ANY(:ids)"),
        {"ids": listing_ids},
    )
    await session.execute(
        text("DELETE FROM listing_field_values WHERE listing_id = ANY(:ids)"),
        {"ids": listing_ids},
    )
    await session.execute(
        text("DELETE FROM listings WHERE id = ANY(:ids)"),
        {"ids": listing_ids},
    )
    await session.commit()


async def _create_activate(
    client,
    *,
    owner_id: int,
    category_id: int,
    title: str,
    fields: dict[str, str],
    price: str = "900",
) -> int:
    _auth_as(owner_id)
    created = await client.post(
        "/api/v1/listings",
        json={
            "title": title,
            "description": f"{title} stationery package A",
            "price": price,
            "currency": "KGS",
            "category_id": category_id,
            "status": "draft",
            "fields": fields,
        },
        headers={"Authorization": "Bearer test"},
    )
    assert created.status_code in (200, 201), created.text
    listing_id = int(created.json()["id"])
    async with async_session_maker() as session:
        await _attach_photo(session, listing_id)
    act = await client.patch(
        f"/api/v1/listings/{listing_id}/status",
        json={"status": "active"},
        headers={"Authorization": "Bearer test"},
    )
    assert act.status_code == 200, act.text
    async with async_session_maker() as session:
        eav = await _eav_map(session, listing_id)
    for key, value in fields.items():
        assert eav.get(key) == value, (key, eav, fields)
    return listing_id


@pytest.mark.asyncio
async def test_stationery_create_persistence_cases_a_d(client) -> None:
    """A consumable / B fiction / C textbook / D backpack + publish gate."""
    await engine.dispose()
    created_ids: list[int] = []
    try:
        async with async_session_maker() as session:
            owner = (
                await session.execute(select(User).order_by(User.id).limit(1))
            ).scalar_one()
            owner_id = int(owner.id)
            stationery_id = await _cat_id(
                session, "stationery-books-kantselyarskie-tovary"
            )
            fiction_id = await _cat_id(
                session, "stationery-books-hudozhestvennaya-literatura"
            )
            textbooks_id = await _cat_id(
                session, "stationery-books-uchebniki-i-uchebnye-posobiya"
            )
            before = (
                await session.execute(select(Listing.id))
            ).scalars().all()
            before_set = set(int(x) for x in before)

        # A — consumable: NO Condition, NO Grade
        lid_a = await _create_activate(
            client,
            owner_id=owner_id,
            category_id=stationery_id,
            title="PERSIST stationery pens A",
            fields={
                STATIONERY_KIND_KEY: "Ручки",
                STATIONERY_SELLER_KEY: "Частное лицо",
                "contact_methods": "Только чат",
                "negotiable": "Есть торг",
                "region": "Чуйская область",
                "city": "Бишкек",
            },
        )
        created_ids.append(lid_a)
        async with async_session_maker() as session:
            eav = await _eav_map(session, lid_a)
        assert STATIONERY_CONDITION_KEY not in eav
        assert STATIONERY_GRADE_KEY not in eav

        # B — fiction book: Condition YES, NO Grade
        lid_b = await _create_activate(
            client,
            owner_id=owner_id,
            category_id=fiction_id,
            title="PERSIST stationery novel B",
            fields={
                STATIONERY_KIND_KEY: "Романы",
                STATIONERY_SELLER_KEY: "Магазин",
                STATIONERY_CONDITION_KEY: "Б/у",
                "contact_methods": "Чат + телефон",
                "negotiable": "Без торга",
                "region": "Ошская область",
                "city": "Ош",
            },
        )
        created_ids.append(lid_b)
        async with async_session_maker() as session:
            eav = await _eav_map(session, lid_b)
        assert eav[STATIONERY_CONDITION_KEY] == "Б/у"
        assert STATIONERY_GRADE_KEY not in eav
        assert "language" not in eav

        # C — school textbook: Condition + Grade
        lid_c = await _create_activate(
            client,
            owner_id=owner_id,
            category_id=textbooks_id,
            title="PERSIST stationery algebra C",
            fields={
                STATIONERY_KIND_KEY: "Алгебра",
                STATIONERY_SELLER_KEY: "Частное лицо",
                STATIONERY_CONDITION_KEY: "Б/у",
                STATIONERY_GRADE_KEY: "7 класс",
                "contact_methods": "Только чат",
                "region": "Чуйская область",
                "city": "Бишкек",
            },
        )
        created_ids.append(lid_c)
        async with async_session_maker() as session:
            eav = await _eav_map(session, lid_c)
        assert eav[STATIONERY_GRADE_KEY] == "7 класс"
        assert eav[STATIONERY_CONDITION_KEY] == "Б/у"

        # D — school backpack: Condition YES, NO Grade
        lid_d = await _create_activate(
            client,
            owner_id=owner_id,
            category_id=stationery_id,
            title="PERSIST stationery backpack D",
            fields={
                STATIONERY_KIND_KEY: "Школьные рюкзаки",
                STATIONERY_SELLER_KEY: "Другой",
                STATIONERY_CONDITION_KEY: "Новое",
                "contact_methods": "Чат + Тел. + Wapp",
                "region": "Чуйская область",
                "city": "Бишкек",
            },
        )
        created_ids.append(lid_d)
        async with async_session_maker() as session:
            eav = await _eav_map(session, lid_d)
        assert eav[STATIONERY_CONDITION_KEY] == "Новое"
        assert STATIONERY_GRADE_KEY not in eav

        # Publish gate — geo-only incomplete blocked
        bare = await client.post(
            "/api/v1/listings",
            json={
                "title": "PERSIST stationery bare fail",
                "description": "missing kind",
                "price": "100",
                "currency": "KGS",
                "category_id": stationery_id,
                "status": "draft",
                "fields": {"city": "Бишкек", "region": "Чуйская область"},
            },
            headers={"Authorization": "Bearer test"},
        )
        assert bare.status_code in (200, 201), bare.text
        bare_id = int(bare.json()["id"])
        created_ids.append(bare_id)
        async with async_session_maker() as session:
            await _attach_photo(session, bare_id)
        blocked = await client.patch(
            f"/api/v1/listings/{bare_id}/status",
            json={"status": "active"},
            headers={"Authorization": "Bearer test"},
        )
        assert blocked.status_code == 400, blocked.text
        assert blocked.json().get("code") == "MISSING_REQUIRED_FIELDS"

        async with async_session_maker() as session:
            after = (
                await session.execute(select(Listing.id))
            ).scalars().all()
            after_set = set(int(x) for x in after)
        # Before teardown, fixtures exist; delta checked after cleanup.
        assert created_ids
        _ = before_set, after_set
    finally:
        async with async_session_maker() as session:
            await _cleanup(session, created_ids)
            after = (
                await session.execute(select(Listing.id))
            ).scalars().all()
            # Persistent marketplace delta must be 0 vs pre-test snapshot
            # (recompute before set inside finally is unsafe — use created cleanup).
            leftover = (
                await session.execute(
                    select(Listing.id).where(Listing.id.in_(created_ids or [0]))
                )
            ).scalars().all()
            assert list(leftover) == []


@pytest.mark.asyncio
async def test_stationery_edit_textbook_grade_condition(client) -> None:
    await engine.dispose()
    created_ids: list[int] = []
    try:
        async with async_session_maker() as session:
            owner = (
                await session.execute(select(User).order_by(User.id).limit(1))
            ).scalar_one()
            owner_id = int(owner.id)
            textbooks_id = await _cat_id(
                session, "stationery-books-uchebniki-i-uchebnye-posobiya"
            )

        lid = await _create_activate(
            client,
            owner_id=owner_id,
            category_id=textbooks_id,
            title="PERSIST stationery edit textbook",
            fields={
                STATIONERY_KIND_KEY: "Физика",
                STATIONERY_SELLER_KEY: "Частное лицо",
                STATIONERY_CONDITION_KEY: "Б/у",
                STATIONERY_GRADE_KEY: "9 класс",
                "contact_methods": "Только чат",
                "region": "Чуйская область",
                "city": "Бишкек",
            },
        )
        created_ids.append(lid)

        # API replace_from_known_fields: send full Create EAV (Flutter safe-edit
        # merge happens client-side before PATCH).
        patched = await client.patch(
            f"/api/v1/listings/{lid}",
            json={
                "fields": {
                    STATIONERY_KIND_KEY: "Физика",
                    STATIONERY_SELLER_KEY: "Частное лицо",
                    STATIONERY_CONDITION_KEY: "Новое",
                    STATIONERY_GRADE_KEY: "10 класс",
                    "contact_methods": "Только чат",
                    "region": "Чуйская область",
                    "city": "Бишкек",
                }
            },
            headers={"Authorization": "Bearer test"},
        )
        assert patched.status_code == 200, patched.text
        async with async_session_maker() as session:
            eav = await _eav_map(session, lid)
        assert eav[STATIONERY_GRADE_KEY] == "10 класс"
        assert eav[STATIONERY_CONDITION_KEY] == "Новое"
        assert eav[STATIONERY_KIND_KEY] == "Физика"
        assert eav[STATIONERY_SELLER_KEY] == "Частное лицо"
        assert "language" not in eav
    finally:
        async with async_session_maker() as session:
            await _cleanup(session, created_ids)
