"""ai sessions last_read_message_id

Revision ID: h9d0e1f2a3b4
Revises: g7b8c9d0e1f2
Create Date: 2026-08-21 12:55:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "h9d0e1f2a3b4"
down_revision: Union[str, None] = "g7b8c9d0e1f2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text(
        "ALTER TABLE ai_sessions "
        "ADD COLUMN IF NOT EXISTS last_read_message_id INTEGER"
    ))
    # Existing threads: don't show historical messages as unread.
    conn.execute(sa.text(
        """
        UPDATE ai_sessions s
        SET last_read_message_id = (
            SELECT MAX(m.id) FROM ai_messages m WHERE m.session_id = s.id
        )
        WHERE s.last_read_message_id IS NULL
        """
    ))


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text(
        "ALTER TABLE ai_sessions DROP COLUMN IF EXISTS last_read_message_id"
    ))
