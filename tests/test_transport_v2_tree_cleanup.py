"""Transport V2 Stage 1 — canonical L2 tree integrity against live DB."""
from __future__ import annotations

import asyncio

from sqlalchemy import text

from app.db.session import async_session_maker
from app.seeds.transport_v2_1 import (
    AUTO_SERVICES_CHILD_SLUGS,
    BUSES_L2_CHILD_SLUGS,
    L1_ACTIVE,
)


EXPECTED_L2 = [s for s, _, _ in L1_ACTIVE]


async def _checks() -> None:
    async with async_session_maker() as session:
        transport = (
            await session.execute(
                text("SELECT id FROM categories WHERE slug = 'transport'")
            )
        ).scalar_one()

        active_l2 = (
            await session.execute(
                text(
                    """
                    SELECT id, slug, name, sort_order
                    FROM categories
                    WHERE parent_id = :pid AND is_active = true
                    ORDER BY sort_order, id
                    """
                ),
                {"pid": transport},
            )
        ).mappings().all()

        slugs = [r["slug"] for r in active_l2]
        assert len(slugs) == 15, slugs
        assert slugs == EXPECTED_L2, slugs
        sorts = [int(r["sort_order"]) for r in active_l2]
        assert len(set(sorts)) == 15, sorts
        assert [r["name"] for r in active_l2] == [n for _, n, _ in L1_ACTIVE]

        # Auto services
        services = (
            await session.execute(
                text(
                    "SELECT id, is_active FROM categories WHERE slug = 'transport-auto-services'"
                )
            )
        ).mappings().one()
        assert services["is_active"] is True
        svc_children = (
            await session.execute(
                text(
                    """
                    SELECT slug, is_active
                    FROM categories
                    WHERE parent_id = :pid
                    ORDER BY sort_order, id
                    """
                ),
                {"pid": services["id"]},
            )
        ).mappings().all()
        active_svc = [r["slug"] for r in svc_children if r["is_active"]]
        assert set(active_svc) == set(AUTO_SERVICES_CHILD_SLUGS)
        assert len(active_svc) == 10

        # Buses
        buses = (
            await session.execute(
                text(
                    "SELECT id FROM categories WHERE slug = 'transport-buses-microbuses-motorhomes'"
                )
            )
        ).scalar_one()
        bus_children = (
            await session.execute(
                text(
                    """
                    SELECT slug, is_active
                    FROM categories
                    WHERE parent_id = :pid AND is_active = true
                    ORDER BY sort_order, id
                    """
                ),
                {"pid": buses},
            )
        ).mappings().all()
        bus_slugs = [r["slug"] for r in bus_children]
        assert bus_slugs == list(BUSES_L2_CHILD_SLUGS), bus_slugs

        # Commercial / buyback — inactive + 0 active children
        for root in ("transport-commercial", "transport-buyback-exchange"):
            row = (
                await session.execute(
                    text(
                        """
                        SELECT c.id, c.is_active,
                          (SELECT COUNT(*) FROM categories ch
                           WHERE ch.parent_id = c.id AND ch.is_active = true) AS active_kids
                        FROM categories c WHERE c.slug = :s
                        """
                    ),
                    {"s": root},
                )
            ).mappings().one()
            assert row["is_active"] is False, root
            assert int(row["active_kids"]) == 0, root

        # Regression rules
        rules = {
            "transport-special-equipment-manipulyatory": "transport-special-equipment",
            "transport-cargo-evakuatory": "transport-cargo",
            "transport-cargo-tsisterny": "transport-cargo",
            "transport-cargo-furgony": "transport-cargo",
        }
        for child, parent in rules.items():
            hit = (
                await session.execute(
                    text(
                        """
                        SELECT c.is_active AS child_active, p.slug AS parent
                        FROM categories c
                        JOIN categories p ON p.id = c.parent_id
                        WHERE c.slug = :s
                        """
                    ),
                    {"s": child},
                )
            ).mappings().one()
            assert hit["child_active"] is True, child
            assert hit["parent"] == parent, (child, hit["parent"])

        for inactive in (
            "transport-cargo-spetsgruzoviki",
            "transport-bicycles-detskie",
            "transport-accessories-tuning-avtosvet-i-tyuning-optiki",
            "transport-special-equipment-dorozhnaya-tehnika",
            "transport-special-equipment-evakuatory",
        ):
            active = (
                await session.execute(
                    text("SELECT is_active FROM categories WHERE slug = :s"),
                    {"s": inactive},
                )
            ).scalar_one()
            assert active is False, inactive

        optics = (
            await session.execute(
                text(
                    """
                    SELECT c.is_active, p.slug AS parent
                    FROM categories c
                    JOIN categories p ON p.id = c.parent_id
                    WHERE c.slug = 'transport-auto-parts-optika-fary-i-fonari'
                    """
                )
            )
        ).mappings().one()
        assert optics["is_active"] is True
        # Canonical home: Автозапчасти → Оптика (not accessories Автосвет)
        assert optics["parent"] in {
            "transport-auto-parts",
            "transport-auto-parts-kuzovnye-detali",
        }

        # Integrity: cleaned legacy branches must not leak IPAC
        ipac = (
            await session.execute(
                text(
                    """
                    SELECT COUNT(*) FROM categories c
                    JOIN categories p ON p.id = c.parent_id
                    WHERE p.is_active = false AND c.is_active = true
                      AND p.slug IN (
                        'transport-commercial',
                        'transport-buyback-exchange'
                      )
                    """
                )
            )
        ).scalar_one()
        assert int(ipac) == 0


def test_transport_v2_tree_cleanup() -> None:
    asyncio.run(_checks())
