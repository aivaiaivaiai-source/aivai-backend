"""Sport Package A — real Create/Edit/Detail persistence + fixture hygiene."""
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
from app.seeds.sport_v2 import SPORT_CONDITION_KEY, SPORT_KIND_KEY, SPORT_SELLER_KEY


def _auth_as(user_id: int, phone: str = "+79001234567") -> None:
    now = datetime.now(UTC)

    async def _user() -> UserRead:
        return UserRead(
            id=user_id,
            phone=phone,
            full_name="SportPersistTester",
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
              :lid, '/media/test/sport-hobby-e2e.jpg', 0, false,
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
    price: str = "5000",
) -> int:
    _auth_as(owner_id)
    created = await client.post(
        "/api/v1/listings",
        json={
            "title": title,
            "description": f"{title} sport package A",
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
    assert "size" not in eav
    assert "brand" not in eav
    assert "price_basis" not in eav
    return listing_id


@pytest.mark.asyncio
async def test_sport_hobby_create_persistence_detail_edit(client) -> None:
    await engine.dispose()
    created_ids: list[int] = []
    try:
        async with async_session_maker() as session:
            owner = (
                await session.execute(select(User).order_by(User.id).limit(1))
            ).scalar_one()
            owner_id = int(owner.id)
            sport_id = await _cat_id(session, "sports-hobby-sportivnye-tovary")
            nutrition_id = await _cat_id(
                session, "sports-hobby-sportivnoe-pitanie"
            )
            fishing_id = await _cat_id(session, "sports-hobby-ohota-i-rybalka")
            music_id = await _cat_id(
                session, "sports-hobby-muzykalnye-instrumenty"
            )
            horse_id = await _cat_id(
                session, "sports-hobby-konnyy-sport-i-verhovaya-ezda"
            )
            collect_id = await _cat_id(
                session, "sports-hobby-kollektsionirovanie"
            )

        # E2E A — durable sport good + Condition
        lid_a = await _create_activate(
            client,
            owner_id=owner_id,
            category_id=sport_id,
            title="PERSIST sport durable A",
            fields={
                SPORT_KIND_KEY: "Лыжи",
                SPORT_SELLER_KEY: "Частное лицо",
                SPORT_CONDITION_KEY: "Новое",
                "contact_methods": "Чат + телефон",
                "negotiable": "Есть торг",
                "region": "Чуйская область",
                "city": "Бишкек",
            },
            price="12000",
        )
        created_ids.append(lid_a)

        detail = await client.get(
            f"/api/v1/listings/{lid_a}",
            headers={"Authorization": "Bearer test"},
        )
        assert detail.status_code == 200, detail.text
        body = detail.json()
        fields = body.get("fields") or {}
        assert fields.get(SPORT_KIND_KEY) == "Лыжи"
        assert fields.get(SPORT_SELLER_KEY) == "Частное лицо"
        assert fields.get(SPORT_CONDITION_KEY) == "Новое"

        intel = await client.get(
            f"/api/v1/categories/intelligence/{sport_id}",
            headers={"Authorization": "Bearer test"},
        )
        assert intel.status_code == 200, intel.text
        core = intel.json().get("core_fields") or intel.json().get("coreFields") or []
        labels = {
            (f.get("field_key") or f.get("fieldKey")): (f.get("label") or "")
            for f in core
            if isinstance(f, dict)
        }
        assert labels.get(SPORT_KIND_KEY) == "Товар"
        assert labels.get(SPORT_SELLER_KEY) == "Продавец"
        assert labels.get(SPORT_CONDITION_KEY) == "Состояние"
        assert "size" not in labels
        assert "brand" not in labels

        # E2E B — nutrition: NO Condition
        lid_b = await _create_activate(
            client,
            owner_id=owner_id,
            category_id=nutrition_id,
            title="PERSIST sport nutrition B",
            fields={
                SPORT_KIND_KEY: "Протеин",
                SPORT_SELLER_KEY: "Магазин",
                "contact_methods": "Только чат",
                "negotiable": "Без торга",
                "region": "Чуйская область",
                "city": "Бишкек",
            },
            price="3500",
        )
        created_ids.append(lid_b)
        async with async_session_maker() as session:
            eav_b = await _eav_map(session, lid_b)
        assert SPORT_CONDITION_KEY not in eav_b
        intel_n = await client.get(
            f"/api/v1/categories/intelligence/{nutrition_id}",
            headers={"Authorization": "Bearer test"},
        )
        nutrition_keys = {
            (f.get("field_key") or f.get("fieldKey"))
            for f in (
                intel_n.json().get("core_fields")
                or intel_n.json().get("coreFields")
                or []
            )
            if isinstance(f, dict)
        }
        assert SPORT_CONDITION_KEY not in nutrition_keys

        # E2E C/D — fishing + echo sounder
        lid_c = await _create_activate(
            client,
            owner_id=owner_id,
            category_id=fishing_id,
            title="PERSIST sport fishing C",
            fields={
                SPORT_KIND_KEY: "Удочки",
                SPORT_SELLER_KEY: "Частное лицо",
                SPORT_CONDITION_KEY: "Б/у",
                "contact_methods": "Чат + Wapp",
                "region": "Иссык-Кульская область",
                "city": "Каракол",
            },
            price="4500",
        )
        created_ids.append(lid_c)

        lid_d = await _create_activate(
            client,
            owner_id=owner_id,
            category_id=fishing_id,
            title="PERSIST sport echo D",
            fields={
                SPORT_KIND_KEY: "Эхолоты",
                SPORT_SELLER_KEY: "Магазин",
                SPORT_CONDITION_KEY: "Новое",
                "contact_methods": "Только телефон",
                "region": "Чуйская область",
                "city": "Бишкек",
            },
            price="18000",
        )
        created_ids.append(lid_d)
        async with async_session_maker() as session:
            cat = (
                await session.execute(select(Category).where(Category.id == fishing_id))
            ).scalar_one()
            assert cat.slug.startswith("sports-hobby-")
            eav_d = await _eav_map(session, lid_d)
        assert eav_d.get(SPORT_KIND_KEY) == "Эхолоты"

        # E2E E — musical instrument (synthesizer)
        lid_e = await _create_activate(
            client,
            owner_id=owner_id,
            category_id=music_id,
            title="PERSIST sport synth E",
            fields={
                SPORT_KIND_KEY: "Синтезаторы",
                SPORT_SELLER_KEY: "Другой",
                SPORT_CONDITION_KEY: "Б/у",
                "contact_methods": "Чат + Тел. + Wapp",
                "region": "Чуйская область",
                "city": "Бишкек",
            },
            price="25000",
        )
        created_ids.append(lid_e)

        # E2E F — horse gear
        lid_f = await _create_activate(
            client,
            owner_id=owner_id,
            category_id=horse_id,
            title="PERSIST sport horse F",
            fields={
                SPORT_KIND_KEY: "Сёдла",
                SPORT_SELLER_KEY: "Частное лицо",
                SPORT_CONDITION_KEY: "Новое",
                "contact_methods": "Чат + телефон",
                "region": "Нарынская область",
                "city": "Нарын",
            },
            price="15000",
        )
        created_ids.append(lid_f)
        async with async_session_maker() as session:
            eav_f = await _eav_map(session, lid_f)
        assert eav_f.get(SPORT_KIND_KEY) == "Сёдла"
        assert "Лошади" not in eav_f.values()

        # E2E G — collectible
        lid_g = await _create_activate(
            client,
            owner_id=owner_id,
            category_id=collect_id,
            title="PERSIST sport collect G",
            fields={
                SPORT_KIND_KEY: "Монеты",
                SPORT_SELLER_KEY: "Магазин",
                SPORT_CONDITION_KEY: "Б/у",
                "contact_methods": "Только чат",
                "region": "Чуйская область",
                "city": "Бишкек",
            },
            price="2000",
        )
        created_ids.append(lid_g)
        async with async_session_maker() as session:
            eav_g = await _eav_map(session, lid_g)
        assert eav_g.get(SPORT_KIND_KEY) == "Монеты"
        assert "appraisal" not in eav_g
        assert "оценка" not in {v.lower() for v in eav_g.values()}

        # Edit E2E — Condition Новое → Б/у → prune via kind switch to bait (NO)
        _auth_as(owner_id)
        patch1 = await client.patch(
            f"/api/v1/listings/{lid_c}",
            json={"fields": {SPORT_CONDITION_KEY: "Новое"}},
            headers={"Authorization": "Bearer test"},
        )
        assert patch1.status_code == 200, patch1.text
        async with async_session_maker() as session:
            assert (await _eav_map(session, lid_c)).get(SPORT_CONDITION_KEY) == "Новое"

        patch2 = await client.patch(
            f"/api/v1/listings/{lid_c}",
            json={"fields": {SPORT_CONDITION_KEY: "Б/у"}},
            headers={"Authorization": "Bearer test"},
        )
        assert patch2.status_code == 200, patch2.text
        async with async_session_maker() as session:
            assert (await _eav_map(session, lid_c)).get(SPORT_CONDITION_KEY) == "Б/у"

        patch3 = await client.patch(
            f"/api/v1/listings/{lid_c}",
            json={
                "fields": {
                    SPORT_KIND_KEY: "Блёсны и приманки",
                    SPORT_CONDITION_KEY: "",
                }
            },
            headers={"Authorization": "Bearer test"},
        )
        assert patch3.status_code == 200, patch3.text
        async with async_session_maker() as session:
            eav_pruned = await _eav_map(session, lid_c)
        assert eav_pruned.get(SPORT_KIND_KEY) == "Блёсны и приманки"
        assert eav_pruned.get(SPORT_CONDITION_KEY, "") in {"", None}

        # Retired identities stay inactive
        for retired_slug in (
            "sports-equipment",
            "sports-tourism",
            "sports-music",
            "sports-hobby-yurty-i-natsionalnye-izdeliya",
            "sports-hobby-shyrdaki-i-izdeliya-iz-voyloka",
        ):
            async with async_session_maker() as session:
                row = (
                    await session.execute(
                        select(Category).where(Category.slug == retired_slug)
                    )
                ).scalar_one()
                assert row.is_active is False

        # Empty schema publish must be blocked for Backend-SoT leaf
        # (activation defense already covered globally; assert cores non-empty)
        async with async_session_maker() as session:
            core_count = (
                await session.execute(
                    text(
                        """
                        SELECT count(*) FROM category_core_fields
                        WHERE category_id = :cid
                        """
                    ),
                    {"cid": sport_id},
                )
            ).scalar_one()
        assert int(core_count or 0) >= 5

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
                        WHERE c.slug LIKE 'sports-hobby-%'
                          AND l.title LIKE 'PERSIST sport%'
                        """
                    )
                )
            ).scalar_one()
            assert int(left or 0) == 0
