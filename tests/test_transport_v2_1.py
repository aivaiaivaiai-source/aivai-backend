"""Transport V2.1 catalog shape checks against configured DB."""
from __future__ import annotations

import asyncio

from sqlalchemy import text

from app.db.session import async_session_maker
from app.seeds.transport_v2_1 import L1_ACTIVE
from app.seeds.transport_v2_1_migration import verify_post_migration


async def _run_checks() -> None:
    async with async_session_maker() as session:
        stats = await verify_post_migration(session)
        assert stats["l1_match"] is True
        assert stats["forbidden_still_active"] == []
        assert stats["car_sale_active"] is True
        assert stats["parts_name"] == "Автозапчасти"
        assert [s for s, _, _ in L1_ACTIVE] == stats["active_l1_slugs"]
        assert len(stats["active_l1_slugs"]) == 15

        row = (
            await session.execute(
                text(
                    """
                    SELECT c.slug AS child, p.slug AS parent
                    FROM categories c
                    JOIN categories p ON c.parent_id = p.id
                    WHERE c.slug = 'transport-auto-parts-optika-fary-i-fonari'
                    """
                )
            )
        ).mappings().one()
        # Canonical: Автозапчасти → Оптика (not accessories Автосвет)
        assert row["parent"] in {
            "transport-auto-parts",
            "transport-auto-parts-kuzovnye-detali",
        }

        counts = (
            await session.execute(
                text(
                    """
                    SELECT
                      COUNT(*) FILTER (WHERE status = 'active') AS active,
                      COUNT(*) FILTER (WHERE status = 'draft') AS draft
                    FROM listings
                    WHERE category_id = (
                      SELECT id FROM categories WHERE slug = 'transport-car-sale'
                    )
                    """
                )
            )
        ).mappings().one()
        assert int(counts["active"]) >= 1


def test_transport_v2_1_catalog_shape() -> None:
    asyncio.run(_run_checks())
