# -*- coding: utf-8 -*-
"""Transport Auto Services V2 — taxonomy, schemas, search, aliases, multi-select."""
from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime
from decimal import Decimal

from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from app.api.deps import get_current_user
from app.db.session import async_session_maker, engine
from app.main import app
from app.schemas.user import UserRead
from app.seeds.auto_services_v2 import (
    AUTO_SERVICES_CORE_FIELDS_BY_SLUG,
    AUTO_SERVICES_SEARCH_FILTERS_BY_SLUG,
    DETAILING_SLUG,
    ELECTRICS_SLUG,
    GBO_SLUG,
    LEAF_IDS,
    LEAF_LABELS,
    LEAF_SLUGS,
    PARENT_ID,
    PARENT_SLUG,
    PROVIDER_TYPE_CHOICES,
    REPAIR_SLUG,
    SERVICE_PRICE_TYPE_CHOICES,
    SERVICE_TYPES_BY_SLUG,
    TIRES_SVC_SLUG,
    TOWING_SLUG,
    TUNING_SVC_SLUG,
    VEHICLE_CLASS_CHOICES,
    service_price_type_card_label,
    service_price_type_label,
)
from app.services import fx_service


def _auth_user(user_id: int = 1) -> None:
    now = datetime.now(UTC)

    async def _user() -> UserRead:
        return UserRead(
            id=user_id,
            phone="+79001234567",
            full_name="AutoSvcV2Tester",
            is_active=True,
            balance=Decimal("0"),
            last_login=None,
            created_at=now,
            updated_at=now,
        )

    app.dependency_overrides[get_current_user] = _user


def _core_keys(fields: list) -> set[str]:
    return {f[0] for f in fields}


async def _slug_id(session, slug: str) -> int:
    return int(
        (
            await session.execute(
                text("SELECT id FROM categories WHERE slug = :s"),
                {"s": slug},
            )
        ).scalar_one()
    )


async def _insert_active(session, *, title, price, cid, oid, eav):
    """Insert active fixture with Currency V2 FX fields (avoid null-snapshot debris)."""
    rate = (
        await session.execute(
            text("SELECT rate FROM fx_rates WHERE pair = 'USD_KGS' LIMIT 1")
        )
    ).scalar_one_or_none()
    if rate is None:
        rate = 89
    row = await session.execute(
        text(
            """
            INSERT INTO listings
            (title, description, price, currency, category_id, owner_id,
             status, exchange_rate_snapshot, normalized_price_kgs,
             created_at, updated_at)
            VALUES
            (:t, :d, :p, 'KGS', :cid, :oid, 'active', :rate, :p, now(), now())
            RETURNING id
            """
        ),
        {
            "t": title,
            "d": title,
            "p": price,
            "cid": cid,
            "oid": oid,
            "rate": rate,
        },
    )
    new_id = int(row.scalar_one())
    for key, val in eav.items():
        await session.execute(
            text(
                """
                INSERT INTO listing_field_values
                (listing_id, field_key, value_text, created_at, updated_at)
                VALUES (:lid, :k, :v, now(), now())
                """
            ),
            {"lid": new_id, "k": key, "v": str(val)},
        )
    return new_id


