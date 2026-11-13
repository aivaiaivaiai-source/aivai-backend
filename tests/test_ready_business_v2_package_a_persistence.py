"""Ready Business Package A — real Create/Edit/Detail persistence + fixture hygiene."""
from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from sqlalchemy import select, text

from app.api.deps import get_current_user
from app.db.session import async_session_maker, engine
from app.main import app
from app.models.category import Category
from app.models.listing_field_value import ListingFieldValue
from app.models.user import User
from app.schemas.user import UserRead
from app.seeds.ready_business_v2 import (
    READY_BUSINESS_KIND_KEY,
    READY_BUSINESS_POSTER_KEY,
    READY_BUSINESS_PREMISES_KEY,
)


def _auth_as(user_id: int, phone: str = "+79001234567") -> None:
    now = datetime.now(UTC)

    async def _user() -> UserRead:
        return UserRead(
            id=user_id,
            phone=phone,
            full_name="ReadyBusinessPersistTester",
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
              :lid, '/media/test/ready-business-e2e.jpg', 0, false,
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
    ids = [i for i in listing_ids if i]
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
    price: str = "250000",
) -> int:
    _auth_as(owner_id)
    created = await client.post(
        "/api/v1/listings",
        json={
            "title": title,
            "description": f"{title} ready business package A",
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
    assert "condition" not in eav
    assert "revenue" not in eav
    assert "profit" not in eav
    return listing_id


@pytest.mark.asyncio
async def test_ready_business_create_persistence_detail_edit(client) -> None:
    await engine.dispose()
    created_ids: list[int] = []
    try:
        async with async_session_maker() as session:
            owner = (
                await session.execute(select(User).order_by(User.id).limit(1))
            ).scalar_one()
            owner_id = int(owner.id)
            shops_id = await _cat_id(
                session, "ready-business-magaziny-i-torgovye-tochki"
            )
            online_id = await _cat_id(session, "ready-business-onlayn-magaziny")
            franchise_id = await _cat_id(session, "ready-business-franshizy")
            auto_id = await _cat_id(
                session, "ready-business-avtomoyki-avtouslugi-i-sto"
            )
            production_id = await _cat_id(
                session, "ready-business-proizvodstvo-i-tseha"
            )

        # E2E A — physical ready business + premises
        lid_a = await _create_activate(
            client,
            owner_id=owner_id,
            category_id=shops_id,
            title="PERSIST rb shop A",
            fields={
                READY_BUSINESS_KIND_KEY: "Магазины",
                READY_BUSINESS_POSTER_KEY: "Владелец",
                READY_BUSINESS_PREMISES_KEY: "В аренде",
                "contact_methods": "Чат + телефон",
                "negotiable": "Есть торг",
                "region": "Чуйская область",
                "city": "Бишкек",
            },
            price="450000",
        )
        created_ids.append(lid_a)

        detail = await client.get(
            f"/api/v1/listings/{lid_a}",
            headers={"Authorization": "Bearer test"},
        )
        assert detail.status_code == 200, detail.text
        body = detail.json()
        fields = body.get("fields") or {}
        assert fields.get(READY_BUSINESS_KIND_KEY) == "Магазины"
        assert fields.get(READY_BUSINESS_POSTER_KEY) == "Владелец"
        assert fields.get(READY_BUSINESS_PREMISES_KEY) == "В аренде"
        assert "condition" not in fields

        intel = await client.get(
            f"/api/v1/categories/intelligence/{shops_id}",
            headers={"Authorization": "Bearer test"},
        )
        assert intel.status_code == 200, intel.text
        core = intel.json().get("core_fields") or intel.json().get("coreFields") or []
        labels = {
            (f.get("field_key") or f.get("fieldKey")): (f.get("label") or "")
            for f in core
            if isinstance(f, dict)
        }
        assert labels.get(READY_BUSINESS_KIND_KEY) == "Вид бизнеса"
        assert labels.get(READY_BUSINESS_POSTER_KEY) == "Кто разместил"
        assert labels.get(READY_BUSINESS_PREMISES_KEY) == "Помещение"
        assert "condition" not in labels
        assert "revenue" not in labels
        assert "seller_type" not in labels

        # E2E B — online business: no premises
        lid_b = await _create_activate(
            client,
            owner_id=owner_id,
            category_id=online_id,
            title="PERSIST rb online B",
            fields={
                READY_BUSINESS_KIND_KEY: "Интернет-магазины",
                READY_BUSINESS_POSTER_KEY: "Представитель",
                "contact_methods": "Только чат",
                "negotiable": "Без торга",
                "region": "Чуйская область",
                "city": "Бишкек",
            },
            price="120000",
        )
        created_ids.append(lid_b)
        async with async_session_maker() as session:
            eav_b = await _eav_map(session, lid_b)
        assert READY_BUSINESS_PREMISES_KEY not in eav_b
        assert eav_b.get(READY_BUSINESS_KIND_KEY) == "Интернет-магазины"

        intel_online = await client.get(
            f"/api/v1/categories/intelligence/{online_id}",
            headers={"Authorization": "Bearer test"},
        )
        assert intel_online.status_code == 200
        online_keys = {
            (f.get("field_key") or f.get("fieldKey"))
            for f in (
                intel_online.json().get("core_fields")
                or intel_online.json().get("coreFields")
                or []
            )
            if isinstance(f, dict)
        }
        assert READY_BUSINESS_PREMISES_KEY not in online_keys
        assert "condition" not in online_keys

        # E2E C — franchise: entry price, no finance questionnaire, no premises
        lid_c = await _create_activate(
            client,
            owner_id=owner_id,
            category_id=franchise_id,
            title="PERSIST rb franchise C",
            fields={
                READY_BUSINESS_KIND_KEY: "Франшиза точки",
                READY_BUSINESS_POSTER_KEY: "Другой",
                "contact_methods": "Чат + Wapp",
                "negotiable": "Есть торг",
                "region": "Ошская область",
                "city": "Ош",
            },
            price="80000",
        )
        created_ids.append(lid_c)
        async with async_session_maker() as session:
            eav_c = await _eav_map(session, lid_c)
        assert READY_BUSINESS_PREMISES_KEY not in eav_c
        assert "royalty" not in eav_c
        assert "investment" not in eav_c
        assert "payback" not in eav_c
        assert "condition" not in eav_c

        # E2E D — auto business remains Ready Business
        lid_d = await _create_activate(
            client,
            owner_id=owner_id,
            category_id=auto_id,
            title="PERSIST rb auto D",
            fields={
                READY_BUSINESS_KIND_KEY: "Автомойки",
                READY_BUSINESS_POSTER_KEY: "Владелец",
                READY_BUSINESS_PREMISES_KEY: "В собственности",
                "contact_methods": "Только телефон",
                "region": "Чуйская область",
                "city": "Бишкек",
            },
            price="900000",
        )
        created_ids.append(lid_d)
        async with async_session_maker() as session:
            cat = (
                await session.execute(select(Category).where(Category.id == auto_id))
            ).scalar_one()
            assert cat.slug.startswith("ready-business-")
            eav_d = await _eav_map(session, lid_d)
        assert eav_d.get(READY_BUSINESS_KIND_KEY) == "Автомойки"
        assert eav_d.get(READY_BUSINESS_PREMISES_KEY) == "В собственности"

        # E2E E — production business (no equipment-only leak)
        lid_e = await _create_activate(
            client,
            owner_id=owner_id,
            category_id=production_id,
            title="PERSIST rb production E",
            fields={
                READY_BUSINESS_KIND_KEY: "Заводы",
                READY_BUSINESS_POSTER_KEY: "Представитель",
                READY_BUSINESS_PREMISES_KEY: "В аренде",
                "contact_methods": "Чат + Тел. + Wapp",
                "region": "Чуйская область",
                "city": "Бишкек",
            },
            price="1500000",
        )
        created_ids.append(lid_e)
        async with async_session_maker() as session:
            eav_e = await _eav_map(session, lid_e)
        assert eav_e.get(READY_BUSINESS_KIND_KEY) == "Заводы"
        assert "Линии" not in eav_e.values()

        # Edit E2E — premises empty→В аренде→В собственности→cleared
        _auth_as(owner_id)
        patch1 = await client.patch(
            f"/api/v1/listings/{lid_e}",
            json={"fields": {READY_BUSINESS_PREMISES_KEY: "В аренде"}},
            headers={"Authorization": "Bearer test"},
        )
        assert patch1.status_code == 200, patch1.text
        async with async_session_maker() as session:
            assert (await _eav_map(session, lid_e)).get(
                READY_BUSINESS_PREMISES_KEY
            ) == "В аренде"

        patch2 = await client.patch(
            f"/api/v1/listings/{lid_e}",
            json={"fields": {READY_BUSINESS_PREMISES_KEY: "В собственности"}},
            headers={"Authorization": "Bearer test"},
        )
        assert patch2.status_code == 200, patch2.text
        async with async_session_maker() as session:
            assert (await _eav_map(session, lid_e)).get(
                READY_BUSINESS_PREMISES_KEY
            ) == "В собственности"

        patch3 = await client.patch(
            f"/api/v1/listings/{lid_e}",
            json={"fields": {READY_BUSINESS_PREMISES_KEY: ""}},
            headers={"Authorization": "Bearer test"},
        )
        assert patch3.status_code == 200, patch3.text
        async with async_session_maker() as session:
            eav_cleared = await _eav_map(session, lid_e)
        assert eav_cleared.get(READY_BUSINESS_PREMISES_KEY, "") in {"", None}

        # Retired identities stay inactive / schema-less
        for retired_slug in (
            "ready-business-cafe",
            "ready-business-dolya-v-biznese-i-investitsii",
            "ready-business-kriptobiznes-i-tsifrovye-aktivy",
            "ready-business-biznes-pod-klyuch",
        ):
            async with async_session_maker() as session:
                row = (
                    await session.execute(
                        select(Category).where(Category.slug == retired_slug)
                    )
                ).scalar_one()
                assert row.is_active is False

    finally:
        async with async_session_maker() as session:
            await _cleanup(session, created_ids)
        async with async_session_maker() as session:
            left = (
                await session.execute(
                    text(
                        """
                        SELECT count(*) FROM listings l
                        JOIN categories c ON c.id = l.category_id
                        WHERE c.slug LIKE 'ready-business-%'
                          AND l.title LIKE 'PERSIST rb%'
                        """
                    )
                )
            ).scalar_one()
            assert int(left or 0) == 0
