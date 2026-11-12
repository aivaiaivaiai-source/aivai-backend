"""Medical Package A — real Create/Edit/Detail persistence + legacy incomplete safety."""
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
from app.seeds.loader import CategorySeedLoader
from app.seeds.medical_v2 import (
    MED_CONDITION_KEY,
    MED_KIND_KEY,
    MED_SELLER_KEY,
)

LEGACY_INCOMPLETE_LISTING_ID = 3154


def _auth_as(user_id: int, phone: str = "+79001234567") -> None:
    now = datetime.now(UTC)

    async def _user() -> UserRead:
        return UserRead(
            id=user_id,
            phone=phone,
            full_name="MedicalPersistTester",
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
              :lid, '/media/test/medical-e2e.jpg', 0, false,
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


async def _listing_fingerprint(session, listing_id: int) -> dict:
    row = (
        await session.execute(select(Listing).where(Listing.id == listing_id))
    ).scalar_one_or_none()
    if row is None:
        return {"exists": False}
    eav = await _eav_map(session, listing_id)
    return {
        "exists": True,
        "id": int(row.id),
        "title": row.title,
        "status": str(row.status.value if hasattr(row.status, "value") else row.status),
        "price": str(row.price),
        "currency": row.currency,
        "owner_id": int(row.owner_id),
        "category_id": int(row.category_id),
        "description": row.description,
        "eav": eav,
    }


async def _cleanup(session, listing_ids: list[int]) -> None:
    ids = [i for i in listing_ids if i != LEGACY_INCOMPLETE_LISTING_ID]
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
    price: str = "4500",
) -> int:
    _auth_as(owner_id)
    created = await client.post(
        "/api/v1/listings",
        json={
            "title": title,
            "description": f"{title} medical package A",
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
async def test_medical_legacy_incomplete_class_preserved_on_schema_reseed() -> None:
    """Class-based: incomplete Medical listing is not backfilled by Package A seed."""
    await engine.dispose()
    created_ids: list[int] = []
    try:
        async with async_session_maker() as session:
            owner = (
                await session.execute(select(User).order_by(User.id).limit(1))
            ).scalar_one()
            cat_id = await _cat_id(session, "medical-ortopedicheskie-tovary")
            row = await session.execute(
                text(
                    """
                    INSERT INTO listings (
                      owner_id, category_id, title, description, price, currency,
                      status, created_at, updated_at
                    ) VALUES (
                      :oid, :cid, :title, :descr, 199.00, 'KGS',
                      'active', now(), now()
                    )
                    RETURNING id
                    """
                ),
                {
                    "oid": int(owner.id),
                    "cid": cat_id,
                    "title": "LEGACY_INCOMPLETE medical fixture",
                    "descr": "pre package a incomplete",
                },
            )
            lid = int(row.scalar_one())
            created_ids.append(lid)
            for key, val in (("region", "Чуйская область"), ("city", "Бишкек")):
                await session.execute(
                    text(
                        """
                        INSERT INTO listing_field_values (
                          listing_id, field_key, value_text, created_at, updated_at
                        ) VALUES (:lid, :key, :val, now(), now())
                        """
                    ),
                    {"lid": lid, "key": key, "val": val},
                )
            await session.commit()
            before = await _listing_fingerprint(session, lid)

        async with async_session_maker() as session:
            loader = CategorySeedLoader(session)
            await loader._seed_medical_v2_fields()
            await session.commit()

        async with async_session_maker() as session:
            after = await _listing_fingerprint(session, lid)
        assert after == before
        assert MED_KIND_KEY not in after["eav"]
        assert MED_SELLER_KEY not in after["eav"]
        assert MED_CONDITION_KEY not in after["eav"]
        assert after["eav"] == {"region": "Чуйская область", "city": "Бишкек"}
    finally:
        async with async_session_maker() as session:
            await _cleanup(session, created_ids)


@pytest.mark.asyncio
async def test_medical_create_persistence_detail_and_3154_boundary(client) -> None:
    await engine.dispose()
    created_ids: list[int] = []
    forensic_existed = False
    forensic_before: dict = {}
    try:
        async with async_session_maker() as session:
            owner = (
                await session.execute(select(User).order_by(User.id).limit(1))
            ).scalar_one()
            owner_id = int(owner.id)
            devices_id = await _cat_id(session, "medical-meditsinskie-pribory")
            consumables_id = await _cat_id(
                session, "medical-rashodnye-med-materialy"
            )
            clothing_id = await _cat_id(session, "medical-meditsinskaya-odezhda")
            optics_id = await _cat_id(
                session, "medical-optika-i-tovary-dlya-zreniya"
            )
            diabetes_id = await _cat_id(session, "medical-tovary-dlya-diabetikov")
            forensic_before = await _listing_fingerprint(
                session, LEGACY_INCOMPLETE_LISTING_ID
            )
            forensic_existed = bool(forensic_before.get("exists"))

        # E2E A — durable device (Condition YES)
        lid_a = await _create_activate(
            client,
            owner_id=owner_id,
            category_id=devices_id,
            title="PERSIST med tonometr A",
            fields={
                MED_KIND_KEY: "Тонометры",
                MED_SELLER_KEY: "Частное лицо",
                MED_CONDITION_KEY: "Б/у",
                "contact_methods": "Чат + телефон",
                "negotiable": "Есть торг",
                "region": "Чуйская область",
                "city": "Бишкек",
            },
        )
        created_ids.append(lid_a)

        detail = await client.get(
            f"/api/v1/listings/{lid_a}",
            headers={"Authorization": "Bearer test"},
        )
        assert detail.status_code == 200, detail.text
        fields = detail.json().get("fields") or {}
        assert fields.get(MED_KIND_KEY) == "Тонометры"
        assert fields.get(MED_SELLER_KEY) == "Частное лицо"
        assert fields.get(MED_CONDITION_KEY) == "Б/у"
        assert fields.get("contact_methods") == "Чат + телефон"
        assert fields.get("negotiable") == "Есть торг"

        intel = await client.get(
            f"/api/v1/categories/intelligence/{devices_id}",
            headers={"Authorization": "Bearer test"},
        )
        assert intel.status_code == 200, intel.text
        core = intel.json().get("core_fields") or intel.json().get("coreFields") or []
        labels = {
            (f.get("field_key") or f.get("fieldKey")): (f.get("label") or "")
            for f in core
            if isinstance(f, dict)
        }
        assert labels.get(MED_KIND_KEY) == "Товар"
        assert labels.get(MED_SELLER_KEY) == "Продавец"
        assert labels.get(MED_CONDITION_KEY) == "Состояние"
        assert labels.get("negotiable") == "Торг"
        assert labels.get("contact_methods") == "Способы связи"

        # E2E B — consumable Condition NO
        lid_b = await _create_activate(
            client,
            owner_id=owner_id,
            category_id=consumables_id,
            title="PERSIST med syringes B",
            fields={
                MED_KIND_KEY: "Шприцы",
                MED_SELLER_KEY: "Магазин",
                "contact_methods": "Только чат",
                "negotiable": "Без торга",
                "region": "Чуйская область",
                "city": "Бишкек",
            },
        )
        created_ids.append(lid_b)
        async with async_session_maker() as session:
            eav_b = await _eav_map(session, lid_b)
        assert MED_CONDITION_KEY not in eav_b

        # E2E C — medical clothing Condition ABSENT
        lid_c = await _create_activate(
            client,
            owner_id=owner_id,
            category_id=clothing_id,
            title="PERSIST med gown C",
            fields={
                MED_KIND_KEY: "Медицинские халаты",
                MED_SELLER_KEY: "Другой",
                "contact_methods": "Чат + Wapp",
                "region": "Ошская область",
                "city": "Ош",
            },
        )
        created_ids.append(lid_c)
        async with async_session_maker() as session:
            eav_c = await _eav_map(session, lid_c)
        assert MED_CONDITION_KEY not in eav_c

        # E2E D — optics YES + NO
        lid_d1 = await _create_activate(
            client,
            owner_id=owner_id,
            category_id=optics_id,
            title="PERSIST med frames D1",
            fields={
                MED_KIND_KEY: "Оправы",
                MED_SELLER_KEY: "Частное лицо",
                MED_CONDITION_KEY: "Новое",
                "contact_methods": "Только телефон",
                "region": "Чуйская область",
                "city": "Бишкек",
            },
        )
        created_ids.append(lid_d1)
        lid_d2 = await _create_activate(
            client,
            owner_id=owner_id,
            category_id=optics_id,
            title="PERSIST med lenses D2",
            fields={
                MED_KIND_KEY: "Контактные линзы",
                MED_SELLER_KEY: "Магазин",
                "contact_methods": "Чат + Тел. + Wapp",
                "region": "Чуйская область",
                "city": "Бишкек",
            },
        )
        created_ids.append(lid_d2)
        async with async_session_maker() as session:
            eav_d2 = await _eav_map(session, lid_d2)
        assert MED_CONDITION_KEY not in eav_d2

        # E2E E — medical-purpose electronic device stays Medical
        lid_e = await _create_activate(
            client,
            owner_id=owner_id,
            category_id=diabetes_id,
            title="PERSIST med glucometer E",
            fields={
                MED_KIND_KEY: "Глюкометры",
                MED_SELLER_KEY: "Частное лицо",
                MED_CONDITION_KEY: "Б/у",
                "contact_methods": "Телефон + Wapp",
                "region": "Чуйская область",
                "city": "Бишкек",
            },
        )
        created_ids.append(lid_e)
        async with async_session_maker() as session:
            cat = (
                await session.execute(
                    select(Category).where(Category.id == diabetes_id)
                )
            ).scalar_one()
            assert cat.slug == "medical-tovary-dlya-diabetikov"
            eav_e = await _eav_map(session, lid_e)
        assert eav_e[MED_KIND_KEY] == "Глюкометры"
        assert "brand" not in eav_e
        assert "electronics_brand" not in eav_e

        # Publish gate — geo-only blocked
        bare = await client.post(
            "/api/v1/listings",
            json={
                "title": "PERSIST med bare fail",
                "description": "missing kind",
                "price": "100",
                "currency": "KGS",
                "category_id": devices_id,
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
                    MED_KIND_KEY: "Тонометры",
                    MED_SELLER_KEY: "Магазин",
                    MED_CONDITION_KEY: "Новое",
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
        assert eav_a[MED_CONDITION_KEY] == "Новое"
        assert eav_a[MED_SELLER_KEY] == "Магазин"

        # Production LEGACY_INCOMPLETE 3154 untouched
        if forensic_existed:
            async with async_session_maker() as session:
                after = await _listing_fingerprint(
                    session, LEGACY_INCOMPLETE_LISTING_ID
                )
            # Compare identity fields + EAV; updated_at may move only if mutated —
            # fingerprint includes description/price/status/eav which must match.
            for key in (
                "id",
                "title",
                "status",
                "price",
                "currency",
                "owner_id",
                "category_id",
                "description",
                "eav",
            ):
                assert after.get(key) == forensic_before.get(key), key
            assert MED_KIND_KEY not in after["eav"]
            assert after["eav"] == {"region": "Чуйская область", "city": "Бишкек"}

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
            if forensic_existed:
                still = (
                    await session.execute(
                        select(Listing.id).where(
                            Listing.id == LEGACY_INCOMPLETE_LISTING_ID
                        )
                    )
                ).scalar_one_or_none()
                assert still == LEGACY_INCOMPLETE_LISTING_ID
