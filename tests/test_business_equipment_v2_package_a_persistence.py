"""Business Equipment Package A — real Create/Edit/Detail persistence."""
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
from app.seeds.business_equipment_v2 import (
    BUSINESS_CONDITION_KEY,
    BUSINESS_KIND_KEY,
    BUSINESS_SELLER_KEY,
)


FORENSIC_LISTING_ID = 2911


def _auth_as(user_id: int, phone: str = "+79001234567") -> None:
    now = datetime.now(UTC)

    async def _user() -> UserRead:
        return UserRead(
            id=user_id,
            phone=phone,
            full_name="BusinessPersistTester",
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
              :lid, '/media/test/business-e2e.jpg', 0, false,
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
    ids = [i for i in listing_ids if i != FORENSIC_LISTING_ID]
    if not ids:
        return
    await session.execute(
        text("DELETE FROM media WHERE listing_id = ANY(:ids)"),
        {"ids": ids},
    )
    await session.execute(
        text("DELETE FROM listing_field_values WHERE listing_id = ANY(:ids)"),
        {"ids": ids},
    )
    await session.execute(
        text("DELETE FROM listings WHERE id = ANY(:ids)"),
        {"ids": ids},
    )
    await session.commit()


async def _create_activate(
    client,
    *,
    owner_id: int,
    category_id: int,
    title: str,
    fields: dict[str, str],
    price: str = "15000",
) -> int:
    _auth_as(owner_id)
    created = await client.post(
        "/api/v1/listings",
        json={
            "title": title,
            "description": f"{title} business equipment package A",
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
async def test_business_create_persistence_detail_and_2911_boundary(client) -> None:
    await engine.dispose()
    created_ids: list[int] = []
    forensic_existed = False
    forensic_eav_before: dict[str, str] = {}
    try:
        async with async_session_maker() as session:
            owner = (
                await session.execute(select(User).order_by(User.id).limit(1))
            ).scalar_one()
            owner_id = int(owner.id)
            trade_id = await _cat_id(
                session, "business-equipment-torgovoe-oborudovanie"
            )
            parts_id = await _cat_id(
                session, "business-equipment-zapchasti-i-komplektuyuschie"
            )
            print_id = await _cat_id(
                session, "business-equipment-poligraficheskoe-oborudovanie"
            )
            sto_id = await _cat_id(
                session, "business-equipment-oborudovanie-dlya-avtomoek-i-sto"
            )
            forensic = (
                await session.execute(
                    select(Listing).where(Listing.id == FORENSIC_LISTING_ID)
                )
            ).scalar_one_or_none()
            forensic_existed = forensic is not None
            forensic_eav_before = (
                await _eav_map(session, FORENSIC_LISTING_ID)
                if forensic_existed
                else {}
            )

        # Durable equipment — Condition YES
        lid_a = await _create_activate(
            client,
            owner_id=owner_id,
            category_id=trade_id,
            title="PERSIST be vitrina A",
            fields={
                BUSINESS_KIND_KEY: "Торговые витрины",
                BUSINESS_SELLER_KEY: "Частное лицо",
                BUSINESS_CONDITION_KEY: "Б/у",
                "contact_methods": "Чат + телефон",
                "negotiable": "Есть торг",
                "region": "Чуйская область",
                "city": "Бишкек",
            },
        )
        created_ids.append(lid_a)

        # Detail API — characteristics present with human labels via intelligence
        detail = await client.get(
            f"/api/v1/listings/{lid_a}",
            headers={"Authorization": "Bearer test"},
        )
        assert detail.status_code == 200, detail.text
        body = detail.json()
        fields = body.get("fields") or {}
        assert fields.get(BUSINESS_KIND_KEY) == "Торговые витрины"
        assert fields.get(BUSINESS_SELLER_KEY) == "Частное лицо"
        assert fields.get(BUSINESS_CONDITION_KEY) == "Б/у"
        assert fields.get("contact_methods") == "Чат + телефон"
        assert fields.get("negotiable") == "Есть торг"

        intel = await client.get(
            f"/api/v1/categories/intelligence/{trade_id}",
            headers={"Authorization": "Bearer test"},
        )
        assert intel.status_code == 200, intel.text
        core = intel.json().get("core_fields") or intel.json().get("coreFields") or []
        labels = {
            (f.get("field_key") or f.get("fieldKey")): (f.get("label") or "")
            for f in core
            if isinstance(f, dict)
        }
        assert labels.get(BUSINESS_KIND_KEY) == "Товар"
        assert labels.get(BUSINESS_SELLER_KEY) == "Продавец"
        assert labels.get(BUSINESS_CONDITION_KEY) == "Состояние"
        assert labels.get("negotiable") == "Торг"
        assert labels.get("contact_methods") == "Способы связи"

        # Condition NO — needles
        lid_b = await _create_activate(
            client,
            owner_id=owner_id,
            category_id=parts_id,
            title="PERSIST be needles B",
            fields={
                BUSINESS_KIND_KEY: "Иглы промышленные",
                BUSINESS_SELLER_KEY: "Магазин",
                "contact_methods": "Только чат",
                "negotiable": "Без торга",
                "region": "Чуйская область",
                "city": "Бишкек",
            },
        )
        created_ids.append(lid_b)
        async with async_session_maker() as session:
            eav_b = await _eav_map(session, lid_b)
        assert BUSINESS_CONDITION_KEY not in eav_b

        # Boundary — plotters under print L2 (not Electronics catalog)
        lid_c = await _create_activate(
            client,
            owner_id=owner_id,
            category_id=print_id,
            title="PERSIST be plotter C",
            fields={
                BUSINESS_KIND_KEY: "Плоттеры",
                BUSINESS_SELLER_KEY: "Другой",
                BUSINESS_CONDITION_KEY: "Новое",
                "contact_methods": "Чат + Тел. + Wapp",
                "region": "Ошская область",
                "city": "Ош",
            },
        )
        created_ids.append(lid_c)
        async with async_session_maker() as session:
            cat = (
                await session.execute(
                    select(Category).where(Category.id == print_id)
                )
            ).scalar_one()
            assert cat.slug == "business-equipment-poligraficheskoe-oborudovanie"
            eav_c = await _eav_map(session, lid_c)
        assert eav_c[BUSINESS_KIND_KEY] == "Плоттеры"
        assert "electronics_brand" not in eav_c
        assert "brand" not in eav_c

        # STO compressor boundary
        lid_d = await _create_activate(
            client,
            owner_id=owner_id,
            category_id=sto_id,
            title="PERSIST be sto compressor D",
            fields={
                BUSINESS_KIND_KEY: "Компрессоры для СТО",
                BUSINESS_SELLER_KEY: "Частное лицо",
                BUSINESS_CONDITION_KEY: "Б/у",
                "contact_methods": "Только телефон",
                "region": "Чуйская область",
                "city": "Бишкек",
            },
        )
        created_ids.append(lid_d)

        # Publish gate — geo-only blocked
        bare = await client.post(
            "/api/v1/listings",
            json={
                "title": "PERSIST be bare fail",
                "description": "missing kind",
                "price": "100",
                "currency": "KGS",
                "category_id": trade_id,
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

        # Edit — change condition on durable listing
        patched = await client.patch(
            f"/api/v1/listings/{lid_a}",
            json={
                "fields": {
                    BUSINESS_KIND_KEY: "Торговые витрины",
                    BUSINESS_SELLER_KEY: "Частное лицо",
                    BUSINESS_CONDITION_KEY: "Новое",
                    "contact_methods": "Чат + телефон",
                    "negotiable": "Есть торг",
                    "region": "Чуйская область",
                    "city": "Бишкек",
                }
            },
            headers={"Authorization": "Bearer test"},
        )
        assert patched.status_code == 200, patched.text
        async with async_session_maker() as session:
            eav_a = await _eav_map(session, lid_a)
        assert eav_a[BUSINESS_CONDITION_KEY] == "Новое"

        # Forensic 2911 untouched
        if forensic_existed:
            async with async_session_maker() as session:
                still = (
                    await session.execute(
                        select(Listing).where(Listing.id == FORENSIC_LISTING_ID)
                    )
                ).scalar_one_or_none()
                assert still is not None
                eav_f = await _eav_map(session, FORENSIC_LISTING_ID)
            assert eav_f == forensic_eav_before
            assert BUSINESS_KIND_KEY not in eav_f
            detail_old = await client.get(
                f"/api/v1/listings/{FORENSIC_LISTING_ID}",
                headers={"Authorization": "Bearer test"},
            )
            assert detail_old.status_code == 200
            old_fields = detail_old.json().get("fields") or {}
            assert BUSINESS_KIND_KEY not in old_fields

        assert created_ids
    finally:
        async with async_session_maker() as session:
            await _cleanup(session, created_ids)
            leftover = (
                await session.execute(
                    select(Listing.id).where(Listing.id.in_(created_ids or [0]))
                )
            ).scalars().all()
            assert list(leftover) == []
            # 2911 must still exist if it existed before
            forensic_after = (
                await session.execute(
                    select(Listing.id).where(Listing.id == FORENSIC_LISTING_ID)
                )
            ).scalar_one_or_none()
            if forensic_existed:
                assert forensic_after == FORENSIC_LISTING_ID
