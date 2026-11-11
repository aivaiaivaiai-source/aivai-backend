"""CREATE_PERSISTENCE + CREATE_SEARCH_E2E_PARITY across Backend-SoT domains.

These tests MUST use the production Create/PATCH listing API payload contract.
ORM-injected ListingFieldValue rows are forbidden here.
"""
from __future__ import annotations

import json
import re
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
from app.seeds.animals_v2 import ANIMALS_GENDER_KEY, ANIMALS_KIND_KEY, ANIMALS_SELLER_KEY


def _auth_as(user_id: int, phone: str = "+79001234567") -> None:
    now = datetime.now(UTC)

    async def _user() -> UserRead:
        return UserRead(
            id=user_id,
            phone=phone,
            full_name="PersistParityTester",
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
              :lid, '/media/test/persist-e2e.jpg', 0, false,
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


def _first_option_value(options_text: str | None) -> str | None:
    if not options_text:
        return None
    m = re.search(r'"value"\s*:\s*"([^"]+)"', options_text)
    return m.group(1) if m else None


async def _create_activate_search(
    client,
    *,
    owner_id: int,
    category_id: int,
    title: str,
    fields: dict[str, str],
    search_attrs: dict[str, str],
    wrong_attrs: dict[str, str] | None = None,
    price: str | None = "1500",
) -> int:
    _auth_as(owner_id)
    payload: dict = {
        "title": title,
        "description": f"{title} persistence boundary",
        "currency": "KGS",
        "category_id": category_id,
        "status": "draft",
        "fields": fields,
    }
    if price is not None:
        payload["price"] = price
    created = await client.post(
        "/api/v1/listings",
        json=payload,
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
        if key in ("price", "currency", "price_currency"):
            continue
        assert eav.get(key) == value, (key, eav, fields)

    found = await client.get(
        "/api/v1/listings",
        params={
            "category_id": category_id,
            "attrs": json.dumps(search_attrs, ensure_ascii=False),
            "limit": 40,
        },
    )
    assert found.status_code == 200, found.text
    ids = [int(i["id"]) for i in found.json().get("items") or []]
    assert listing_id in ids, (search_attrs, found.json())

    if wrong_attrs:
        miss = await client.get(
            "/api/v1/listings",
            params={
                "category_id": category_id,
                "attrs": json.dumps(wrong_attrs, ensure_ascii=False),
                "limit": 40,
            },
        )
        assert miss.status_code == 200, miss.text
        miss_ids = [int(i["id"]) for i in miss.json().get("items") or []]
        assert listing_id not in miss_ids, (wrong_attrs, miss.json())

    return listing_id


@pytest.mark.asyncio
async def test_animals_create_persistence_and_search_e2e(client) -> None:
    """CREATE_SEARCH_E2E_PARITY — Animals via production Create API."""
    await engine.dispose()
    created_ids: list[int] = []
    try:
        async with async_session_maker() as session:
            owner = (
                await session.execute(select(User).order_by(User.id).limit(1))
            ).scalar_one()
            owner_id = int(owner.id)
            sheep_id = await _cat_id(session, "animals-ovtsy-barany-i-kozy")
            dogs_id = await _cat_id(session, "animals-sobaki")

        fields = {
            ANIMALS_KIND_KEY: "Овцы",
            ANIMALS_SELLER_KEY: "Частное лицо",
            "contact_methods": "Только чат",
            "negotiable": "Есть торг",
            "region": "Ошская область",
            "city": "Ош",
        }
        lid = await _create_activate_search(
            client,
            owner_id=owner_id,
            category_id=sheep_id,
            title="PERSIST animals sheep e2e",
            fields=fields,
            search_attrs={
                ANIMALS_KIND_KEY: "Овцы",
                ANIMALS_SELLER_KEY: "Частное лицо",
            },
            wrong_attrs={ANIMALS_KIND_KEY: "Бараны"},
        )
        created_ids.append(lid)

        dog_fields = {
            ANIMALS_KIND_KEY: "Собаки",
            ANIMALS_SELLER_KEY: "Частное лицо",
            ANIMALS_GENDER_KEY: "Самец",
            "contact_methods": "Только чат",
            "region": "Чуйская область",
            "city": "Бишкек",
        }
        lid2 = await _create_activate_search(
            client,
            owner_id=owner_id,
            category_id=dogs_id,
            title="PERSIST animals dog male e2e",
            fields=dog_fields,
            search_attrs={
                ANIMALS_KIND_KEY: "Собаки",
                ANIMALS_GENDER_KEY: "Самец",
            },
            wrong_attrs={
                ANIMALS_KIND_KEY: "Собаки",
                ANIMALS_GENDER_KEY: "Самка",
            },
        )
        created_ids.append(lid2)

        bare = await client.post(
            "/api/v1/listings",
            json={
                "title": "PERSIST animals bare fail",
                "description": "missing kind",
                "price": "100",
                "currency": "KGS",
                "category_id": sheep_id,
                "status": "draft",
                "fields": {"city": "Ош", "region": "Ошская область"},
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
            row = (
                await session.execute(select(Listing).where(Listing.id == 2327))
            ).scalar_one_or_none()
            if row is not None:
                eav_2327 = await _eav_map(session, 2327)
                assert ANIMALS_KIND_KEY not in eav_2327
                assert ANIMALS_SELLER_KEY not in eav_2327
        cat_only = await client.get(
            "/api/v1/listings",
            params={"category_id": sheep_id, "limit": 50},
        )
        assert cat_only.status_code == 200
        cat_ids = [int(i["id"]) for i in cat_only.json().get("items") or []]
        if 2327 in cat_ids:
            kind_q = await client.get(
                "/api/v1/listings",
                params={
                    "category_id": sheep_id,
                    "attrs": json.dumps(
                        {ANIMALS_KIND_KEY: "Овцы"}, ensure_ascii=False
                    ),
                    "limit": 50,
                },
            )
            kind_ids = [int(i["id"]) for i in kind_q.json().get("items") or []]
            assert 2327 not in kind_ids
    finally:
        async with async_session_maker() as session:
            await _cleanup(session, created_ids)


@pytest.mark.asyncio
async def test_cross_domain_create_persistence_smoke(client) -> None:
    """One production-Create persistence smoke per closed Backend-SoT domain."""
    await engine.dispose()
    created_ids: list[int] = []
    cases = [
        ("food-agri-ovoschi-i-frukty", "food_kind", False),
        ("kids-detskaya-odezhda", "kids_kind", False),
        ("fashion-zhenskaya-odezhda", "fashion_kind", False),
        ("electronics-smartfony-i-telefony", "electronics_kind", False),
        ("home-garden-mebel-dlya-doma-divany", "seller_type", False),
        ("repair-construction-stroitelnye-materialy", "repair_kind", False),
        ("services-elektrika", "service_kind", True),
    ]
    try:
        async with async_session_maker() as session:
            owner = (
                await session.execute(select(User).order_by(User.id).limit(1))
            ).scalar_one()
            owner_id = int(owner.id)

            prepared: list[tuple[int, dict[str, str], dict[str, str], str | None, str]] = []
            for slug, search_key, services_negotiated in cases:
                cat = (
                    await session.execute(
                        select(Category).where(Category.slug == slug)
                    )
                ).scalar_one()
                core_rows = (
                    await session.execute(
                        text(
                            """
                            SELECT field_key, is_required, options::text
                            FROM category_core_fields
                            WHERE category_id = :cid
                            ORDER BY sort_order
                            """
                        ),
                        {"cid": cat.id},
                    )
                ).mappings().all()
                by_key = {r["field_key"]: r for r in core_rows}
                fields: dict[str, str] = {
                    "city": "Бишкек",
                    "region": "Чуйская область",
                }
                # Fill every required non-price core with first option / safe default.
                for r in core_rows:
                    key = r["field_key"]
                    if key in ("price", "currency", "price_currency"):
                        continue
                    if not r["is_required"] and key != search_key:
                        continue
                    if key in fields:
                        continue
                    first = _first_option_value(r["options"])
                    if first:
                        fields[key] = first
                    elif key == "contact_methods":
                        fields[key] = "Только чат"
                    elif key == "seller_type":
                        fields[key] = "Частное лицо"
                    elif key == "executor":
                        fields[key] = "Частный мастер"
                # Ensure search key present.
                if search_key not in fields:
                    first = _first_option_value(
                        (by_key.get(search_key) or {}).get("options")
                    )
                    assert first, (slug, search_key)
                    fields[search_key] = first
                if services_negotiated:
                    fields["negotiable"] = "По договорённости"
                    price = None
                else:
                    price = "1500"
                prepared.append(
                    (
                        int(cat.id),
                        fields,
                        {search_key: fields[search_key]},
                        price,
                        slug,
                    )
                )

        for category_id, fields, search_attrs, price, slug in prepared:
            lid = await _create_activate_search(
                client,
                owner_id=owner_id,
                category_id=category_id,
                title=f"PERSIST smoke {slug}",
                fields=fields,
                search_attrs=search_attrs,
                price=price,
            )
            created_ids.append(lid)
    finally:
        async with async_session_maker() as session:
            await _cleanup(session, created_ids)
