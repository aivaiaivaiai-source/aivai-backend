"""Beauty Package A — real Create/Edit/Detail persistence + fixture hygiene."""
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
from app.seeds.beauty_v2 import (
    BEAUTY_CONDITION_KEY,
    BEAUTY_KIND_KEY,
    BEAUTY_SELLER_KEY,
)


def _auth_as(user_id: int, phone: str = "+79001234567") -> None:
    now = datetime.now(UTC)

    async def _user() -> UserRead:
        return UserRead(
            id=user_id,
            phone=phone,
            full_name="BeautyPersistTester",
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
              :lid, '/media/test/beauty-e2e.jpg', 0, false,
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
    price: str = "1500",
) -> int:
    _auth_as(owner_id)
    created = await client.post(
        "/api/v1/listings",
        json={
            "title": title,
            "description": f"{title} beauty package A",
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
    assert "package_state" not in eav
    assert "beauty_brand" not in eav
    assert "volume" not in eav
    assert "price_basis" not in eav
    return listing_id


@pytest.mark.asyncio
async def test_beauty_create_persistence_detail_edit(client) -> None:
    await engine.dispose()
    created_ids: list[int] = []
    try:
        async with async_session_maker() as session:
            owner = (
                await session.execute(select(User).order_by(User.id).limit(1))
            ).scalar_one()
            owner_id = int(owner.id)
            cosmetics_id = await _cat_id(session, "beauty-kosmetika")
            perfume_id = await _cat_id(session, "beauty-parfyumeriya")
            hair_id = await _cat_id(session, "beauty-uhod-za-volosami")
            tools_id = await _cat_id(
                session, "beauty-instrumenty-oborud-e-dlya-krasoty"
            )
            tattoo_id = await _cat_id(
                session, "beauty-tovary-dlya-tatu-i-pirsinga"
            )
            other_id = await _cat_id(
                session, "beauty-prochee-dlya-krasoty-i-uhoda"
            )

        # E2E A — cosmetic consumable: NO Condition / NO package_state
        lid_a = await _create_activate(
            client,
            owner_id=owner_id,
            category_id=cosmetics_id,
            title="PERSIST beauty cosmetic A",
            fields={
                BEAUTY_KIND_KEY: "Тональные средства",
                BEAUTY_SELLER_KEY: "Частное лицо",
                "contact_methods": "Чат + телефон",
                "negotiable": "Есть торг",
                "region": "Чуйская область",
                "city": "Бишкек",
            },
            price="1200",
        )
        created_ids.append(lid_a)
        async with async_session_maker() as session:
            eav_a = await _eav_map(session, lid_a)
        assert BEAUTY_CONDITION_KEY not in eav_a
        assert "package_state" not in eav_a

        detail = await client.get(
            f"/api/v1/listings/{lid_a}",
            headers={"Authorization": "Bearer test"},
        )
        assert detail.status_code == 200, detail.text
        body = detail.json()
        fields = body.get("fields") or {}
        assert fields.get(BEAUTY_KIND_KEY) == "Тональные средства"
        assert fields.get(BEAUTY_SELLER_KEY) == "Частное лицо"

        intel = await client.get(
            f"/api/v1/categories/intelligence/{cosmetics_id}",
            headers={"Authorization": "Bearer test"},
        )
        assert intel.status_code == 200, intel.text
        core = intel.json().get("core_fields") or intel.json().get("coreFields") or []
        labels = {
            (f.get("field_key") or f.get("fieldKey")): (f.get("label") or "")
            for f in core
            if isinstance(f, dict)
        }
        assert labels.get(BEAUTY_KIND_KEY) == "Товар"
        assert labels.get(BEAUTY_SELLER_KEY) == "Продавец"
        assert BEAUTY_CONDITION_KEY not in labels
        assert "package_state" not in labels
        assert "beauty_brand" not in labels

        # E2E B — perfume: NO Condition / NO brand/model/volume/gender
        lid_b = await _create_activate(
            client,
            owner_id=owner_id,
            category_id=perfume_id,
            title="PERSIST beauty perfume B",
            fields={
                BEAUTY_KIND_KEY: "Духи",
                BEAUTY_SELLER_KEY: "Магазин",
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
        assert BEAUTY_CONDITION_KEY not in eav_b
        assert "beauty_brand" not in eav_b
        assert "volume" not in eav_b
        assert "gender" not in eav_b

        # E2E C — hair care consumable
        lid_c = await _create_activate(
            client,
            owner_id=owner_id,
            category_id=hair_id,
            title="PERSIST beauty hair C",
            fields={
                BEAUTY_KIND_KEY: "Шампуни",
                BEAUTY_SELLER_KEY: "Другой",
                "contact_methods": "Чат + Wapp",
                "region": "Чуйская область",
                "city": "Бишкек",
            },
            price="800",
        )
        created_ids.append(lid_c)
        async with async_session_maker() as session:
            eav_c = await _eav_map(session, lid_c)
        assert BEAUTY_CONDITION_KEY not in eav_c

        # E2E D — durable personal device (фен) Condition YES
        lid_d = await _create_activate(
            client,
            owner_id=owner_id,
            category_id=tools_id,
            title="PERSIST beauty dryer D",
            fields={
                BEAUTY_KIND_KEY: "Фены",
                BEAUTY_SELLER_KEY: "Частное лицо",
                BEAUTY_CONDITION_KEY: "Новое",
                "contact_methods": "Чат + телефон",
                "negotiable": "Есть торг",
                "region": "Чуйская область",
                "city": "Бишкек",
            },
            price="4500",
        )
        created_ids.append(lid_d)
        detail_d = await client.get(
            f"/api/v1/listings/{lid_d}",
            headers={"Authorization": "Bearer test"},
        )
        assert detail_d.status_code == 200
        assert (detail_d.json().get("fields") or {}).get(BEAUTY_KIND_KEY) == "Фены"
        assert (detail_d.json().get("fields") or {}).get(
            BEAUTY_CONDITION_KEY
        ) == "Новое"
        intel_t = await client.get(
            f"/api/v1/categories/intelligence/{tools_id}",
            headers={"Authorization": "Bearer test"},
        )
        tool_labels = {
            (f.get("field_key") or f.get("fieldKey")): (f.get("label") or "")
            for f in (
                intel_t.json().get("core_fields")
                or intel_t.json().get("coreFields")
                or []
            )
            if isinstance(f, dict)
        }
        assert tool_labels.get(BEAUTY_KIND_KEY) == "Товар"
        assert tool_labels.get(BEAUTY_CONDITION_KEY) == "Состояние"

        # E2E E — manicure lamp durable (tools L2 ownership)
        lid_e = await _create_activate(
            client,
            owner_id=owner_id,
            category_id=tools_id,
            title="PERSIST beauty lamp E",
            fields={
                BEAUTY_KIND_KEY: "Лампы для маникюра",
                BEAUTY_SELLER_KEY: "Магазин",
                BEAUTY_CONDITION_KEY: "Б/у",
                "contact_methods": "Только телефон",
                "region": "Чуйская область",
                "city": "Бишкек",
            },
            price="2800",
        )
        created_ids.append(lid_e)
        async with async_session_maker() as session:
            eav_e = await _eav_map(session, lid_e)
        assert eav_e.get(BEAUTY_CONDITION_KEY) == "Б/у"

        # E2E F — tattoo tool (Beauty ownership, not service/BE)
        lid_f = await _create_activate(
            client,
            owner_id=owner_id,
            category_id=tattoo_id,
            title="PERSIST beauty tattoo F",
            fields={
                BEAUTY_KIND_KEY: "Машинки для тату",
                BEAUTY_SELLER_KEY: "Частное лицо",
                BEAUTY_CONDITION_KEY: "Новое",
                "contact_methods": "Чат + Тел. + Wapp",
                "region": "Чуйская область",
                "city": "Бишкек",
            },
            price="15000",
        )
        created_ids.append(lid_f)
        async with async_session_maker() as session:
            cat = (
                await session.execute(
                    select(Category).where(Category.id == tattoo_id)
                )
            ).scalar_one()
            assert cat.slug.startswith("beauty-")
            eav_f = await _eav_map(session, lid_f)
        assert eav_f.get(BEAUTY_KIND_KEY) == "Машинки для тату"
        assert eav_f.get(BEAUTY_CONDITION_KEY) == "Новое"

        # E2E G — wig stays Beauty
        lid_g = await _create_activate(
            client,
            owner_id=owner_id,
            category_id=other_id,
            title="PERSIST beauty wig G",
            fields={
                BEAUTY_KIND_KEY: "Парики и шиньоны",
                BEAUTY_SELLER_KEY: "Магазин",
                BEAUTY_CONDITION_KEY: "Б/у",
                "contact_methods": "Только чат",
                "region": "Чуйская область",
                "city": "Бишкек",
            },
            price="5000",
        )
        created_ids.append(lid_g)
        async with async_session_maker() as session:
            eav_g = await _eav_map(session, lid_g)
        assert eav_g.get(BEAUTY_KIND_KEY) == "Парики и шиньоны"
        assert eav_g.get(BEAUTY_CONDITION_KEY) == "Б/у"

        # Edit E2E — Condition Новое → Б/у → prune via YES→NO kind
        _auth_as(owner_id)
        patch1 = await client.patch(
            f"/api/v1/listings/{lid_d}",
            json={"fields": {BEAUTY_CONDITION_KEY: "Б/у"}},
            headers={"Authorization": "Bearer test"},
        )
        assert patch1.status_code == 200, patch1.text
        async with async_session_maker() as session:
            assert (await _eav_map(session, lid_d)).get(
                BEAUTY_CONDITION_KEY
            ) == "Б/у"

        patch2 = await client.patch(
            f"/api/v1/listings/{lid_d}",
            json={
                "fields": {
                    BEAUTY_KIND_KEY: "Другие персональные устройства для красоты",
                    BEAUTY_CONDITION_KEY: "Новое",
                }
            },
            headers={"Authorization": "Bearer test"},
        )
        assert patch2.status_code == 200, patch2.text

        # Switch category to cosmetics consumable — Condition should clear when
        # client omits it; assert no package_state resurrection.
        patch3 = await client.patch(
            f"/api/v1/listings/{lid_d}",
            json={
                "category_id": cosmetics_id,
                "fields": {
                    BEAUTY_KIND_KEY: "Тональные средства",
                    BEAUTY_SELLER_KEY: "Частное лицо",
                    BEAUTY_CONDITION_KEY: "",
                    "contact_methods": "Чат + телефон",
                },
            },
            headers={"Authorization": "Bearer test"},
        )
        assert patch3.status_code == 200, patch3.text
        async with async_session_maker() as session:
            eav_pruned = await _eav_map(session, lid_d)
        assert eav_pruned.get(BEAUTY_KIND_KEY) == "Тональные средства"
        assert eav_pruned.get(BEAUTY_CONDITION_KEY, "") in {"", None}
        assert "package_state" not in eav_pruned

        # Legacy inactive
        for retired_slug in ("beauty-cosmetics", "beauty-hair"):
            async with async_session_maker() as session:
                row = (
                    await session.execute(
                        select(Category).where(Category.slug == retired_slug)
                    )
                ).scalar_one()
                assert row.is_active is False

        # Cores non-empty on modern L2 (publish gate foundation)
        async with async_session_maker() as session:
            core_count = (
                await session.execute(
                    text(
                        """
                        SELECT count(*) FROM category_core_fields
                        WHERE category_id = :cid
                        """
                    ),
                    {"cid": cosmetics_id},
                )
            ).scalar_one()
        assert int(core_count or 0) >= 5

        async with async_session_maker() as session:
            nonempty = (
                await session.execute(
                    text(
                        """
                        SELECT count(DISTINCT c.id)
                        FROM categories c
                        JOIN categories r ON r.id = c.parent_id
                        JOIN category_core_fields cf ON cf.category_id = c.id
                        WHERE r.slug = 'beauty' AND c.is_active = true
                        """
                    )
                )
            ).scalar_one()
        assert int(nonempty or 0) == 16

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
                        WHERE c.slug LIKE 'beauty%'
                          AND l.title LIKE 'PERSIST beauty%'
                        """
                    )
                )
            ).scalar_one()
            assert int(left or 0) == 0
