"""One-off: count media rows after lifecycle migration."""
from __future__ import annotations

import asyncio

from sqlalchemy import text

from app.db.session import async_session_maker


async def main() -> None:
    async with async_session_maker() as session:
        total = (await session.execute(text("SELECT COUNT(*) FROM media"))).scalar_one()
        ready = (
            await session.execute(
                text("SELECT COUNT(*) FROM media WHERE lifecycle_status = 'ready'"),
            )
        ).scalar_one()
        rejected = (
            await session.execute(
                text("SELECT COUNT(*) FROM media WHERE lifecycle_status = 'rejected'"),
            )
        ).scalar_one()
        with_original = (
            await session.execute(
                text("SELECT COUNT(*) FROM media WHERE original_url IS NOT NULL"),
            )
        ).scalar_one()
        print(f"total={total} ready={ready} rejected={rejected} with_original_url={with_original}")


if __name__ == "__main__":
    asyncio.run(main())
