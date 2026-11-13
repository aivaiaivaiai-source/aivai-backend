"""Materials Package A — real Create/Edit/Detail persistence + fixture hygiene."""
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
from app.seeds.materials_v2 import (
    MATERIALS_KIND_KEY,
    MATERIALS_PRICE_BASIS_KEY,
    MATERIALS_SELLER_KEY,
)


def _auth_as(user_id: int, phone: str = "+79001234567") -> None:
    now = datetime.now(UTC)

    async def _user() -> UserRead:
        return UserRead(
            id=user_id,
            phone=phone,
            full_name="MaterialsPersistTester",
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
              :lid, '/media/test/materials-e2e.jpg', 0, false,
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
            "description": f"{title} materials package A",
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
    return listing_id


@pytest.mark.asyncio
async def test_materials_create_persistence_detail_edit(client) -> None:
    await engine.dispose()
    created_ids: list[int] = []
    try:
        async with async_session_maker() as session:
            owner = (
                await session.execute(select(User).order_by(User.id).limit(1))
            ).scalar_one()
            owner_id = int(owner.id)
            fabric_id = await _cat_id(
                session, "materials-tkani-i-tekstilnoe-syre"
            )
            metal_id = await _cat_id(
                session, "materials-metally-metallicheskoe-syre"
            )
            pack_id = await _cat_id(
                session, "materials-upakovochnye-materialy"
            )
            food_id = await _cat_id(
                session, "materials-pischevoe-syre-i-ingredienty"
            )
            other_id = await _cat_id(
                session, "materials-prochee-syre-dlya-proizvodstva"
            )

        # E2E A — textile + price_basis м
        lid_a = await _create_activate(
            client,
            owner_id=owner_id,
            category_id=fabric_id,
            title="PERSIST mat cotton A",
            fields={
                MATERIALS_KIND_KEY: "Хлопковые ткани",
                MATERIALS_SELLER_KEY: "Частное лицо",
                MATERIALS_PRICE_BASIS_KEY: "м",
                "contact_methods": "Чат + телефон",
                "negotiable": "Есть торг",
                "region": "Чуйская область",
                "city": "Бишкек",
            },
            price="150",
        )
        created_ids.append(lid_a)

        detail = await client.get(
            f"/api/v1/listings/{lid_a}",
            headers={"Authorization": "Bearer test"},
        )
        assert detail.status_code == 200, detail.text
        body = detail.json()
        fields = body.get("fields") or {}
        assert fields.get(MATERIALS_KIND_KEY) == "Хлопковые ткани"
        assert fields.get(MATERIALS_PRICE_BASIS_KEY) == "м"
        assert fields.get(MATERIALS_SELLER_KEY) == "Частное лицо"
        assert "condition" not in fields
        assert str(body.get("price")) in {"150", "150.0", "150.00"}

        intel = await client.get(
            f"/api/v1/categories/intelligence/{fabric_id}",
            headers={"Authorization": "Bearer test"},
        )
        assert intel.status_code == 200, intel.text
        core = intel.json().get("core_fields") or intel.json().get("coreFields") or []
        labels = {
            (f.get("field_key") or f.get("fieldKey")): (f.get("label") or "")
            for f in core
            if isinstance(f, dict)
        }
        assert labels.get(MATERIALS_KIND_KEY) == "Товар"
        assert labels.get(MATERIALS_PRICE_BASIS_KEY) == "Цена за"
        assert labels.get(MATERIALS_SELLER_KEY) == "Продавец"
        assert "condition" not in labels

        # Detail characteristics human labels (mapper path via characteristics if present)
        chars = body.get("characteristics") or body.get("specs") or []
        if isinstance(chars, list) and chars:
            as_map = {}
            for item in chars:
                if not isinstance(item, dict):
                    continue
                lab = item.get("label") or item.get("name")
                val = item.get("value") or item.get("display_value")
                if lab:
                    as_map[str(lab)] = str(val or "")
            if as_map:
                assert as_map.get("Товар") == "Хлопковые ткани"
                assert as_map.get("Цена за") == "м"

        # E2E B — metal feedstock kg
        lid_b = await _create_activate(
            client,
            owner_id=owner_id,
            category_id=metal_id,
            title="PERSIST mat sheet B",
            fields={
                MATERIALS_KIND_KEY: "Листовой прокат",
                MATERIALS_SELLER_KEY: "Магазин",
                MATERIALS_PRICE_BASIS_KEY: "кг",
                "contact_methods": "Только чат",
                "negotiable": "Без торга",
                "region": "Чуйская область",
                "city": "Бишкек",
            },
            price="95",
        )
        created_ids.append(lid_b)

        # E2E C — packaging (no invented tara)
        lid_c = await _create_activate(
            client,
            owner_id=owner_id,
            category_id=pack_id,
            title="PERSIST mat stretch C",
            fields={
                MATERIALS_KIND_KEY: "Стретч-плёнка",
                MATERIALS_SELLER_KEY: "Другой",
                MATERIALS_PRICE_BASIS_KEY: "рулон",
                "contact_methods": "Чат + Wapp",
                "region": "Ошская область",
                "city": "Ош",
            },
        )
        created_ids.append(lid_c)

        # E2E D — industrial food ingredient stays Materials
        lid_d = await _create_activate(
            client,
            owner_id=owner_id,
            category_id=food_id,
            title="PERSIST mat gelatin D",
            fields={
                MATERIALS_KIND_KEY: "Желатин",
                MATERIALS_SELLER_KEY: "Частное лицо",
                MATERIALS_PRICE_BASIS_KEY: "кг",
                "contact_methods": "Только телефон",
                "region": "Чуйская область",
                "city": "Бишкек",
            },
        )
        created_ids.append(lid_d)
        async with async_session_maker() as session:
            cat = (
                await session.execute(select(Category).where(Category.id == food_id))
            ).scalar_one()
            assert cat.slug.startswith("materials-")

        # E2E E — scrap/reclaimed NO Condition
        lid_e = await _create_activate(
            client,
            owner_id=owner_id,
            category_id=other_id,
            title="PERSIST mat scrap E",
            fields={
                MATERIALS_KIND_KEY: "Вторсырьё",
                MATERIALS_SELLER_KEY: "Частное лицо",
                "contact_methods": "Чат + Тел. + Wapp",
                "region": "Чуйская область",
                "city": "Бишкек",
            },
        )
        created_ids.append(lid_e)
        async with async_session_maker() as session:
            eav_e = await _eav_map(session, lid_e)
        assert "condition" not in eav_e
        assert MATERIALS_PRICE_BASIS_KEY not in eav_e

        # Edit E2E — change price_basis empty→кг→тонна→cleared
        _auth_as(owner_id)
        patch1 = await client.patch(
            f"/api/v1/listings/{lid_e}",
            json={"fields": {MATERIALS_PRICE_BASIS_KEY: "кг"}},
            headers={"Authorization": "Bearer test"},
        )
        assert patch1.status_code == 200, patch1.text
        async with async_session_maker() as session:
            assert (await _eav_map(session, lid_e)).get(
                MATERIALS_PRICE_BASIS_KEY
            ) == "кг"

        patch2 = await client.patch(
            f"/api/v1/listings/{lid_e}",
            json={"fields": {MATERIALS_PRICE_BASIS_KEY: "тонна"}},
            headers={"Authorization": "Bearer test"},
        )
        assert patch2.status_code == 200, patch2.text
        async with async_session_maker() as session:
            assert (await _eav_map(session, lid_e)).get(
                MATERIALS_PRICE_BASIS_KEY
            ) == "тонна"

        patch3 = await client.patch(
            f"/api/v1/listings/{lid_e}",
            json={"fields": {MATERIALS_PRICE_BASIS_KEY: ""}},
            headers={"Authorization": "Bearer test"},
        )
        assert patch3.status_code == 200, patch3.text
        async with async_session_maker() as session:
            eav_cleared = await _eav_map(session, lid_e)
        assert eav_cleared.get(MATERIALS_PRICE_BASIS_KEY, "") in {"", None}

        # Publish gate — empty schema leaf (retired) must not activate with cores missing
        async with async_session_maker() as session:
            retired = await _cat_id(session, "materials-textile")
            row = (
                await session.execute(select(Category).where(Category.id == retired))
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
                        WHERE c.slug LIKE 'materials-%'
                          AND l.title LIKE 'PERSIST mat%'
                        """
                    )
                )
            ).scalar_one()
            assert int(left or 0) == 0
