"""recreate ai agent tables with constraints

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-08-20 15:30:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e5f6a7b8c9d0"
down_revision: Union[str, None] = "d4e5f6a7b8c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()

    conn.execute(sa.text(
        "DO $$ BEGIN CREATE TYPE ai_agent_type_enum AS ENUM ('ai_realtor','ai_auto','ai_hr'); "
        "EXCEPTION WHEN duplicate_object THEN NULL; END $$"
    ))
    conn.execute(sa.text(
        "DO $$ BEGIN CREATE TYPE ai_subscription_status_enum AS ENUM ('active','expired','cancelled'); "
        "EXCEPTION WHEN duplicate_object THEN NULL; END $$"
    ))
    conn.execute(sa.text(
        "DO $$ BEGIN CREATE TYPE ai_message_type_enum AS ENUM ('text','listing_link'); "
        "EXCEPTION WHEN duplicate_object THEN NULL; END $$"
    ))

    conn.execute(sa.text("""
        CREATE TABLE ai_subscriptions (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            agent_type ai_agent_type_enum NOT NULL,
            status ai_subscription_status_enum NOT NULL DEFAULT 'active',
            price_som INTEGER NOT NULL,
            starts_at TIMESTAMPTZ NOT NULL,
            expires_at TIMESTAMPTZ NOT NULL,
            messages_today INTEGER NOT NULL DEFAULT 0,
            messages_today_reset DATE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """))
    conn.execute(sa.text("CREATE INDEX ix_ai_subscriptions_user_id ON ai_subscriptions(user_id)"))
    conn.execute(sa.text("CREATE INDEX ix_ai_subscriptions_agent_type ON ai_subscriptions(agent_type)"))
    conn.execute(sa.text("CREATE INDEX ix_ai_subscriptions_expires_at ON ai_subscriptions(expires_at)"))
    conn.execute(sa.text(
        "CREATE UNIQUE INDEX uq_ai_subscriptions_active_user_agent "
        "ON ai_subscriptions(user_id, agent_type) "
        "WHERE status = 'active'"
    ))

    conn.execute(sa.text("""
        CREATE TABLE ai_sessions (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            agent_type ai_agent_type_enum NOT NULL,
            subscription_id INTEGER REFERENCES ai_subscriptions(id) ON DELETE SET NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT uq_ai_sessions_user_agent UNIQUE (user_id, agent_type)
        )
    """))
    conn.execute(sa.text("CREATE INDEX ix_ai_sessions_user_id ON ai_sessions(user_id)"))

    conn.execute(sa.text("""
        CREATE TABLE ai_messages (
            id SERIAL PRIMARY KEY,
            session_id INTEGER NOT NULL REFERENCES ai_sessions(id) ON DELETE CASCADE,
            role assistant_message_role_enum NOT NULL,
            content TEXT NOT NULL,
            message_type ai_message_type_enum NOT NULL DEFAULT 'text',
            metadata_json JSONB NOT NULL DEFAULT '{}',
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """))
    conn.execute(sa.text("CREATE INDEX ix_ai_messages_session_id ON ai_messages(session_id)"))
    conn.execute(sa.text("CREATE INDEX ix_ai_messages_created_at ON ai_messages(created_at)"))

    conn.execute(sa.text("""
        CREATE TABLE ai_search_tasks (
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
        "CREATE INDEX ix_ai_search_tasks_user_agent_active "
        "ON ai_search_tasks(user_id, agent_type, is_active)"
    ))

    conn.execute(sa.text("""
        CREATE TABLE ai_search_matches (
            id SERIAL PRIMARY KEY,
            task_id INTEGER NOT NULL REFERENCES ai_search_tasks(id) ON DELETE CASCADE,
            listing_id INTEGER NOT NULL REFERENCES listings(id) ON DELETE CASCADE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT uq_ai_search_matches_task_listing UNIQUE (task_id, listing_id)
        )
    """))
    conn.execute(sa.text("CREATE INDEX ix_ai_search_matches_listing_id ON ai_search_matches(listing_id)"))


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("DROP TABLE IF EXISTS ai_search_matches"))
    conn.execute(sa.text("DROP TABLE IF EXISTS ai_search_tasks"))
    conn.execute(sa.text("DROP TABLE IF EXISTS ai_messages"))
    conn.execute(sa.text("DROP TABLE IF EXISTS ai_sessions"))
    conn.execute(sa.text("DROP TABLE IF EXISTS ai_subscriptions"))
    conn.execute(sa.text("DROP TYPE IF EXISTS ai_message_type_enum"))
    conn.execute(sa.text("DROP TYPE IF EXISTS ai_subscription_status_enum"))
    conn.execute(sa.text("DROP TYPE IF EXISTS ai_agent_type_enum"))
