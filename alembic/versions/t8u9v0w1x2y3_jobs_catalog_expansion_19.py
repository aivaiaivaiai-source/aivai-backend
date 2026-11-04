"""Jobs final catalog: 19 sectors, expanded roles, work_mode search, abroad off.

Revision ID: t8u9v0w1x2y3
Revises: s7t8u9v0w1x2
Create Date: 2026-10-30

- Soft-deactivate jobs-rabota-za-rubezhom (0 listings; geography ≠ profession)
- Re-upsert hiring/seeking core_fields role catalogs for Jobs leaves
- Re-upsert hiring/seeking search filters (incl. work_mode on hiring)
- No physical category deletes; other L1 untouched
"""
from __future__ import annotations

import json

from alembic import op
from sqlalchemy import text

revision = "t8u9v0w1x2y3"
down_revision = "s7t8u9v0w1x2"
branch_labels = None
depends_on = None

_ABROAD_SLUG = "jobs-rabota-za-rubezhom"


def _upsert_fields(bind, cat_id: int, intent: str, fields) -> None:
    wanted = {f[0] for f in fields}
    existing = bind.execute(
        text(
            """
            SELECT id, field_key FROM category_core_fields
            WHERE category_id = :cid AND COALESCE(create_intent, '') = :intent
            """
        ),
        {"cid": cat_id, "intent": intent},
    ).fetchall()
    for fid, fkey in existing:
        if fkey not in wanted:
            bind.execute(
                text("DELETE FROM category_core_fields WHERE id = :id"),
                {"id": fid},
            )
    for sort_i, field in enumerate(fields):
        key, label, ftype, required, options, hint = field
        ftype_val = ftype.value if hasattr(ftype, "value") else str(ftype)
        opts_json = json.dumps(options, ensure_ascii=False) if options else None
        found = bind.execute(
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
        if found is None:
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
                    "id": found[0],
                    "label": label,
                    "ftype": ftype_val,
                    "req": required,
                    "sort": sort_i,
                    "opts": opts_json,
                    "hint": hint,
                },
            )


def _upsert_search_filters(bind, cat_id: int, intent: str, filters) -> None:
    wanted = {f[0] for f in filters}
    existing = bind.execute(
        text(
            """
            SELECT id, filter_key FROM category_filters
            WHERE category_id = :cid AND search_intent = :intent
            """
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
                """
                SELECT id FROM category_filters
                WHERE category_id = :cid AND filter_key = :key
                  AND search_intent = :intent
                """
            ),
            {"cid": cat_id, "key": key, "intent": intent},
        ).fetchone()
        if found:
            bind.execute(
                text(
                    """
                    UPDATE category_filters SET label = :label,
                        filter_type = CAST(:ftype AS category_filter_type_enum),
                        sort_order = :sort_order, config = CAST(:config AS jsonb),
                        updated_at = NOW() WHERE id = :id
                    """
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
                    """
                    INSERT INTO category_filters
                    (category_id, filter_key, label, filter_type, sort_order,
                     config, search_intent, created_at, updated_at)
                    VALUES
                    (:cid, :key, :label, CAST(:ftype AS category_filter_type_enum),
                     :sort_order, CAST(:config AS jsonb), :intent, NOW(), NOW())
                    """
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


def upgrade() -> None:
    bind = op.get_bind()
    from app.models.job_create_intent import HIRING, JOB_SEEKING
    from app.seeds.jobs_create_fields import (
        JOBS_V2_CANONICAL_SLUGS,
        JOBS_V2_META_SLUGS,
        build_jobs_create_core_fields,
    )
    from app.seeds.jobs_search_filters import build_jobs_search_filters
    from app.seeds.jobs_seeking_fields import build_jobs_seeking_core_fields

    # Soft-deactivate abroad sector (geography handled via geo country picker).
    bind.execute(
        text(
            """
            UPDATE categories
            SET is_active = false, updated_at = now()
            WHERE slug = :slug
            """
        ),
        {"slug": _ABROAD_SLUG},
    )

    hiring_map = build_jobs_create_core_fields()
    seeking_map = build_jobs_seeking_core_fields()
    # Re-sync canonical + meta hiring; seeking only canonical (19).
    hiring_slugs = set(JOBS_V2_CANONICAL_SLUGS) | set(JOBS_V2_META_SLUGS) | {_ABROAD_SLUG}
    for slug in hiring_slugs:
        row = bind.execute(
            text("SELECT id FROM categories WHERE slug = :slug"),
            {"slug": slug},
        ).fetchone()
        if row is None:
            continue
        fields = hiring_map.get(slug)
        if fields:
            _upsert_fields(bind, int(row[0]), HIRING, fields)

    for slug, fields in seeking_map.items():
        row = bind.execute(
            text("SELECT id FROM categories WHERE slug = :slug"),
            {"slug": slug},
        ).fetchone()
        if row is None:
            continue
        _upsert_fields(bind, int(row[0]), JOB_SEEKING, fields)

    # Search filters only for active canonical 19.
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
            _upsert_search_filters(bind, cat_id, intent, filters)

    # Drop search filters for inactive abroad (no new search via this sector).
    abroad = bind.execute(
        text("SELECT id FROM categories WHERE slug = :slug"),
        {"slug": _ABROAD_SLUG},
    ).fetchone()
    if abroad:
        bind.execute(
            text("DELETE FROM category_filters WHERE category_id = :cid"),
            {"cid": int(abroad[0])},
        )


def downgrade() -> None:
    bind = op.get_bind()
    bind.execute(
        text(
            """
            UPDATE categories
            SET is_active = true, updated_at = now()
            WHERE slug = :slug
            """
        ),
        {"slug": _ABROAD_SLUG},
    )
