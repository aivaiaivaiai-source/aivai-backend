"""chat media attachments

Revision ID: c91f4ab12d33
Revises: g8c4d56e0a12
Create Date: 2026-08-18 13:10:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c91f4ab12d33"
down_revision: Union[str, None] = "g8c4d56e0a12"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("media", sa.Column("chat_id", sa.Integer(), nullable=True))
    op.create_index(op.f("ix_media_chat_id"), "media", ["chat_id"], unique=False)
    op.create_foreign_key(
        "fk_media_chat_id_chats",
        "media",
        "chats",
        ["chat_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint("fk_media_chat_id_chats", "media", type_="foreignkey")
    op.drop_index(op.f("ix_media_chat_id"), table_name="media")
    op.drop_column("media", "chat_id")
