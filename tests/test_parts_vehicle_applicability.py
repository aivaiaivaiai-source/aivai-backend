"""Parts Step 1 + category intelligence regression."""
from __future__ import annotations

import asyncio

from sqlalchemy import text

from app.db.session import async_session_maker, engine
from app.repositories.category_alias_repository import CategoryAliasRepository
from app.repositories.category_moderation_rule_repository import CategoryModerationRuleRepository
from app.repositories.category_repository import CategoryRepository
from app.repositories.category_routing_rule_repository import CategoryRoutingRuleRepository
from app.repositories.vehicle_repository import VehicleAliasRepository
from app.seeds.transport_v2_1 import PARTS_VEHICLE_APPLICABILITY_OPTIONS
from app.services.category_intelligence_service import CategoryIntelligenceService


EXPECTED_VALUES = [v for v, _ in PARTS_VEHICLE_APPLICABILITY_OPTIONS]
EXPECTED_LABELS = [lbl for _, lbl in PARTS_VEHICLE_APPLICABILITY_OPTIONS]


def test_deps_imports_category_alias_repository() -> None:
    """Regression: missing import caused intelligence endpoint 500."""
    import app.api.deps as deps

    assert hasattr(deps, "CategoryAliasRepository")
    assert deps.CategoryAliasRepository is CategoryAliasRepository


def test_parts_vehicle_applicability_options_in_db_and_intelligence() -> None:
    async def _run() -> None:
        async with async_session_maker() as session:
            cat_id = int(
                (
                    await session.execute(
                        text(
                            "SELECT id FROM categories WHERE slug = 'transport-auto-parts'"
                        )
                    )
                ).scalar_one()
            )
            row = (
                await session.execute(
                    text(
                        """
                        SELECT options
                        FROM category_core_fields
                        WHERE category_id = :cid AND field_key = 'vehicle_applicability'
                        """
                    ),
                    {"cid": cat_id},
                )
            ).mappings().one()
            options = row["options"] or {}
            values = options.get("values") or []
            assert len(values) == 10
            assert [item["value"] for item in values] == EXPECTED_VALUES
            assert [item["label"] for item in values] == EXPECTED_LABELS
            assert "Микроавтобусы" not in [item["label"] for item in values]
            assert "Коммерческий транспорт" not in [item["label"] for item in values]

            svc = CategoryIntelligenceService(
                CategoryRepository(session),
                CategoryAliasRepository(session),
                CategoryRoutingRuleRepository(session),
                CategoryModerationRuleRepository(session),
                VehicleAliasRepository(session),
            )
            intel = await svc.get_category_intelligence(cat_id)
            assert intel is not None
            assert intel.slug == "transport-auto-parts"
            field = next(
                f for f in intel.core_fields if f.field_key == "vehicle_applicability"
            )
            assert field.label == "Для какого транспорта"
            assert field.field_type.value == "enum" or str(field.field_type) == "enum"
            opts = (field.options or {}).get("values") or []
            assert [item["value"] for item in opts] == EXPECTED_VALUES
            assert [item["label"] for item in opts] == EXPECTED_LABELS
        await engine.dispose()

    asyncio.run(_run())
