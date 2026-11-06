"""Add work-mode ratios and make Jobs experience multi-select.

Revision ID: y5z6a7b8c9d0jobswmexp
Revises: x4y5z6a7b8c9jobssales
Create Date: 2026-11-06

Metadata only. Existing single experience and work_mode values stay as stored.
"""
from __future__ import annotations

import json

from alembic import op
from sqlalchemy import text

revision = "y5z6a7b8c9d0jobswmexp"
down_revision = "x4y5z6a7b8c9jobssales"
branch_labels = None
depends_on = None

_PREVIOUS_WORK_MODE = (
    "5/2",
    "6/1",
    "4/3",
    "3/3",
    "2/2",
    "По договорённости",
)


def _choices(labels: tuple[str, ...]) -> str:
    return json.dumps(
        {"choices": [{"value": label, "label": label} for label in labels]},
        ensure_ascii=False,
    )


def _filter_options(labels: tuple[str, ...]) -> str:
    return json.dumps(
        [{"value": label, "label": label} for label in labels],
        ensure_ascii=False,
    )


def _apply(labels: tuple[str, ...], experience_type: str) -> None:
    bind = op.get_bind()
    bind.execute(
        text(
            """
            UPDATE category_core_fields AS f
            SET options = CAST(:options AS jsonb),
                updated_at = NOW()
            FROM categories AS c
            WHERE f.category_id = c.id
              AND c.slug LIKE 'jobs-%'
              AND f.field_key = 'work_mode'
            """
        ),
        {"options": _choices(labels)},
    )
    bind.execute(
        text(
            """
            UPDATE category_core_fields AS f
            SET field_type = CAST(:field_type AS category_field_type_enum),
                updated_at = NOW()
            FROM categories AS c
            WHERE f.category_id = c.id
              AND c.slug LIKE 'jobs-%'
              AND f.field_key = 'experience'
            """
        ),
        {"field_type": experience_type},
    )
    bind.execute(
        text(
            """
            UPDATE category_filters AS f
            SET config = jsonb_set(
                    COALESCE(f.config, '{}'::jsonb),
                    '{options}',
                    CAST(:options AS jsonb),
                    true
                ),
                updated_at = NOW()
            FROM categories AS c
            WHERE f.category_id = c.id
              AND c.slug LIKE 'jobs-%'
              AND f.filter_key = 'work_mode'
            """
        ),
        {"options": _filter_options(labels)},
    )


def upgrade() -> None:
    from app.seeds.jobs_create_fields import WORK_MODE

    _apply(tuple(WORK_MODE), "multi_select")


def downgrade() -> None:
    _apply(_PREVIOUS_WORK_MODE, "enum")
