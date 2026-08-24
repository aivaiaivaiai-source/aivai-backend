"""drop ai agent tables

Revision ID: d4e5f6a7b8c9
Revises: c2d3e4f5a6b7
Create Date: 2026-08-19 23:35:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, None] = "c2d3e4f5a6b7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("DROP TABLE IF EXISTS ai_search_matches"))
    conn.execute(sa.text("DROP TABLE IF EXISTS ai_search_tasks"))
    conn.execute(sa.text("DROP TABLE IF EXISTS ai_messages"))
    conn.execute(sa.text("DROP TABLE IF EXISTS ai_sessions"))
    conn.execute(sa.text("DROP TABLE IF EXISTS ai_subscriptions"))
    conn.execute(sa.text("DROP TYPE IF EXISTS ai_message_type_enum"))
    conn.execute(sa.text("DROP TYPE IF EXISTS ai_subscription_status_enum"))
    conn.execute(sa.text("DROP TYPE IF EXISTS ai_agent_type_enum"))


def downgrade() -> None:
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
