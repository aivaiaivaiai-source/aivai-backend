"""Read-only catalog audit helper — not for commit."""
from __future__ import annotations

import asyncio
import json
from collections import defaultdict

from sqlalchemy import text

from app.db.session import async_session_maker


async def main() -> None:
    async with async_session_maker() as s:
        rows = (
            await s.execute(
                text(
                    """
                    SELECT c.id, c.slug, c.name, c.parent_id, c.is_active, c.entity_type, c.sort_order,
                           (SELECT COUNT(*) FROM category_core_fields f WHERE f.category_id=c.id) AS core_n,
                           (SELECT COUNT(*) FROM category_optional_fields f WHERE f.category_id=c.id) AS opt_n,
                           (SELECT COUNT(*) FROM category_filters f WHERE f.category_id=c.id) AS filter_n,
                           (SELECT COUNT(*) FROM category_ai_rules r WHERE r.category_id=c.id) AS rule_n
                    FROM categories c ORDER BY c.id
                    """
                )
            )
        ).fetchall()
        cats = [dict(r._mapping) for r in rows]
        by_id = {c["id"]: c for c in cats}
        children: dict[int, list[int]] = defaultdict(list)
        for c in cats:
            if c["parent_id"]:
                children[c["parent_id"]].append(c["id"])

        def depth(cid: int) -> int:
            d = 0
            cur = cid
            while by_id[cur]["parent_id"]:
                d += 1
                cur = by_id[cur]["parent_id"]
            return d

        for c in cats:
            c["depth"] = depth(c["id"])
            c["is_leaf"] = len(children[c["id"]]) == 0

        stats = {
            "total": len(cats),
            "active": sum(1 for c in cats if c["is_active"]),
            "inactive": sum(1 for c in cats if not c["is_active"]),
            "leaf": sum(1 for c in cats if c["is_leaf"]),
            "max_depth": max(c["depth"] for c in cats) if cats else 0,
        }
        print(json.dumps({"stats": stats, "categories": cats}, ensure_ascii=False, default=str))


if __name__ == "__main__":
    asyncio.run(main())
