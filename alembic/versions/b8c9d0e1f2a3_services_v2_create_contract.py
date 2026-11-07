"""Services V2 Create contract: multi-object, drop materials, nullable price.

Revision ID: b8c9d0e1f2a3svccreate
Revises: a7b8c9d0e1f2servicesv2a
Create Date: 2026-11-07

- listings.price nullable (Services «По договорённости»)
- Re-seed canonical Services core fields from services_v2 SoT
"""
from __future__ import annotations

import json

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

revision = "b8c9d0e1f2a3svccreate"
down_revision = "a7b8c9d0e1f2servicesv2a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    from app.seeds.services_v2 import (
        SERVICES_V2_CANONICAL_SLUGS,
        build_services_v2_core_fields,
    )

    bind = op.get_bind()
    op.alter_column(
        "listings",
        "price",
        existing_type=sa.Numeric(precision=12, scale=2),
        nullable=True,
    )

    # Safety: refuse if any Services EAV still has service_materials values.
    mats = bind.execute(
        text(
            """
            SELECT count(*) FROM listing_field_values lfv
            JOIN listings l ON l.id = lfv.listing_id
            JOIN categories c ON c.id = l.category_id
            WHERE lfv.field_key = 'service_materials'
              AND (c.slug LIKE 'services-%' OR c.slug = 'services')
            """
        )
    ).scalar_one()
    if int(mats or 0) > 0:
        raise RuntimeError(
            "Services Create contract STOP: persisted service_materials values exist"
        )

    core_by_slug = build_services_v2_core_fields()
    for slug in sorted(SERVICES_V2_CANONICAL_SLUGS):
        row = bind.execute(
            text("SELECT id FROM categories WHERE slug = :slug"),
            {"slug": slug},
        ).fetchone()
        if row is None:
            continue
        cid = int(row[0])
        bind.execute(
            text("DELETE FROM category_core_fields WHERE category_id = :cid"),
            {"cid": cid},
        )
        for key, label, ftype, required, sort, options, hint in core_by_slug[slug]:
            if key in {"city", "title", "description", "photos", "region"}:
                continue
            bind.execute(
                text(
                    """
                    INSERT INTO category_core_fields (
                        category_id, field_key, label, field_type, is_required,
                        sort_order, ai_hint, options, create_intent,
                        created_at, updated_at
                    ) VALUES (
                        :cid, :key, :label, :ftype, :req,
                        :sort, :hint, CAST(:options AS jsonb), NULL,
                        now(), now()
                    )
                    """
                ),
                {
                    "cid": cid,
                    "key": key,
                    "label": label,
                    "ftype": ftype.value if hasattr(ftype, "value") else str(ftype),
                    "req": bool(required),
                    "sort": int(sort),
                    "hint": hint,
                    "options": json.dumps(options, ensure_ascii=False)
                    if options is not None
                    else None,
                },
            )


def downgrade() -> None:
    # Do not force NOT NULL — historical negotiated rows may exist.
    pass
