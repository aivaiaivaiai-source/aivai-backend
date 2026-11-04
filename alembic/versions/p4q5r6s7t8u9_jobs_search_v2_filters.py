"""Jobs Search V2: intent-aware category_filters + seed.

Revision ID: p4q5r6s7t8u9
Revises: o3p4q5r6s7t8
Create Date: 2026-10-29

- Add category_filters.search_intent ('' = non-intent / legacy rows)
- Unique (category_id, filter_key, search_intent)
- Seed hiring + job_seeking search filters for 20 canonical job sectors
"""
from __future__ import annotations

import json

import sqlalchemy as sa
from alembic import op
from sqlalchemy import text

revision = "p4q5r6s7t8u9"
down_revision = "o3p4q5r6s7t8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "category_filters",
        sa.Column(
            "search_intent",
            sa.String(length=32),
            nullable=False,
            server_default="",
        ),
    )
    op.drop_constraint(
        "uq_category_filters_key",
        "category_filters",
        type_="unique",
    )
    op.create_unique_constraint(
        "uq_category_filters_key_intent",
        "category_filters",
        ["category_id", "filter_key", "search_intent"],
    )
    op.create_index(
        "ix_category_filters_search_intent",
        "category_filters",
        ["search_intent"],
        unique=False,
    )

    bind = op.get_bind()
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
            for key, label, ftype, sort_order, config in filters:
                ftype_val = ftype.value if hasattr(ftype, "value") else str(ftype)
                cfg_json = json.dumps(config, ensure_ascii=False) if config else None
                existing = bind.execute(
                    text(
                        "SELECT id FROM category_filters "
                        "WHERE category_id = :cid AND filter_key = :key "
                        "AND search_intent = :intent"
                    ),
                    {"cid": cat_id, "key": key, "intent": intent},
                ).fetchone()
                if existing:
                    bind.execute(
                        text(
                            "UPDATE category_filters SET label = :label, "
                            "filter_type = CAST(:ftype AS category_filter_type_enum), "
                            "sort_order = :sort_order, config = CAST(:config AS jsonb), "
                            "updated_at = NOW() WHERE id = :id"
                        ),
                        {
                            "id": existing[0],
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
    bind = op.get_bind()
    bind.execute(
        text(
            "DELETE FROM category_filters WHERE search_intent IN "
            "('hiring', 'job_seeking')"
        )
    )
    op.drop_index("ix_category_filters_search_intent", table_name="category_filters")
    op.drop_constraint(
        "uq_category_filters_key_intent",
        "category_filters",
        type_="unique",
    )
    op.create_unique_constraint(
        "uq_category_filters_key",
        "category_filters",
        ["category_id", "filter_key"],
    )
    op.drop_column("category_filters", "search_intent")
