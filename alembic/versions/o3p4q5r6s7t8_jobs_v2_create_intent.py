"""Jobs V2: create_intent on core_fields + listing.job_intent + seeking seed.

Revision ID: o3p4q5r6s7t8
Revises: n2o3p4q5r6s7
Create Date: 2026-10-28

- Add category_core_fields.create_intent (hiring | job_seeking | NULL)
- Tag existing Jobs Pilot fields as hiring
- Seed job_seeking schemas for 20 canonical sectors
- Soft-deactivate meta/legacy job leaves from active tree (no row deletes)
- Add listings.job_intent (nullable; no destructive backfill)
"""
from __future__ import annotations

import json

import sqlalchemy as sa
from alembic import op
from sqlalchemy import text

revision = "o3p4q5r6s7t8"
down_revision = "n2o3p4q5r6s7"
branch_labels = None
depends_on = None

_DEACTIVATE_SLUGS = (
    "jobs-vacancies",
    "jobs-resume",
    "jobs-vakansii-bez-opyta",
    "jobs-rezyume-soiskateley",
)


def _upsert_fields(bind, cat_id: int, intent: str, fields) -> None:
    for sort_i, field in enumerate(fields):
        key, label, ftype, required, options, hint = field
        ftype_val = ftype.value if hasattr(ftype, "value") else str(ftype)
        opts_json = json.dumps(options, ensure_ascii=False) if options else None
        existing = bind.execute(
            text(
                """
                SELECT id FROM category_core_fields
                WHERE category_id = :cid
                  AND field_key = :key
                  AND COALESCE(create_intent, '') = :intent
                """
            ),
            {"cid": cat_id, "key": key, "intent": intent},
        ).fetchone()
        if existing is None:
            bind.execute(
                text(
                    """
                    INSERT INTO category_core_fields
                    (category_id, field_key, label, field_type, is_required,
                     sort_order, options, ai_hint, create_intent, created_at, updated_at)
                    VALUES
                    (:cid, :key, :label, CAST(:ftype AS category_field_type_enum),
                     :req, :sort, CAST(:opts AS jsonb), :hint, :intent, now(), now())
                    """
                ),
                {
                    "cid": cat_id,
                    "key": key,
                    "label": label,
                    "ftype": ftype_val,
                    "req": required,
                    "sort": sort_i,
                    "opts": opts_json,
                    "hint": hint,
                    "intent": intent,
                },
            )
        else:
            bind.execute(
                text(
                    """
                    UPDATE category_core_fields
                    SET label = :label,
                        field_type = CAST(:ftype AS category_field_type_enum),
                        is_required = :req,
                        sort_order = :sort,
                        options = CAST(:opts AS jsonb),
                        ai_hint = :hint,
                        updated_at = now()
                    WHERE id = :id
                    """
                ),
                {
                    "id": existing[0],
                    "label": label,
                    "ftype": ftype_val,
                    "req": required,
                    "sort": sort_i,
                    "opts": opts_json,
                    "hint": hint,
                },
            )


