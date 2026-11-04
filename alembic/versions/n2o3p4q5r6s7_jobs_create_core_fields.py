"""Jobs create-listing core_fields + field_type multi_select/time.

Revision ID: n2o3p4q5r6s7
Revises: m1n2o3p4q5r6
Create Date: 2026-10-28

Pilot: backfill category_core_fields for L1 Работа sector leaves from
approved create intelligence (Flutter + JOB_SECTIONS). Does not delete
categories or listings. Does not touch legacy jobs-vacancies / jobs-resume
beyond leaving their existing rows intact.
"""
from __future__ import annotations

import json

from alembic import op
from sqlalchemy import text

revision = "n2o3p4q5r6s7"
down_revision = "m1n2o3p4q5r6"
branch_labels = None
depends_on = None

_NEW_FIELD_TYPES = ("multi_select", "time")


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        # ADD VALUE cannot be used in the same transaction as INSERTs that
        # reference the new labels — commit first (Alembic transactional DDL).
        for value in _NEW_FIELD_TYPES:
            op.execute(
                f"ALTER TYPE category_field_type_enum "
                f"ADD VALUE IF NOT EXISTS '{value}'"
            )
        # Force end of transaction so new enum labels become usable.
        op.execute("COMMIT")

    from app.seeds.jobs_create_fields import build_jobs_create_core_fields

    fields_by_slug = build_jobs_create_core_fields()
    for slug, fields in fields_by_slug.items():
        row = bind.execute(
            text("SELECT id FROM categories WHERE slug = :slug"),
            {"slug": slug},
        ).fetchone()
        if row is None:
            continue
        cat_id = row[0]
        wanted_keys = {f[0] for f in fields}

        existing = bind.execute(
            text(
                "SELECT id, field_key FROM category_core_fields "
                "WHERE category_id = :cid"
            ),
            {"cid": cat_id},
        ).fetchall()
        for eid, ekey in existing:
            if ekey not in wanted_keys:
                bind.execute(
                    text("DELETE FROM category_core_fields WHERE id = :id"),
                    {"id": eid},
                )

        for sort_i, field in enumerate(fields):
            key, label, ftype, required, options, hint = field
            opts_json = (
                json.dumps(options, ensure_ascii=False) if options else None
            )
            ftype_s = ftype.value if hasattr(ftype, "value") else str(ftype)
            existing_field = bind.execute(
                text(
                    "SELECT id FROM category_core_fields "
                    "WHERE category_id = :cid AND field_key = :key"
                ),
                {"cid": cat_id, "key": key},
            ).fetchone()
            if existing_field is None:
                bind.execute(
                    text(
                        """
                        INSERT INTO category_core_fields
                          (category_id, field_key, label, field_type,
                           is_required, sort_order, options, ai_hint)
                        VALUES
                          (:cid, :key, :label,
                           CAST(:ftype AS category_field_type_enum),
                           :req, :sort, CAST(:opts AS jsonb), :hint)
                        """
                    ),
                    {
                        "cid": cat_id,
                        "key": key,
                        "label": label,
                        "ftype": ftype_s,
                        "req": required,
                        "sort": sort_i,
                        "opts": opts_json,
                        "hint": hint,
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
                            updated_at = NOW()
                        WHERE id = :id
                        """
                    ),
                    {
                        "id": existing_field[0],
                        "label": label,
                        "ftype": ftype_s,
                        "req": required,
                        "sort": sort_i,
                        "opts": opts_json,
                        "hint": hint,
                    },
                )


def downgrade() -> None:
    """Remove jobs create core_fields for sector leaves only.

    Does not remove enum values (Postgres limitation) and does not touch
    legacy jobs-vacancies / jobs-resume rows.
    """
    from app.seeds.jobs_create_fields import expected_job_create_slugs

    bind = op.get_bind()
    for slug in expected_job_create_slugs():
        bind.execute(
            text(
                """
                DELETE FROM category_core_fields
                WHERE category_id = (
                    SELECT id FROM categories WHERE slug = :slug
                )
                """
            ),
            {"slug": slug},
        )
