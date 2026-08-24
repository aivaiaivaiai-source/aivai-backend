"""ai agent scale indexes

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-08-20 18:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f6a7b8c9d0e1"
down_revision: Union[str, None] = "e5f6a7b8c9d0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    # Active tasks scanned on every new listing publish (via match worker).
    conn.execute(sa.text(
        "CREATE INDEX IF NOT EXISTS ix_ai_search_tasks_active_id "
        "ON ai_search_tasks(id DESC) WHERE is_active = TRUE"
    ))
    # JSONB category filter for match candidates.
    conn.execute(sa.text(
        "CREATE INDEX IF NOT EXISTS ix_ai_search_tasks_category_ids_gin "
        "ON ai_search_tasks USING GIN (category_ids jsonb_path_ops)"
    ))
    # Maintenance worker: expire active subscriptions by expires_at.
    conn.execute(sa.text(
        "CREATE INDEX IF NOT EXISTS ix_ai_subscriptions_active_expires "
        "ON ai_subscriptions(expires_at) WHERE status = 'active'"
    ))
    # Dedup lookup: matches for a listing across candidate tasks.
    conn.execute(sa.text(
        "CREATE INDEX IF NOT EXISTS ix_ai_search_matches_listing_task "
        "ON ai_search_matches(listing_id, task_id)"
    ))


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("DROP INDEX IF EXISTS ix_ai_search_matches_listing_task"))
    conn.execute(sa.text("DROP INDEX IF EXISTS ix_ai_subscriptions_active_expires"))
    conn.execute(sa.text("DROP INDEX IF EXISTS ix_ai_search_tasks_category_ids_gin"))
    conn.execute(sa.text("DROP INDEX IF EXISTS ix_ai_search_tasks_active_id"))
