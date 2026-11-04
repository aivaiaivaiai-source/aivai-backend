#!/usr/bin/env python3
"""Apply Transport V2.1 catalog migration (dev).

Usage:
  python -m scripts.migrate_transport_v2_1 --dry-run
  python -m scripts.migrate_transport_v2_1
  python -m scripts.migrate_transport_v2_1 --verify-only
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
from app.seeds.transport_v2_1_migration import (
    preflight,
    run_migration,
    verify_post_migration,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()

    async with async_session_maker() as session:
        if args.verify_only:
            print(json.dumps(await verify_post_migration(session), ensure_ascii=False, indent=2))
            return

        pf = await preflight(session)
        logger.info("Preflight ok=%s already=%s listings=%s", pf.ok, pf.already_applied, pf.listing_counts)
        if not pf.ok:
            raise SystemExit(f"Preflight blocked: {pf.errors}")

        result = await run_migration(session, dry_run=args.dry_run)
        verify = await verify_post_migration(session)
        print(
            json.dumps(
                {
                    "result": {
                        "snapshot_path": result.snapshot_path,
                        "snapshot_sha256": result.snapshot_sha256,
                        "created": result.created,
                        "renamed": result.renamed,
                        "moved": result.moved,
                        "retired_count": len(result.retired),
                        "listings_remapped": result.listings_remapped,
                        "aliases_retargeted": result.aliases_retargeted,
                        "services_pending": result.services_pending,
                        "dry_run": result.dry_run,
                    },
                    "verify": verify,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        if not args.dry_run and not verify.get("l1_match"):
            raise SystemExit("L1 mismatch after migration")
        if not args.dry_run and verify.get("forbidden_still_active"):
            raise SystemExit(f"Forbidden still active: {verify['forbidden_still_active']}")


if __name__ == "__main__":
    asyncio.run(main())
