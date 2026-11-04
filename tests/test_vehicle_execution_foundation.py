"""Vehicle Execution Foundation V2 — catalog, listing execution, resolver."""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import text

from app.db.session import async_session_maker, engine
from app.models.category_enums import VehicleCatalogContext, VehicleExecution
from app.models.enums import Currency, ListingStatus
from app.repositories.vehicle_repository import (
    VehicleBrandRepository,
    VehicleModelRepository,
)
from app.schemas.listing import ListingCreate, ListingRead
from app.services.vehicle_catalog_service import VehicleCatalogService
from app.services.vehicle_execution import (
    APPROVED_MODEL_EXECUTIONS,
    detect_execution_from_text,
    text_mentions_execution_sensitive_subject,
)
from app.seeds.parts_passenger_cars import build_passenger_cars_catalog
from app.seeds.transport_v2_1 import PARTS_VEHICLE_APPLICABILITY_OPTIONS


def _catalog(session) -> VehicleCatalogService:
    return VehicleCatalogService(
        VehicleBrandRepository(session),
        VehicleModelRepository(session),
    )


_DUAL = [
    ("mercedes-benz", "sprinter"),
    ("gaz", "gazelle"),
    ("gaz", "sobol"),
    ("ford", "transit"),
    ("toyota", "hiace"),
]
_CARGO_ONLY = [
    ("hyundai", "porter"),
    ("kia", "bongo"),
    ("iveco", "daily"),
    ("fiat", "ducato"),
    ("citroen", "jumper"),
    ("uaz", "profi"),
]


def test_approved_allowed_executions_constants() -> None:
    for key in _DUAL:
        assert APPROVED_MODEL_EXECUTIONS[key] == (
            VehicleExecution.cargo,
            VehicleExecution.passenger,
        )
    for key in _CARGO_ONLY:
        assert APPROVED_MODEL_EXECUTIONS[key] == (VehicleExecution.cargo,)


def test_detect_execution_never_guesses_bare_model() -> None:
    assert detect_execution_from_text("Sprinter") is None
    assert detect_execution_from_text("Gazelle") is None
    assert detect_execution_from_text("продаю грузовой Sprinter") == VehicleExecution.cargo
    assert detect_execution_from_text("пассажирский Transit") == VehicleExecution.passenger
    assert text_mentions_execution_sensitive_subject("Sprinter")
    assert not text_mentions_execution_sensitive_subject("Camry")


def test_listing_execution_single_value_semantics() -> None:
    body = ListingCreate(
        title="Sprinter cargo",
        price=Decimal("1000"),
        vehicle_execution=VehicleExecution.cargo,
    )
    assert body.vehicle_execution == VehicleExecution.cargo
    assert not isinstance(body.vehicle_execution, list)

    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    read = ListingRead(
        id=1,
        title="x",
        description=None,
        price=Decimal("1"),
        currency=Currency.KGS,
        status=ListingStatus.draft,
        owner_id=1,
        created_at=now,
        updated_at=now,
        vehicle_execution=VehicleExecution.passenger,
    )
    assert read.vehicle_execution == VehicleExecution.passenger


def test_step1_and_parts_regression_still_pass() -> None:
    values = [v for v, _ in PARTS_VEHICLE_APPLICABILITY_OPTIONS]
    assert "passenger_cars" in values
    assert "cargo" in values
    cat = build_passenger_cars_catalog()
    assert cat["applicability"] == "passenger_cars"
    assert len(cat["sections"]) == 15


