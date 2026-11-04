#!/usr/bin/env python3
"""Phase 1: Transport catalog canonicalization migration.

Usage (from aivai_backend root):
    python -m scripts.migrate_transport_canonical_phase1
    python -m scripts.migrate_transport_canonical_phase1 --verify-only
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
from app.seeds.transport_canonical_migration import (
    preflight,
    run_phase1_migration,
    verify_post_migration,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()

    async with async_session_maker() as session:
        if args.verify_only:
            stats = await verify_post_migration(session)
            print(json.dumps(stats, ensure_ascii=False, indent=2))
            return

        pf = await preflight(session)
        logger.info("Preflight: %s", pf)
        if not pf.ok:
            raise SystemExit(f"Preflight blocked: {pf.errors}")

        result = await run_phase1_migration(session)
        logger.info("Migration complete: %s", result)

        stats = await verify_post_migration(session)
        logger.info("Post-migration verify: %s", stats)
        print(json.dumps({"result": result.__dict__, "verify": stats}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
