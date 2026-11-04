"""Brand canonicalization + execution regression."""
from __future__ import annotations

import asyncio

from sqlalchemy import text

from app.db.session import async_session_maker, engine
from app.models.category_enums import VehicleCatalogContext, VehicleExecution
from app.repositories.vehicle_repository import (
    VehicleBrandRepository,
    VehicleModelRepository,
)
from app.seeds.vehicle_data import MODEL_ALIASES
from app.services.vehicle_catalog_service import VehicleCatalogService


def _catalog(session) -> VehicleCatalogService:
    return VehicleCatalogService(
        VehicleBrandRepository(session),
        VehicleModelRepository(session),
    )


def test_no_duplicate_hyundai_toyota_mercedes_bmw_in_picker() -> None:
    async def _run() -> None:
        async with async_session_maker() as session:
            svc = _catalog(session)
            for ctx in (
                VehicleCatalogContext.car_sale,
                VehicleCatalogContext.passenger_parts,
            ):
                brands = await svc.list_brands(catalog_context=ctx)
                names = [b.name for b in brands]
                for marque in ("Hyundai", "Toyota", "Mercedes-Benz", "BMW"):
                    assert names.count(marque) == 1, (
                        f"{marque} appears {names.count(marque)} times in {ctx}"
                    )
                slugs = {b.slug for b in brands}
                for bad in ("солярис", "приус", "гелик", "x3"):
                    assert bad not in slugs
            # Identity is slug
            hyundai = next(
                b
                for b in await svc.list_brands(
                    catalog_context=VehicleCatalogContext.car_sale
                )
                if b.name == "Hyundai"
            )
            assert hyundai.slug == "hyundai"
            assert hyundai.id > 0
        await engine.dispose()

    asyncio.run(_run())


def test_hyundai_gaz_execution_contexts() -> None:
    async def _run() -> None:
        async with async_session_maker() as session:
            svc = _catalog(session)
            car = await svc.list_models_for_brand(
                "hyundai", catalog_context=VehicleCatalogContext.car_sale
            )
            assert "porter" not in {m.slug for m in car}
            assert any(m.slug in ("solaris", "sonata", "elantra") for m in car)

            passenger = await svc.list_models_for_brand(
                "hyundai",
                catalog_context=VehicleCatalogContext.passenger_parts,
            )
            assert "porter" not in {m.slug for m in passenger}

            cargo = await svc.list_models_for_brand(
                "hyundai", catalog_context=VehicleCatalogContext.cargo_parts
            )
            assert "porter" in {m.slug for m in cargo}
            porter = next(m for m in cargo if m.slug == "porter")
            assert porter.allowed_executions == [VehicleExecution.cargo]

            gaz_car = await svc.list_models_for_brand(
                "gaz", catalog_context=VehicleCatalogContext.car_sale
            )
            assert "gazelle" not in {m.slug for m in gaz_car}
            assert "sobol" not in {m.slug for m in gaz_car}

            gaz_pass = await svc.list_models_for_brand(
                "gaz",
                catalog_context=VehicleCatalogContext.passenger_parts,
            )
            assert "gazelle" not in {m.slug for m in gaz_pass}

            gaz_cargo = await svc.list_models_for_brand(
                "gaz", catalog_context=VehicleCatalogContext.cargo_parts
            )
            assert {"gazelle", "sobol"} <= {m.slug for m in gaz_cargo}
        await engine.dispose()

    asyncio.run(_run())


def test_corrupt_brands_disabled_and_aliases_exist() -> None:
    async def _run() -> None:
        async with async_session_maker() as session:
            for slug in ("солярис", "гелик", "приус", "x3", "vw"):
                enabled = (
                    await session.execute(
                        text(
                            "SELECT is_enabled FROM vehicle_brands WHERE slug = :s"
                        ),
                        {"s": slug},
                    )
                ).scalar()
                assert enabled is False, f"{slug} should be disabled"

            for alias, brand_slug, model_slug in (
                ("солярис", "hyundai", "solaris"),
                ("гелик", "mercedes-benz", "g-class"),
                ("приус", "toyota", "prius"),
            ):
                row = (
                    await session.execute(
                        text(
                            """
                            SELECT a.is_enabled, b.slug, m.slug
                            FROM vehicle_aliases a
                            JOIN vehicle_brands b ON b.id = a.brand_id
                            LEFT JOIN vehicle_models m ON m.id = a.model_id
                            WHERE a.alias_compact = :c AND a.locale = 'ru'
                            """
                        ),
                        {"c": alias.replace(" ", "").lower()},
                    )
                ).first()
                assert row is not None, f"alias missing for {alias}"
                assert row[0] is True
                assert row[1] == brand_slug
                assert row[2] == model_slug

            # Canonical Porter still has policy
            policy = (
                await session.execute(
                    text(
                        """
                        SELECT COUNT(*) FROM vehicle_model_allowed_executions a
                        JOIN vehicle_models m ON m.id = a.model_id
                        JOIN vehicle_brands b ON b.id = m.brand_id
                        WHERE b.slug = 'hyundai' AND m.slug = 'porter'
                          AND a.execution = 'cargo'
                        """
                    )
                )
            ).scalar_one()
            assert policy == 1
        await engine.dispose()

    asyncio.run(_run())


def test_model_aliases_are_forbidden_as_brand_slugs() -> None:
    from app.seeds.loader import _FORBIDDEN_BRAND_SLUGS
    from app.seeds.mobile_vehicle_catalog import MOBILE_VEHICLE_BRANDS
    from app.seeds.vehicle_data import BRANDS

    for alias, _b, _m in MODEL_ALIASES:
        assert alias.strip().lower() in _FORBIDDEN_BRAND_SLUGS

    for slug, *_rest in BRANDS:
        assert slug.strip().lower() not in _FORBIDDEN_BRAND_SLUGS
    for slug, _name in MOBILE_VEHICLE_BRANDS:
        assert slug.strip().lower() not in _FORBIDDEN_BRAND_SLUGS


def test_http_hyundai_contexts_after_canon() -> None:
    import json
    import urllib.request

    base = "http://127.0.0.1:8000/api/v1/vehicles/brands"
    brands = json.loads(
        urllib.request.urlopen(
            f"{base}?catalog_context=car_sale", timeout=15
        ).read().decode()
    )
    hyundai = [b for b in brands if b["name"] == "Hyundai"]
    assert len(hyundai) == 1
    assert hyundai[0]["slug"] == "hyundai"
    assert not any(b["slug"] == "солярис" for b in brands)

    for ctx, expect_porter in (
        ("car_sale", False),
        ("passenger_parts", False),
        ("cargo_parts", True),
    ):
        models = json.loads(
            urllib.request.urlopen(
                f"{base}/hyundai/models?catalog_context={ctx}", timeout=15
            ).read().decode()
        )
        has = any(m["slug"] == "porter" for m in models)
        assert has is expect_porter, f"ctx={ctx} porter={has}"