def test_vehicle_execution_foundation_db() -> None:
    """One asyncio loop for all DB checks (avoids Win/asyncpg pool flake)."""

    async def _run() -> None:
        async with async_session_maker() as session:
            svc = _catalog(session)

            for brand_slug, model_slug in _DUAL + _CARGO_ONLY:
                row = (
                    await session.execute(
                        text(
                            """
                            SELECT m.id, array_agg(a.execution::text ORDER BY a.execution)
                            FROM vehicle_models m
                            JOIN vehicle_brands b ON b.id = m.brand_id
                            JOIN vehicle_model_allowed_executions a ON a.model_id = m.id
                            WHERE b.slug = :bs AND m.slug = :ms
                            GROUP BY m.id
                            """
                        ),
                        {"bs": brand_slug, "ms": model_slug},
                    )
                ).one()
                model_id, executions = row
                assert model_id > 0
                expected = [
                    e.value for e in APPROVED_MODEL_EXECUTIONS[(brand_slug, model_slug)]
                ]
                assert list(executions) == expected

            for brand_slug, model_slug in _DUAL:
                cnt = (
                    await session.execute(
                        text(
                            """
                            SELECT COUNT(*) FROM vehicle_models m
                            JOIN vehicle_brands b ON b.id = m.brand_id
                            WHERE b.slug = :bs AND m.slug = :ms AND m.is_enabled
                            """
                        ),
                        {"bs": brand_slug, "ms": model_slug},
                    )
                ).scalar_one()
                assert cnt == 1

            banned = {
                "sprinter",
                "gazelle",
                "sobol",
                "transit",
                "hiace",
                "porter",
                "bongo",
                "daily",
                "ducato",
                "jumper",
                "profi",
            }
            for brand in ("mercedes-benz", "gaz", "ford", "toyota", "hyundai", "kia"):
                try:
                    models = await svc.list_models_for_brand(
                        brand, catalog_context=VehicleCatalogContext.car_sale
                    )
                except Exception:
                    continue
                slugs = {m.slug for m in models}
                assert not (slugs & banned), f"{brand} still has {slugs & banned}"

            toyota = await svc.list_models_for_brand(
                "toyota", catalog_context=VehicleCatalogContext.car_sale
            )
            names = {m.name for m in toyota}
            assert "Camry" in names or "Corolla" in names
            assert "Hiace" not in names

            mercedes = await svc.list_models_for_brand(
                "mercedes-benz", catalog_context=VehicleCatalogContext.car_sale
            )
            mnames = {m.name for m in mercedes}
            assert "Sprinter" not in mnames
            assert any(n for n in mnames)

            passenger = await svc.list_models_for_brand(
                "mercedes-benz",
                catalog_context=VehicleCatalogContext.passenger_parts,
            )
            assert "sprinter" not in {m.slug for m in passenger}

            cargo_brands = await svc.list_brands(
                catalog_context=VehicleCatalogContext.cargo_parts
            )
            cargo_slugs = {b.slug for b in cargo_brands}
            assert "kamaz" in cargo_slugs
            assert "mercedes-benz" in cargo_slugs

            cargo_models = await svc.list_models_for_brand(
                "mercedes-benz",
                catalog_context=VehicleCatalogContext.cargo_parts,
            )
            assert "sprinter" in {m.slug for m in cargo_models}
            sprinter = next(m for m in cargo_models if m.slug == "sprinter")
            assert set(sprinter.allowed_executions) == {
                VehicleExecution.cargo,
                VehicleExecution.passenger,
            }
            assert sprinter.requires_execution_choice is True
            assert "cargo" in sprinter.placement_by_execution

        await engine.dispose()

    asyncio.run(_run())


def test_http_catalog_context_smoke() -> None:
    """Live docker API smoke (not TestClient)."""
    import json
    import urllib.request

    base = "http://127.0.0.1:8000/api/v1/vehicles/brands/mercedes-benz/models"
    with urllib.request.urlopen(f"{base}?catalog_context=cargo_parts", timeout=10) as resp:
        cargo = json.loads(resp.read().decode())
    assert any(m["slug"] == "sprinter" for m in cargo)

    with urllib.request.urlopen(f"{base}?catalog_context=car_sale", timeout=10) as resp:
        car = json.loads(resp.read().decode())
    assert not any(m["slug"] == "sprinter" for m in car)

    with urllib.request.urlopen(
        f"{base}?catalog_context=passenger_parts", timeout=10
    ) as resp:
        passenger = json.loads(resp.read().decode())
    assert not any(m["slug"] == "sprinter" for m in passenger)
