#!/usr/bin/env python3
"""Apply Home & Garden FINAL catalog migration (dev).

Usage:
  python -m scripts.migrate_home_garden_final --dry-run
  python -m scripts.migrate_home_garden_final
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.db.session import async_session_maker
from app.seeds.home_garden_catalog_final import (
    HOME_GARDEN_L2_NAMES,
    HOME_GARDEN_L2_SLUGS,
    HOME_GARDEN_LEAF_SLUGS,
    HOME_GARDEN_NODES,
    L4_PARENT_SLUGS,
)
from app.seeds.home_garden_final_migration import run_home_garden_final_migration
from sqlalchemy import text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def verify(session) -> dict:
    rows = (
        await session.execute(
            text(
                """
                SELECT c.slug, c.name, c.is_active, p.slug AS parent_slug
                FROM categories c
                LEFT JOIN categories p ON p.id = c.parent_id
                WHERE p.slug = 'home-garden' AND c.is_active
                ORDER BY c.sort_order, c.id
                """
            )
        )
    ).mappings().all()
    l2_slugs = [r["slug"] for r in rows]
    l2_names = [r["name"] for r in rows]

    l4_counts = {}
    for parent in L4_PARENT_SLUGS:
        cnt = int(
            (
                await session.execute(
                    text(
                        """
                        SELECT COUNT(*) FROM categories c
                        JOIN categories p ON p.id = c.parent_id
                        WHERE p.slug = :p AND c.is_active
                        """
                    ),
                    {"p": parent},
                )
            ).scalar_one()
        )
        l4_counts[parent] = cnt

    # Forbidden names under home-garden active tree
    forbidden = ["Мотоблок", "Детские качели", "Электрический чайник"]

    active_names = (
        await session.execute(
            text(
                """
                WITH RECURSIVE tree AS (
                  SELECT id, slug, name, parent_id, is_active
                  FROM categories WHERE slug = 'home-garden'
                  UNION ALL
                  SELECT c.id, c.slug, c.name, c.parent_id, c.is_active
                  FROM categories c
                  JOIN tree t ON c.parent_id = t.id
                )
                SELECT slug, name FROM tree WHERE is_active = true
                """
            )
        )
    ).mappings().all()
    name_set = {r["name"] for r in active_names}
    sleep_children = [
        r["name"]
        for r in active_names
        if r["slug"].startswith("home-garden-postelnoe-bele-i-pledy-")
    ]
    decor_children = [
        r["name"]
        for r in active_names
        if r["slug"].startswith("home-garden-dekor-i-interer-")
    ]
    tech_children = [
        r["name"]
        for r in active_names
        if r["slug"].startswith("home-garden-sadovaya-tehnika-")
    ]
    swings = [
        r["name"]
        for r in active_names
        if r["slug"].startswith("home-garden-sadovye-kacheli-i-gamaki-")
    ]
    dacha = [
        r["name"]
        for r in active_names
        if r["slug"].startswith("home-garden-besedki-navesy-i-tovary-dlya-dachi-")
    ]
    banya = [
        r["name"]
        for r in active_names
        if r["slug"].startswith("home-garden-tovary-dlya-bani-i-sauny-")
    ]

    return {
        "l2_count": len(l2_slugs),
        "l2_count_ok": len(l2_slugs) == 32,
        "prochee_is_last": bool(l2_names) and l2_names[-1] == "Прочее для дома и сада",
        "l2_slugs_ok": l2_slugs == HOME_GARDEN_L2_SLUGS,
        "l2_names_ok": l2_names == HOME_GARDEN_L2_NAMES,
        "l2_names": l2_names,
        "l4_counts": l4_counts,
        "target_nodes": len(HOME_GARDEN_NODES),
        "target_leaves": len(HOME_GARDEN_LEAF_SLUGS),
        "forbidden_present": [n for n in forbidden if n in name_set],
        "kids_furniture_active": any(r["name"] == "Детская мебель" for r in active_names),
        "kids_carpets_active": any(r["name"] == "Детские ковры" for r in active_names),
        "dacha_shezlongi_active": any(r["name"] == "Шезлонги" for r in active_names),
        "dacha_benches_active": any(r["name"] == "Скамейки для дачи" for r in active_names),
        "irrigation_tanks_active": any(r["name"] == "Ёмкости для полива" for r in active_names),
        "mattress_in_sleep": any("Матрас" in n for n in sleep_children),
        "mirror_in_decor": any("Зеркал" in n for n in decor_children),
        "motoblock_in_tech": any("Мотоблок" in n for n in tech_children),
        "kids_swings_in_swings": any("Детск" in n and "качел" in n.lower() for n in swings),
        "swings_in_dacha": any("качел" in n.lower() or "гамак" in n.lower() for n in dacha),
        "stove_in_banya": any("Печ" in n for n in banya),
        "kitchen_set_paths": [
            r["slug"]
            for r in active_names
            if "Кухонн" in r["name"] and "гарнитур" in r["name"].lower()
        ],
        "new_l2_present": all(
            s in l2_slugs
            for s in (
                "home-garden-emkosti-i-rezervuary",
                "home-garden-drova-i-ugol",
                "home-garden-gazovye-ballony",
                "home-garden-tovary-dlya-prazdnikov",
            )
        ),
    }


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()

    async with async_session_maker() as session:
        if args.verify_only:
            print(json.dumps(await verify(session), ensure_ascii=False, indent=2))
            return
        result = await run_home_garden_final_migration(session, dry_run=args.dry_run)
        v = await verify(session)
        print(
            json.dumps(
                {
                    "created": len(result.created),
                    "updated": len(result.updated),
                    "retired": len(result.retired),
                    "listings_remapped": result.listings_remapped,
                    "aliases_upserted": result.aliases_upserted,
                    "fields_upserted": result.fields_upserted,
                    "filters_upserted": result.filters_upserted,
                    "already_applied": result.already_applied,
                    "verify": v,
                },
                ensure_ascii=False,
                indent=2,
            )
        )


if __name__ == "__main__":
    asyncio.run(main())
