"""add message read status and attachments

Revision ID: eec1f2ab3cd4
Revises: d7acc9fa5744
Create Date: 2026-05-03

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "eec1f2ab3cd4"
down_revision: Union[str, Sequence[str], None] = "d7acc9fa5744"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "messages",
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_table(
        "message_attachments",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("message_id", sa.Integer(), nullable=False),
        sa.Column("media_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["media_id"], ["media.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["message_id"], ["messages.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("message_id", "media_id", name="uq_message_attachment_media"),
    )
    op.create_index(op.f("ix_message_attachments_message_id"), "message_attachments", ["message_id"], unique=False)
    op.create_index(op.f("ix_message_attachments_media_id"), "message_attachments", ["media_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_message_attachments_media_id"), table_name="message_attachments")
    op.drop_index(op.f("ix_message_attachments_message_id"), table_name="message_attachments")
    op.drop_table("message_attachments")
    op.drop_column("messages", "read_at")
