"""Remove user-facing Search has_photo filters globally.

Revision ID: e5f6a7b8c9d0nophoto
Revises: d4e5f6a7b8c9specv2
Create Date: 2026-11-02

Photo is required at publication. Keep Listings API has_photo query capability
for SavedSearch / legacy clients; only drop category_filters UI rows.
"""
from __future__ import annotations

from alembic import op
from sqlalchemy import text

revision = "e5f6a7b8c9d0nophoto"
down_revision = "d4e5f6a7b8c9specv2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        text("DELETE FROM category_filters WHERE filter_key = 'has_photo'")
    )


def downgrade() -> None:
    # Intentionally empty: re-seeding photo Search UI is not desired.
    pass
