"""Services V2 Package B — Search filter metadata.

Revision ID: c9d0e1f2a3b4svcpkgb
Revises: b8c9d0e1f2a3svccreate
Create Date: 2026-11-07

Re-seed category_filters for canonical Services leaves from services_v2 SoT.
Does not alter Create core fields.
"""
from __future__ import annotations

import json

from alembic import op
from sqlalchemy import text

revision = "c9d0e1f2a3b4svcpkgb"
down_revision = "b8c9d0e1f2a3svccreate"
branch_labels = None
depends_on = None


def upgrade() -> None:
    from app.seeds.services_v2 import (
        SERVICES_V2_CANONICAL_SLUGS,
        build_services_v2_search_filters,
    )

    bind = op.get_bind()
    filters_by_slug = build_services_v2_search_filters()
    for slug in sorted(SERVICES_V2_CANONICAL_SLUGS):
        row = bind.execute(
            text("SELECT id FROM categories WHERE slug = :slug"),
            {"slug": slug},
        ).fetchone()
        if row is None:
            continue
        cid = int(row[0])
        bind.execute(
            text("DELETE FROM category_filters WHERE category_id = :cid"),
            {"cid": cid},
        )
        for key, label, ftype, sort, config in filters_by_slug[slug]:
            bind.execute(
                text(
                    """
                    INSERT INTO category_filters (
                        category_id, filter_key, label, filter_type, sort_order,
                        config, search_intent, created_at, updated_at
                    ) VALUES (
                        :cid, :key, :label, :ftype, :sort,
                        CAST(:config AS jsonb), '', now(), now()
                    )
                    """
                ),
                {
                    "cid": cid,
                    "key": key,
                    "label": label,
                    "ftype": ftype.value if hasattr(ftype, "value") else str(ftype),
                    "sort": int(sort),
                    "config": json.dumps(config, ensure_ascii=False)
                    if config is not None
                    else None,
                },
            )


def downgrade() -> None:
    bind = op.get_bind()
    bind.execute(
        text(
            """
            DELETE FROM category_filters
            WHERE category_id IN (
                SELECT id FROM categories
                WHERE slug LIKE 'services-%' OR slug = 'services'
            )
            """
        )
    )
