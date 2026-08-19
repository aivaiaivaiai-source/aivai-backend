"""ai search tasks for background monitoring

Revision ID: c2d3e4f5a6b7
Revises: b1a2c3d4e5f6
Create Date: 2026-08-19 22:20:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c2d3e4f5a6b7"
down_revision: Union[str, None] = "b1a2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()

    conn.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS ai_search_tasks (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            agent_type ai_agent_type_enum NOT NULL,
            subscription_id INTEGER NOT NULL REFERENCES ai_subscriptions(id) ON DELETE CASCADE,
            session_id INTEGER NOT NULL REFERENCES ai_sessions(id) ON DELETE CASCADE,
            criteria_json JSONB NOT NULL DEFAULT '{}',
            category_ids JSONB NOT NULL DEFAULT '[]',
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            source_text TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """))
    conn.execute(sa.text(
        "CREATE INDEX IF NOT EXISTS ix_ai_search_tasks_user_id ON ai_search_tasks(user_id)"
    ))
    conn.execute(sa.text(
        "CREATE INDEX IF NOT EXISTS ix_ai_search_tasks_agent_type ON ai_search_tasks(agent_type)"
    ))
    conn.execute(sa.text(
        "CREATE INDEX IF NOT EXISTS ix_ai_search_tasks_subscription_id "
        "ON ai_search_tasks(subscription_id)"
    ))
    conn.execute(sa.text(
        "CREATE INDEX IF NOT EXISTS ix_ai_search_tasks_session_id ON ai_search_tasks(session_id)"
    ))
    conn.execute(sa.text(
        "CREATE INDEX IF NOT EXISTS ix_ai_search_tasks_user_agent_active "
        "ON ai_search_tasks(user_id, agent_type, is_active)"
    ))
    conn.execute(sa.text(
        "CREATE INDEX IF NOT EXISTS ix_ai_search_tasks_criteria_gin "
        "ON ai_search_tasks USING gin (criteria_json)"
    ))

    conn.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS ai_search_matches (
            id SERIAL PRIMARY KEY,
            task_id INTEGER NOT NULL REFERENCES ai_search_tasks(id) ON DELETE CASCADE,
            listing_id INTEGER NOT NULL REFERENCES listings(id) ON DELETE CASCADE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT uq_ai_search_matches_task_listing UNIQUE (task_id, listing_id)
        )
    """))
    conn.execute(sa.text(
        "CREATE INDEX IF NOT EXISTS ix_ai_search_matches_task_id ON ai_search_matches(task_id)"
    ))
    conn.execute(sa.text(
        "CREATE INDEX IF NOT EXISTS ix_ai_search_matches_listing_id "
        "ON ai_search_matches(listing_id)"
    ))


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("DROP TABLE IF EXISTS ai_search_matches"))
    conn.execute(sa.text("DROP TABLE IF EXISTS ai_search_tasks"))
