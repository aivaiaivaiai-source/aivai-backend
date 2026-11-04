"""Jobs Search V2 UX: hiring labels + drop price filters.

Revision ID: q5r6s7t8u9v0
Revises: p4q5r6s7t8u9
Create Date: 2026-10-29

- Update hiring search filter display labels (keys unchanged)
- Delete Jobs Search V2 price filter rows for hiring + job_seeking only
- Re-upsert filter defs from jobs_search_filters seed (no salary)
"""
from __future__ import annotations

import json

import sqlalchemy as sa
from alembic import op
from sqlalchemy import text

revision = "q5r6s7t8u9v0"
down_revision = "p4q5r6s7t8u9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    # Remove only Jobs Search V2 salary filters (both intents).
    bind.execute(
        text(
            """
            DELETE FROM category_filters
            WHERE filter_key = 'price'
              AND search_intent IN ('hiring', 'job_seeking')
              AND category_id IN (
                SELECT id FROM categories WHERE slug LIKE 'jobs-%'
              )
            """
        )
    )

    from app.seeds.jobs_search_filters import build_jobs_search_filters

    by_slug = build_jobs_search_filters()
    for slug, intents in by_slug.items():
        row = bind.execute(
            text("SELECT id FROM categories WHERE slug = :slug"),
            {"slug": slug},
        ).fetchone()
        if row is None:
            continue
        cat_id = int(row[0])
        for intent, filters in intents.items():
            # Drop any stale keys not in new seed for this intent (e.g. price).
            wanted = {f[0] for f in filters}
            existing = bind.execute(
                text(
                    "SELECT id, filter_key FROM category_filters "
                    "WHERE category_id = :cid AND search_intent = :intent"
                ),
                {"cid": cat_id, "intent": intent},
            ).fetchall()
            for eid, ekey in existing:
                if ekey not in wanted:
                    bind.execute(
                        text("DELETE FROM category_filters WHERE id = :id"),
                        {"id": eid},
                    )
            for key, label, ftype, sort_order, config in filters:
                ftype_val = ftype.value if hasattr(ftype, "value") else str(ftype)
                cfg_json = json.dumps(config, ensure_ascii=False) if config else None
                found = bind.execute(
                    text(
                        "SELECT id FROM category_filters "
                        "WHERE category_id = :cid AND filter_key = :key "
                        "AND search_intent = :intent"
                    ),
                    {"cid": cat_id, "key": key, "intent": intent},
                ).fetchone()
                if found:
                    bind.execute(
                        text(
                            "UPDATE category_filters SET label = :label, "
                            "filter_type = CAST(:ftype AS category_filter_type_enum), "
                            "sort_order = :sort_order, config = CAST(:config AS jsonb), "
                            "updated_at = NOW() WHERE id = :id"
                        ),
                        {
                            "id": found[0],
                            "label": label,
                            "ftype": ftype_val,
                            "sort_order": sort_order,
                            "config": cfg_json,
                        },
                    )
                else:
                    bind.execute(
                        text(
                            "INSERT INTO category_filters "
                            "(category_id, filter_key, label, filter_type, sort_order, "
                            "config, search_intent, created_at, updated_at) "
                            "VALUES (:cid, :key, :label, "
                            "CAST(:ftype AS category_filter_type_enum), :sort_order, "
                            "CAST(:config AS jsonb), :intent, NOW(), NOW())"
                        ),
                        {
                            "cid": cat_id,
                            "key": key,
                            "label": label,
                            "ftype": ftype_val,
                            "sort_order": sort_order,
                            "config": cfg_json,
                            "intent": intent,
                        },
                    )


def downgrade() -> None:
    # Non-destructive reverse: restore labels/price from previous seed shape
    # is not required for UX-forward cleanup; no-op keep schema.
    pass
