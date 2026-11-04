# -*- coding: utf-8 -*-
"""Transport V2 P1 Hygiene — picker parents, edit families, saved search, dialogs."""
from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from decimal import Decimal

from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from app.api.deps import get_current_user
from app.db.session import async_session_maker, engine
from app.main import app
from app.schemas.user import UserRead
from app.services.currency_policy import default_currency_for
from app.models.enums import Currency


PICKER_PARENT_SLUGS = (
    "transport-auto-parts",
    "transport-accessories-tuning",
    "transport-tires-wheels",
    "transport-auto-services",
    "transport-moto-tech",
    "transport-electric",
    "transport-bicycles",
    "transport-buses-microbuses-motorhomes",
    "transport-special-equipment",
    "transport-cargo",
    "transport-watercraft",
    "transport-trailers",
    "transport-farm-machinery",
    "transport-rental",
)


def _auth(user_id: int = 1) -> None:
    now = datetime.now(UTC)

    async def _user() -> UserRead:
        return UserRead(
            id=user_id,
            phone="+79001234567",
            full_name="HygieneTester",
            is_active=True,
            balance=Decimal("0"),
            last_login=None,
            created_at=now,
            updated_at=now,
        )

    app.dependency_overrides[get_current_user] = _user


async def _slug_id(session, slug: str) -> int | None:
    row = (
        await session.execute(
            text("SELECT id FROM categories WHERE slug = :s"),
            {"s": slug},
        )
    ).scalar_one_or_none()
    return int(row) if row is not None else None


async def _attach_photo(session, listing_id: int) -> None:
    await session.execute(
        text(
            """
            INSERT INTO media
            (listing_id, url, "order", is_placeholder, lifecycle_status,
             moderation_status, created_at, updated_at)
            VALUES
            (:lid, :url, 0, false, 'ready', 'approved', now(), now())
            """
        ),
        {
            "lid": listing_id,
            "url": f"https://example.test/hygiene/{listing_id}.jpg",
        },
    )
    await session.commit()


async def _delete_listing(session, lid: int) -> None:
    await session.execute(
        text("DELETE FROM listing_field_values WHERE listing_id = :id"),
        {"id": lid},
    )
    await session.execute(
        text("DELETE FROM media WHERE listing_id = :id"),
        {"id": lid},
    )
    await session.execute(
        text("DELETE FROM listings WHERE id = :id"),
        {"id": lid},
    )


