#!/usr/bin/env python3
"""Load category intelligence and vehicle dictionary seed data.

Usage (from project root):
    python -m scripts.seed_categories
"""
from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.db.session import async_session_maker
from app.seeds.loader import CategorySeedLoader

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main() -> None:
    async with async_session_maker() as session:
        loader = CategorySeedLoader(session)
        stats = await loader.run()
        logger.info("Seed complete: %s", stats)


if __name__ == "__main__":
    asyncio.run(main())
