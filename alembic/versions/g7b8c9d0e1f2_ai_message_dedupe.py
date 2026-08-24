"""ai agent message dedupe + history indexes

Revision ID: g7b8c9d0e1f2
Revises: f6a7b8c9d0e1
Create Date: 2026-08-20 18:20:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "g7b8c9d0e1f2"
down_revision: Union[str, None] = "f6a7b8c9d0e1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text(
        "ALTER TABLE ai_messages ADD COLUMN IF NOT EXISTS dedupe_key VARCHAR(128)"
    ))
    conn.execute(sa.text(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_ai_messages_session_dedupe "
        "ON ai_messages(session_id, dedupe_key) "
        "WHERE dedupe_key IS NOT NULL"
    ))
    conn.execute(sa.text(
        "CREATE INDEX IF NOT EXISTS ix_ai_messages_session_id_id "
        "ON ai_messages(session_id, id)"
    ))


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("DROP INDEX IF EXISTS ix_ai_messages_session_id_id"))
    conn.execute(sa.text("DROP INDEX IF EXISTS uq_ai_messages_session_dedupe"))
    conn.execute(sa.text("ALTER TABLE ai_messages DROP COLUMN IF EXISTS dedupe_key"))