def upgrade() -> None:
    bind = op.get_bind()

    op.add_column(
        "category_core_fields",
        sa.Column("create_intent", sa.String(32), nullable=True),
    )
    op.create_index(
        "ix_category_core_fields_create_intent",
        "category_core_fields",
        ["create_intent"],
    )

    # Replace unique (category_id, field_key) with intent-aware expression unique.
    op.drop_constraint("uq_category_core_fields_key", "category_core_fields", type_="unique")
    op.execute(
        """
        CREATE UNIQUE INDEX ix_category_core_fields_cat_key_intent
        ON category_core_fields (
            category_id,
            field_key,
            (COALESCE(create_intent, ''))
        )
        """
    )

    op.add_column(
        "listings",
        sa.Column("job_intent", sa.String(32), nullable=True),
    )
    op.create_index("ix_listings_job_intent", "listings", ["job_intent"])
    # Tag existing jobs sector core_fields as hiring.
    from app.seeds.jobs_create_fields import (
        JOBS_V2_CANONICAL_SLUGS,
        JOBS_V2_META_SLUGS,
        build_jobs_create_core_fields,
    )
    from app.seeds.jobs_seeking_fields import build_jobs_seeking_core_fields
    from app.models.job_create_intent import HIRING, JOB_SEEKING

    hiring_slugs = set(JOBS_V2_CANONICAL_SLUGS) | set(JOBS_V2_META_SLUGS)
    for slug in hiring_slugs:
        row = bind.execute(
            text("SELECT id FROM categories WHERE slug = :slug"),
            {"slug": slug},
        ).fetchone()
        if row is None:
            continue
        bind.execute(
            text(
                """
                UPDATE category_core_fields
                SET create_intent = :intent
                WHERE category_id = :cid
                  AND create_intent IS NULL
                """
            ),
            {"cid": row[0], "intent": HIRING},
        )

    # Re-sync hiring schemas (parity) + seed job_seeking for canonical 20.
    hiring_map = build_jobs_create_core_fields()
    for slug in hiring_slugs:
        row = bind.execute(
            text("SELECT id FROM categories WHERE slug = :slug"),
            {"slug": slug},
        ).fetchone()
        if row is None:
            continue
        fields = hiring_map.get(slug)
        if not fields:
            continue
        # Drop stale hiring keys not in seed.
        wanted = {f[0] for f in fields}
        existing = bind.execute(
            text(
                """
                SELECT id, field_key FROM category_core_fields
                WHERE category_id = :cid AND create_intent = :intent
                """
            ),
            {"cid": row[0], "intent": HIRING},
        ).fetchall()
        for fid, fkey in existing:
            if fkey not in wanted:
                bind.execute(
                    text("DELETE FROM category_core_fields WHERE id = :id"),
                    {"id": fid},
                )
        _upsert_fields(bind, row[0], HIRING, fields)

    seeking_map = build_jobs_seeking_core_fields()
    for slug, fields in seeking_map.items():
        row = bind.execute(
            text("SELECT id FROM categories WHERE slug = :slug"),
            {"slug": slug},
        ).fetchone()
        if row is None:
            continue
        wanted = {f[0] for f in fields}
        existing = bind.execute(
            text(
                """
                SELECT id, field_key FROM category_core_fields
                WHERE category_id = :cid AND create_intent = :intent
                """
            ),
            {"cid": row[0], "intent": JOB_SEEKING},
        ).fetchall()
        for fid, fkey in existing:
            if fkey not in wanted:
                bind.execute(
                    text("DELETE FROM category_core_fields WHERE id = :id"),
                    {"id": fid},
                )
        _upsert_fields(bind, row[0], JOB_SEEKING, fields)

    # Soft-deactivate meta/legacy — no physical deletes; 0 listings on these leaves.
    for slug in _DEACTIVATE_SLUGS:
        bind.execute(
            text(
                """
                UPDATE categories
                SET is_active = false, updated_at = now()
                WHERE slug = :slug
                """
            ),
            {"slug": slug},
        )


def downgrade() -> None:
    bind = op.get_bind()
    from app.models.job_create_intent import JOB_SEEKING

    # Re-activate soft-deactivated leaves.
    for slug in _DEACTIVATE_SLUGS:
        bind.execute(
            text(
                """
                UPDATE categories
                SET is_active = true, updated_at = now()
                WHERE slug = :slug
                """
            ),
            {"slug": slug},
        )

    bind.execute(
        text(
            "DELETE FROM category_core_fields WHERE create_intent = :intent"
        ),
        {"intent": JOB_SEEKING},
    )
    bind.execute(
        text(
            """
            UPDATE category_core_fields
            SET create_intent = NULL
            WHERE create_intent IS NOT NULL
            """
        )
    )

    op.drop_index("ix_listings_job_intent", table_name="listings")
    op.drop_column("listings", "job_intent")

    op.execute("DROP INDEX IF EXISTS ix_category_core_fields_cat_key_intent")
    op.create_unique_constraint(
        "uq_category_core_fields_key",
        "category_core_fields",
        ["category_id", "field_key"],
    )
    op.drop_index(
        "ix_category_core_fields_create_intent",
        table_name="category_core_fields",
    )
    op.drop_column("category_core_fields", "create_intent")