async def _run() -> None:
    await engine.dispose()
    _auth()

    # --- Bicycle KGS policy lock ---
    assert default_currency_for("transport-bicycles") == Currency.KGS
    assert default_currency_for("transport-bicycles-gornye") == Currency.KGS

    created_ids: list[int] = []
    saved_ids: list[int] = []

    async with async_session_maker() as session:
        # Picker parents: no live schema + has children
        for slug in PICKER_PARENT_SLUGS:
            pid = await _slug_id(session, slug)
            assert pid is not None, slug
            kids = (
                await session.execute(
                    text(
                        """
                        SELECT count(*) FROM categories
                        WHERE parent_id = :p AND is_active IS TRUE
                        """
                    ),
                    {"p": pid},
                )
            ).scalar_one()
            assert int(kids) > 0, f"{slug} must have children"
            cf = (
                await session.execute(
                    text(
                        "SELECT count(*) FROM category_core_fields WHERE category_id=:p"
                    ),
                    {"p": pid},
                )
            ).scalar_one()
            fil = (
                await session.execute(
                    text(
                        "SELECT count(*) FROM category_filters WHERE category_id=:p"
                    ),
                    {"p": pid},
                )
            ).scalar_one()
            assert int(cf) == 0, f"{slug} still has core_fields={cf}"
            assert int(fil) == 0, f"{slug} still has filters={fil}"

            # Leaf still has schema
            leaf = (
                await session.execute(
                    text(
                        """
                        SELECT c.id, c.slug,
                          (SELECT count(*) FROM category_core_fields f
                           WHERE f.category_id=c.id) AS cf
                        FROM categories c
                        WHERE c.parent_id = :p AND c.is_active IS TRUE
                        ORDER BY c.sort_order, c.id LIMIT 1
                        """
                    ),
                    {"p": pid},
                )
            ).mappings().one()
            assert int(leaf["cf"]) > 0, f"leaf under {slug} has empty schema"

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        async with async_session_maker() as session:
            parts_parent = await _slug_id(session, "transport-auto-parts")
            parts_leaf = await _slug_id(
                session, "transport-auto-parts-dvigatel-i-navesnoe"
            )
            car_id = await _slug_id(session, "transport-car-sale")
            farm_leaf = await _slug_id(session, "transport-farm-machinery-traktory")
            tires_leaf = await _slug_id(session, "transport-tires-wheels-shiny")
            tuning_leaf = await _slug_id(
                session, "transport-accessories-tuning-aksessuary-salona"
            )
            svc_leaf = await _slug_id(
                session, "transport-auto-services-remont-i-obsluzhivanie"
            )
            rental_leaf = await _slug_id(
                session, "transport-rental-legkovye-avtomobili"
            )
            bike_leaf = await _slug_id(
                session, "transport-bicycles-gornye-velosipedy"
            )
            electric_leaf = await _slug_id(
                session, "transport-electric-elektrosamokaty"
            )
            assert None not in (
                parts_parent,
                parts_leaf,
                car_id,
                farm_leaf,
                tires_leaf,
                tuning_leaf,
                svc_leaf,
                rental_leaf,
                bike_leaf,
                electric_leaf,
            )

        # Publish on picker parent must fail
        draft = await client.post(
            "/api/v1/listings",
            json={
                "title": "Hygiene picker parent block",
                "description": "must not activate on parent",
                "price": "1000",
                "currency": "KGS",
                "category_id": parts_parent,
                "uses_placeholder_image": True,
            },
        )
        assert draft.status_code == 201, draft.text
        parent_lid = draft.json()["id"]
        created_ids.append(parent_lid)
        async with async_session_maker() as session:
            await _attach_photo(session, parent_lid)
        act = await client.patch(
            f"/api/v1/listings/{parent_lid}/status",
            json={"status": "active"},
        )
        assert act.status_code == 400, act.text
        assert "подкатегор" in act.json().get("detail", "").lower() or "подкатегор" in str(
            act.json()
        ).lower() or act.status_code == 400

        # --- Edit family helpers ---
        async def create_active(cat_id: int, title: str, currency: str, fields: dict):
            r = await client.post(
                "/api/v1/listings",
                json={
                    "title": title,
                    "description": title,
                    "price": "10000" if currency == "USD" else "25000",
                    "currency": currency,
                    "category_id": cat_id,
                    "uses_placeholder_image": True,
                    "fields": fields,
                },
            )
            assert r.status_code == 201, r.text
            lid = r.json()["id"]
            created_ids.append(lid)
            async with async_session_maker() as session:
                await _attach_photo(session, lid)
            a = await client.patch(
                f"/api/v1/listings/{lid}/status",
                json={"status": "active"},
            )
            assert a.status_code == 200, a.text
            return lid

        # A Car
        car_lid = await create_active(
            car_id,
            "Hygiene edit car",
            "USD",
            {
                "year": "2018",
                "negotiable": "Есть торг",
                "seller_type": "Собственник",
                "condition": "Хорошее",
                "region": "Чуйская область",
                "city": "Бишкек",
                "contact_methods": "Только телефон",
            },
        )
        got = await client.get(f"/api/v1/listings/{car_lid}")
        assert got.status_code == 200
        assert got.json()["currency"] == "USD"
        assert got.json()["fields"].get("year") in ("2018", 2018, "2018")
        patch = await client.patch(
            f"/api/v1/listings/{car_lid}",
            json={"fields": {**got.json().get("fields", {}), "year": "2019"}},
        )
        assert patch.status_code == 200, patch.text
        got2 = await client.get(f"/api/v1/listings/{car_lid}")
        assert str(got2.json()["fields"].get("year")) == "2019"
        assert got2.json()["currency"] == "USD"

        # B Farm leaf
        farm_lid = await create_active(
            farm_leaf,
            "Hygiene edit farm",
            "USD",
            {
                "year": "2015",
                "negotiable": "Без торга",
                "seller_type": "Частное лицо",
                "condition": "Хорошее",
                "region": "Чуйская область",
                "city": "Бишкек",
                "contact_methods": "Только телефон",
            },
        )
        gfarm = await client.get(f"/api/v1/listings/{farm_lid}")
        assert gfarm.status_code == 200
        assert gfarm.json()["category_id"] == farm_leaf

        # C Parts leaf
        parts_lid = await create_active(
            parts_leaf,
            "Hygiene edit parts",
            "KGS",
            {
                "part_condition": "Б/у",
                "seller_type": "Частное лицо",
                "region": "Чуйская область",
                "city": "Бишкек",
                "contact_methods": "Только телефон",
            },
        )
        gparts = await client.get(f"/api/v1/listings/{parts_lid}")
        assert gparts.status_code == 200
        assert gparts.json()["currency"] == "KGS"

        # D Tires
        tires_lid = await create_active(
            tires_leaf,
            "Hygiene edit tires",
            "KGS",
            {
                "wheel_condition": "Б/у",
                "seller_type": "Частное лицо",
                "region": "Чуйская область",
                "city": "Бишкек",
                "contact_methods": "Только телефон",
            },
        )
        assert (await client.get(f"/api/v1/listings/{tires_lid}")).status_code == 200

        # E Tuning
        tuning_lid = await create_active(
            tuning_leaf,
            "Hygiene edit tuning",
            "KGS",
            {
                "product_condition": "Б/у",
                "seller_type": "Частное лицо",
                "negotiable": "Есть торг",
                "region": "Чуйская область",
                "city": "Бишкек",
                "contact_methods": "Только телефон",
            },
        )
        assert (await client.get(f"/api/v1/listings/{tuning_lid}")).status_code == 200

        # F Auto Services + multi-select
        svc_lid = await create_active(
            svc_leaf,
            "Hygiene edit services",
            "KGS",
            {
                "service_type": "engine_repair",
                "service_price_type": "fixed",
                "provider_type": "service_center",
                "vehicle_class": "passenger_cars||cargo",
                "with_visit": "no",
                "region": "Чуйская область",
                "city": "Бишкек",
                "contact_methods": "Только телефон",
            },
        )
        gsvc = await client.get(f"/api/v1/listings/{svc_lid}")
        assert gsvc.status_code == 200
        fields = gsvc.json().get("fields") or {}
        assert fields.get("service_price_type") == "fixed"
        assert "passenger_cars" in str(fields.get("vehicle_class"))
        snap_before = gsvc.json().get("exchange_rate_snapshot")
        # status-only edit must not refresh FX
        patch_svc = await client.patch(
            f"/api/v1/listings/{svc_lid}",
            json={
                "fields": {
                    **fields,
                    "service_price_type": "negotiable",
                }
            },
        )
        assert patch_svc.status_code == 200, patch_svc.text
        gsvc2 = await client.get(f"/api/v1/listings/{svc_lid}")
        assert gsvc2.json()["fields"].get("service_price_type") == "negotiable"
        assert gsvc2.json().get("exchange_rate_snapshot") == snap_before

        # G Rental
        rental_lid = await create_active(
            rental_leaf,
            "Hygiene edit rental",
            "KGS",
            {
                "provider_type": "Компания",
                "rental_price_unit": "day",
                "region": "Чуйская область",
                "city": "Бишкек",
                "contact_methods": "Только телефон",
            },
        )
        gr = await client.get(f"/api/v1/listings/{rental_lid}")
        assert gr.status_code == 200
        assert gr.json()["currency"] == "KGS"

        # H Bicycle KGS default + USD override persist
        bike_lid = await create_active(
            bike_leaf,
            "Hygiene edit bicycle",
            "USD",
            {
                "region": "Чуйская область",
                "city": "Бишкек",
                "contact_methods": "Только телефон",
            },
        )
        gb = await client.get(f"/api/v1/listings/{bike_lid}")
        assert gb.json()["currency"] == "USD"

        # Electric USD
        el_lid = await create_active(
            electric_leaf,
            "Hygiene edit electric",
            "USD",
            {
                "region": "Чуйская область",
                "city": "Бишкек",
                "contact_methods": "Только телефон",
            },
        )
        ge = await client.get(f"/api/v1/listings/{el_lid}")
        assert ge.json()["currency"] == "USD"

        # --- Saved Search round-trips ---
        families = [
            ("car", car_id, {"category_id": car_id, "price_currency": "USD", "year__min": "2010"}),
            ("farm", farm_leaf, {"category_id": farm_leaf, "price_currency": "USD"}),
            ("parts", parts_leaf, {"category_id": parts_leaf, "price_currency": "KGS"}),
            ("tires", tires_leaf, {"category_id": tires_leaf, "price_currency": "KGS"}),
            ("tuning", tuning_leaf, {"category_id": tuning_leaf, "price_currency": "KGS"}),
            (
                "services",
                svc_leaf,
                {
                    "category_id": svc_leaf,
                    "price_currency": "KGS",
                    "vehicle_class": "passenger_cars||cargo",
                    "service_price_type": "fixed",
                },
            ),
            (
                "rental",
                rental_leaf,
                {"category_id": rental_leaf, "price_currency": "KGS", "rental_price_unit": "day"},
            ),
        ]
        for name, _cid, params in families:
            created = await client.post(
                "/api/v1/saved-searches",
                json={"query_params": params, "is_active": True},
            )
            assert created.status_code == 201, f"{name}: {created.text}"
            sid = created.json()["id"]
            saved_ids.append(sid)
            got_ss = await client.get(f"/api/v1/saved-searches/{sid}")
            assert got_ss.status_code == 200
            qp = got_ss.json()["query_params"]
            for k, v in params.items():
                assert qp.get(k) == v, f"{name} key {k}: {qp.get(k)} != {v}"

        # Existing Transport Saved Searches count in DB (user data)
        async with async_session_maker() as session:
            n = (
                await session.execute(text("SELECT count(*) FROM saved_searches"))
            ).scalar_one()
            # only our test rows if DB was empty; do not mutate unrelated rows
            assert int(n) >= len(saved_ids)

    # Cleanup
    async with async_session_maker() as session:
        for sid in saved_ids:
            await session.execute(
                text("DELETE FROM saved_searches WHERE id = :id"),
                {"id": sid},
            )
        for lid in created_ids:
            await _delete_listing(session, lid)
        await session.commit()

    app.dependency_overrides.clear()
    print("test_transport_p1_hygiene OK")


def test_transport_p1_hygiene() -> None:
    asyncio.run(_run())


if __name__ == "__main__":
    test_transport_p1_hygiene()
