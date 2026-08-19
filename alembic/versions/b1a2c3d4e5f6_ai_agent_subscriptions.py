"""ai agent subscriptions

Revision ID: b1a2c3d4e5f6
Revises: a9c2e71f4b18
Create Date: 2026-08-19 15:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b1a2c3d4e5f6"
down_revision: Union[str, None] = "a9c2e71f4b18"
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
    conn.execute(sa.text(
        "ALTER TYPE wallet_ledger_kind_enum ADD VALUE IF NOT EXISTS 'ai_subscription_charge'"
    ))

    conn.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS ai_subscriptions (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id),
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
    conn.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_ai_subscriptions_user_id ON ai_subscriptions(user_id)"))
    conn.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_ai_subscriptions_agent_type ON ai_subscriptions(agent_type)"))
    conn.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_ai_subscriptions_expires_at ON ai_subscriptions(expires_at)"))
    conn.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_ai_subscriptions_created_at ON ai_subscriptions(created_at)"))

    conn.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS ai_sessions (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id),
            agent_type ai_agent_type_enum NOT NULL,
            subscription_id INTEGER REFERENCES ai_subscriptions(id),
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """))
    conn.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_ai_sessions_user_id ON ai_sessions(user_id)"))
    conn.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_ai_sessions_agent_type ON ai_sessions(agent_type)"))
    conn.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_ai_sessions_created_at ON ai_sessions(created_at)"))

    conn.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS ai_messages (
            id SERIAL PRIMARY KEY,
            session_id INTEGER NOT NULL REFERENCES ai_sessions(id) ON DELETE CASCADE,
            role assistant_message_role_enum NOT NULL,
            content TEXT NOT NULL,
            message_type ai_message_type_enum NOT NULL DEFAULT 'text',
            metadata_json JSON NOT NULL DEFAULT '{}',
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """))
    conn.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_ai_messages_session_id ON ai_messages(session_id)"))
    conn.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_ai_messages_created_at ON ai_messages(created_at)"))


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS ai_messages")
    op.execute("DROP TABLE IF EXISTS ai_sessions")
    op.execute("DROP TABLE IF EXISTS ai_subscriptions")
    op.execute("DROP TYPE IF EXISTS ai_message_type_enum")
    op.execute("DROP TYPE IF EXISTS ai_subscription_status_enum")
    op.execute("DROP TYPE IF EXISTS ai_agent_type_enum")