async def _run_all() -> None:
    await engine.dispose()
    assert len(LEAF_SLUGS) == 10
    assert PARENT_ID == 685
    assert set(LEAF_IDS.values()) == set(range(739, 749))

    # Labels
    assert LEAF_LABELS[REPAIR_SLUG] == "Ремонт и обслуживание"
    assert LEAF_LABELS[ELECTRICS_SLUG] == "Автоэлектрика и диагностика"
    assert LEAF_LABELS[DETAILING_SLUG] == "Мойка, химчистка и детейлинг"
    assert LEAF_LABELS[TIRES_SVC_SLUG] == "Шиномонтаж и ремонт колёс"
    assert LEAF_LABELS[TUNING_SVC_SLUG] == "Тюнинг и дооснащение"
    assert LEAF_LABELS[GBO_SLUG] == "ГБО"
    assert "Автоподбор" in LEAF_LABELS["transport-auto-services-proverka-i-oformlenie"]

    # Common schema contract
    for slug in LEAF_SLUGS:
        keys = _core_keys(AUTO_SERVICES_CORE_FIELDS_BY_SLUG[slug])
        assert "service_type" in keys
        assert "provider_type" in keys
        assert "price" in keys
        assert "service_price_type" in keys
        assert "contact_methods" in keys
        assert "vehicle_class" in keys
        assert "with_visit" in keys
        assert "negotiable" not in keys
        assert "condition" not in keys
        assert "product_condition" not in keys
        assert "vehicle_brand" not in keys
        assert "vehicle_model" not in keys
        assert "service_unit" not in keys
        assert "seller_type" not in keys
        assert len(SERVICE_TYPES_BY_SLUG[slug]) >= 5
        # service_price_type required + next to price
        spt = next(
            f for f in AUTO_SERVICES_CORE_FIELDS_BY_SLUG[slug]
            if f[0] == "service_price_type"
        )
        assert spt[1] == "Условия цены"
        assert spt[3] is True
        filt_keys = {f[0] for f in AUTO_SERVICES_SEARCH_FILTERS_BY_SLUG[slug]}
        assert "service_type" in filt_keys
        assert "provider_type" in filt_keys
        assert "vehicle_class" in filt_keys
        assert "with_visit" in filt_keys
        assert "price" in filt_keys
        assert "service_price_type" in filt_keys
        assert "sort" in filt_keys
        assert "has_photo" not in filt_keys

    assert PROVIDER_TYPE_CHOICES == (
        ("private_master", "Частный мастер"),
        ("service_center", "Автосервис"),
    )
    assert SERVICE_PRICE_TYPE_CHOICES == (
        ("fixed", "Фиксированная"),
        ("negotiable", "Договорная"),
    )
    assert service_price_type_label("fixed") == "Фиксированная"
    assert service_price_type_label("negotiable") == "Договорная"
    assert service_price_type_card_label("fixed") == "Фиксированная цена"
    assert service_price_type_card_label("negotiable") == "Цена договорная"
    assert [v for v, _ in VEHICLE_CLASS_CHOICES] == [
        "passenger_cars",
        "cargo",
        "buses",
        "moto",
        "special_equipment",
        "farm_machinery",
    ]

    # Detailing must not carry tinting / soundproofing as service types
    detailing_vals = {v for v, _ in SERVICE_TYPES_BY_SLUG[DETAILING_SLUG]}
    assert "car_tinting" not in detailing_vals
    assert "soundproofing_work" not in detailing_vals
    tuning_vals = {v for v, _ in SERVICE_TYPES_BY_SLUG[TUNING_SVC_SLUG]}
    assert "car_tinting" in tuning_vals
    assert "soundproofing_work" in tuning_vals
    assert "alarm_installation" in tuning_vals

    _auth_user()
    transport = ASGITransport(app=app)
    ids: list[int] = []

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        async with async_session_maker() as session:
            parent = (
                await session.execute(
                    text(
                        """
                        SELECT id, name, is_active FROM categories
                        WHERE slug = :s
                        """
                    ),
                    {"s": PARENT_SLUG},
                )
            ).fetchone()
            assert parent is not None
            assert int(parent[0]) == PARENT_ID
            assert parent[1] == "Автоуслуги"
            assert parent[2] is True

            parent_fields = (
                await session.execute(
                    text(
                        "SELECT COUNT(*) FROM category_core_fields WHERE category_id = :id"
                    ),
                    {"id": PARENT_ID},
                )
            ).scalar()
            assert int(parent_fields or 0) == 0
            parent_filters = (
                await session.execute(
                    text(
                        "SELECT COUNT(*) FROM category_filters WHERE category_id = :id"
                    ),
                    {"id": PARENT_ID},
                )
            ).scalar()
            assert int(parent_filters or 0) == 0

            children = (
                await session.execute(
                    text(
                        """
                        SELECT id, slug, name FROM categories
                        WHERE parent_id = :pid AND is_active = true
                        ORDER BY sort_order
                        """
                    ),
                    {"pid": PARENT_ID},
                )
            ).fetchall()
            assert len(children) == 10
            child_slugs = [r[1] for r in children]
            assert set(child_slugs) == set(LEAF_SLUGS)
            # Preferred order: Inspection (748) before GBO (747)
            assert child_slugs.index(
                "transport-auto-services-proverka-i-oformlenie"
            ) < child_slugs.index(
                "transport-auto-services-gbo-gazoballonnoe-oborudovanie"
            )

            for slug in LEAF_SLUGS:
                cid = await _slug_id(session, slug)
                assert cid == LEAF_IDS[slug]
                cores = (
                    await session.execute(
                        text(
                            """
                            SELECT field_key, is_required, field_type::text
                            FROM category_core_fields
                            WHERE category_id = :cid
                            """
                        ),
                        {"cid": cid},
                    )
                ).fetchall()
                by_key = {r[0]: r for r in cores}
                assert by_key["service_type"][1] is True
                assert by_key["provider_type"][1] is True
                assert by_key["price"][1] is True
                assert by_key["service_price_type"][1] is True
                assert by_key["vehicle_class"][1] is False
                assert by_key["with_visit"][1] is False
                assert by_key["vehicle_class"][2] == "multi_select"
                assert "negotiable" not in by_key
                assert "condition" not in by_key

                spt_opts = (
                    await session.execute(
                        text(
                            """
                            SELECT options FROM category_core_fields
                            WHERE category_id = :cid
                              AND field_key = 'service_price_type'
                            """
                        ),
                        {"cid": cid},
                    )
                ).scalar_one()
                spt_choices = spt_opts.get("choices") or spt_opts.get("values") or []
                assert [c["value"] for c in spt_choices] == ["fixed", "negotiable"]
                assert [c["label"] for c in spt_choices] == [
                    "Фиксированная",
                    "Договорная",
                ]

                st_opts = (
                    await session.execute(
                        text(
                            """
                            SELECT options FROM category_core_fields
                            WHERE category_id = :cid AND field_key = 'service_type'
                            """
                        ),
                        {"cid": cid},
                    )
                ).scalar_one()
                assert st_opts is not None
                choices = st_opts.get("choices") or st_opts.get("values") or []
                assert len(choices) == len(SERVICE_TYPES_BY_SLUG[slug])
                assert all(
                    isinstance(c, dict) and "value" in c and "label" in c
                    for c in choices
                )

                filters = (
                    await session.execute(
                        text(
                            """
                            SELECT COUNT(*) FROM category_filters
                            WHERE category_id = :cid
                            """
                        ),
                        {"cid": cid},
                    )
                ).scalar()
                assert int(filters or 0) >= 6

            # Aliases
            async def alias_target(alias: str) -> str:
                row = (
                    await session.execute(
                        text(
                            """
                            SELECT c.slug FROM category_aliases a
                            JOIN categories c ON c.id = a.category_id
                            WHERE a.alias_normalized = :a AND a.locale = 'ru'
                              AND a.is_enabled = true
                            ORDER BY a.weight DESC
                            LIMIT 1
                            """
                        ),
                        {"a": alias},
                    )
                ).fetchone()
                assert row is not None, alias
                return row[0]

            assert await alias_target("эвакуатор") == TOWING_SLUG
            assert await alias_target("нужен эвакуатор") == TOWING_SLUG
            assert (
                await alias_target("продам эвакуатор")
                == "transport-cargo-evakuatory"
            )
            assert await alias_target("автоэлектрик") == ELECTRICS_SLUG
            assert await alias_target("шиномонтаж") == TIRES_SVC_SLUG
            assert await alias_target("установка сигнализации") == TUNING_SVC_SLUG
            assert await alias_target("тонировка авто") == TUNING_SVC_SLUG
            assert await alias_target("установка гбо") == GBO_SLUG
            assert await alias_target("химчистка салона") == DETAILING_SLUG

            oid = int(
                (
                    await session.execute(
                        text("SELECT id FROM users ORDER BY id LIMIT 1")
                    )
                ).scalar_one()
            )
            repair_id = await _slug_id(session, REPAIR_SLUG)
            electrics_id = await _slug_id(session, ELECTRICS_SLUG)

            title_ms = "ASV2price electrics multi unique"
            title_engine = "ASV2price engine repair unique"
            lid_ms = await _insert_active(
                session,
                title=title_ms,
                price=1000,
                cid=electrics_id,
                oid=oid,
                eav={
                    "service_type": "auto_electrician",
                    "service_price_type": "negotiable",
                    "provider_type": "private_master",
                    "vehicle_class": "passenger_cars||cargo",
                    "with_visit": "yes",
                    "region": "Чуйская область",
                    "city": "Бишкек",
                    "contact_methods": "Телефон",
                },
            )
            ids.append(lid_ms)

            lid_engine = await _insert_active(
                session,
                title=title_engine,
                price=1500,
                cid=repair_id,
                oid=oid,
                eav={
                    "service_type": "engine_repair",
                    "service_price_type": "fixed",
                    "provider_type": "service_center",
                    "with_visit": "no",
                    "region": "Чуйская область",
                    "city": "Бишкек",
                    "contact_methods": "Телефон",
                },
            )
            ids.append(lid_engine)
            await session.commit()

        def _titles(resp) -> set[str]:
            return {i["title"] for i in resp.json()["items"]}

        # Search: service_type
        r = await client.get(
            "/api/v1/listings",
            params={
                "category_id": electrics_id,
                "attrs": json.dumps({"service_type": "auto_electrician"}),
                "limit": 50,
            },
        )
        assert r.status_code == 200
        assert title_ms in _titles(r)
        assert r.json()["total"] >= 1

        r = await client.get(
            "/api/v1/listings",
            params={
                "category_id": electrics_id,
                "attrs": json.dumps({"service_type": "computer_diagnostics"}),
                "limit": 50,
            },
        )
        assert title_ms not in _titles(r)

        # Provider
        r = await client.get(
            "/api/v1/listings",
            params={
                "category_id": electrics_id,
                "attrs": json.dumps({"provider_type": "private_master"}),
                "limit": 50,
            },
        )
        assert title_ms in _titles(r)
        r = await client.get(
            "/api/v1/listings",
            params={
                "category_id": electrics_id,
                "attrs": json.dumps({"provider_type": "service_center"}),
                "limit": 50,
            },
        )
        assert title_ms not in _titles(r)

        # with_visit
        r = await client.get(
            "/api/v1/listings",
            params={
                "category_id": electrics_id,
                "attrs": json.dumps({"with_visit": "yes"}),
                "limit": 50,
            },
        )
        assert title_ms in _titles(r)
        r = await client.get(
            "/api/v1/listings",
            params={
                "category_id": electrics_id,
                "attrs": json.dumps({"with_visit": "no"}),
                "limit": 50,
            },
        )
        assert title_ms not in _titles(r)

        # CRITICAL: multi-select overlap
        for vc in ("passenger_cars", "cargo"):
            r = await client.get(
                "/api/v1/listings",
                params={
                    "category_id": electrics_id,
                    "attrs": json.dumps({"vehicle_class": vc}),
                    "limit": 50,
                },
            )
            assert r.status_code == 200
            assert title_ms in _titles(r), vc

        r = await client.get(
            "/api/v1/listings",
            params={
                "category_id": electrics_id,
                "attrs": json.dumps({"vehicle_class": "moto"}),
                "limit": 50,
            },
        )
        assert title_ms not in _titles(r)

        # Repair service_type isolation
        r = await client.get(
            "/api/v1/listings",
            params={
                "category_id": repair_id,
                "attrs": json.dumps({"service_type": "engine_repair"}),
                "limit": 50,
            },
        )
        assert title_engine in _titles(r)
        r = await client.get(
            "/api/v1/listings",
            params={
                "category_id": repair_id,
                "attrs": json.dumps({"service_type": "gearbox_repair"}),
                "limit": 50,
            },
        )
        assert title_engine not in _titles(r)

        # service_price_type search (advanced / secondary)
        r = await client.get(
            "/api/v1/listings",
            params={
                "category_id": electrics_id,
                "attrs": json.dumps({"service_price_type": "negotiable"}),
                "limit": 50,
            },
        )
        assert r.status_code == 200
        assert title_ms in _titles(r)
        r = await client.get(
            "/api/v1/listings",
            params={
                "category_id": electrics_id,
                "attrs": json.dumps({"service_price_type": "fixed"}),
                "limit": 50,
            },
        )
        assert title_ms not in _titles(r)
        r = await client.get(
            "/api/v1/listings",
            params={
                "category_id": repair_id,
                "attrs": json.dumps({"service_price_type": "fixed"}),
                "limit": 50,
            },
        )
        assert title_engine in _titles(r)
        r = await client.get(
            "/api/v1/listings",
            params={
                "category_id": repair_id,
                "attrs": json.dumps({"service_price_type": "negotiable"}),
                "limit": 50,
            },
        )
        assert title_engine not in _titles(r)

        # Intelligence schema non-empty
        intel = await client.get(
            f"/api/v1/categories/intelligence/{electrics_id}"
        )
        assert intel.status_code == 200
        data = intel.json()
        core_keys = {f["field_key"] for f in data["core_fields"]}
        assert "service_type" in core_keys
        assert "provider_type" in core_keys
        assert "service_price_type" in core_keys
        filt_keys = {f["filter_key"] for f in data["filters"]}
        assert "service_type" in filt_keys
        assert "service_price_type" in filt_keys

        # Requiredness: Backend schema + Create intelligence (Flutter blocks publish).
        spt_intel = next(
            f for f in data["core_fields"] if f["field_key"] == "service_price_type"
        )
        assert spt_intel["is_required"] is True
        assert spt_intel["label"] == "Условия цены"

        # FX snapshot preserved when only service_price_type changes
        # (replace_from_known_fields is full replace — send complete EAV).
        async with async_session_maker() as session:
            await fx_service.ensure_fx_rate_row(session, rate=Decimal("89"))
            await fx_service.set_current_usd_kgs_rate(session, rate=Decimal("89"))
            await session.commit()
        fx_fields = {
            "service_type": "engine_repair",
            "service_price_type": "fixed",
            "provider_type": "service_center",
            "region": "Чуйская область",
            "city": "Бишкек",
            "contact_methods": "Только телефон",
        }
        draft_fx = await client.post(
            "/api/v1/listings",
            json={
                "title": "ASV2 fx status-only",
                "description": "fx regression",
                "price": "1500",
                "currency": "KGS",
                "category_id": repair_id,
                "uses_placeholder_image": True,
                "fields": fx_fields,
            },
        )
        assert draft_fx.status_code == 201, draft_fx.text
        fx_id = draft_fx.json()["id"]
        ids.append(fx_id)
        async with async_session_maker() as session:
            await session.execute(
                text(
                    """
                    INSERT INTO media (
                      listing_id, url, "order", is_placeholder,
                      lifecycle_status, moderation_status,
                      created_at, updated_at
                    ) VALUES (
                      :lid, '/media/test/asv2-fx.jpg', 0, false,
                      'ready', 'approved', now(), now()
                    )
                    """
                ),
                {"lid": fx_id},
            )
            await session.commit()
        act_fx = await client.patch(
            f"/api/v1/listings/{fx_id}/status",
            json={"status": "active"},
        )
        assert act_fx.status_code == 200, act_fx.text

        async with async_session_maker() as session:
            row_before = (
                await session.execute(
                    text(
                        """
                        SELECT price, currency::text,
                               exchange_rate_snapshot, normalized_price_kgs
                        FROM listings WHERE id = :id
                        """
                    ),
                    {"id": fx_id},
                )
            ).one()
        snap_before = Decimal(str(row_before[2]))
        norm_before = Decimal(str(row_before[3]))
        assert Decimal(str(row_before[0])) == Decimal("1500")
        assert row_before[1] == "KGS"
        assert snap_before == Decimal("89")

        async with async_session_maker() as session:
            await fx_service.set_current_usd_kgs_rate(session, rate=Decimal("99"))
            await session.commit()

        patched_fields = {**fx_fields, "service_price_type": "negotiable"}
        patch_status = await client.patch(
            f"/api/v1/listings/{fx_id}",
            json={"fields": patched_fields},
        )
        assert patch_status.status_code == 200, patch_status.text

        async with async_session_maker() as session:
            row_after = (
                await session.execute(
                    text(
                        """
                        SELECT price, currency::text,
                               exchange_rate_snapshot, normalized_price_kgs
                        FROM listings WHERE id = :id
                        """
                    ),
                    {"id": fx_id},
                )
            ).one()
            spt_after = (
                await session.execute(
                    text(
                        """
                        SELECT value_text FROM listing_field_values
                        WHERE listing_id = :id
                          AND field_key = 'service_price_type'
                        """
                    ),
                    {"id": fx_id},
                )
            ).scalar_one()
        assert spt_after == "negotiable"
        assert Decimal(str(row_after[0])) == Decimal("1500")
        assert row_after[1] == "KGS"
        assert Decimal(str(row_after[2])) == snap_before
        assert Decimal(str(row_after[3])) == norm_before

    # Cleanup
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

    app.dependency_overrides.clear()
    print("test_auto_services_v2 OK")


def test_auto_services_v2() -> None:
    asyncio.run(_run_all())
