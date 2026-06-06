"""assistant conversations and messages

Revision ID: e6a1c34d8f03
Revises: d5f9a23b7c02
Create Date: 2026-05-21

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "e6a1c34d8f03"
down_revision: Union[str, None] = "d5f9a23b7c02"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_conversation_status = sa.Enum(
    "active",
    "closed",
    name="assistant_conversation_status_enum",
)
_message_role = sa.Enum(
    "user",
    "assistant",
    "system",
    name="assistant_message_role_enum",
)
_message_type = sa.Enum(
    "text",
    "voice",
    "draft",
    "preview",
    "moderation",
    "promotion",
    "system",
    name="assistant_message_type_enum",
)


def upgrade() -> None:
    _conversation_status.create(op.get_bind(), checkfirst=True)
    _message_role.create(op.get_bind(), checkfirst=True)
    _message_type.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "assistant_conversations",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("status", _conversation_status, nullable=False, server_default="active"),
        sa.Column(
            "state_json",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=False,
            server_default=sa.text("'{}'"),
        ),
        sa.Column(
            "last_activity_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_assistant_conversations_user_id"),
        "assistant_conversations",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_assistant_conversations_status"),
        "assistant_conversations",
        ["status"],
        unique=False,
    )
    op.create_index(
        op.f("ix_assistant_conversations_last_activity_at"),
        "assistant_conversations",
        ["last_activity_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_assistant_conversations_created_at"),
        "assistant_conversations",
        ["created_at"],
        unique=False,
    )

    op.create_table(
        "assistant_messages",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("conversation_id", sa.Integer(), nullable=False),
        sa.Column("role", _message_role, nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("message_type", _message_type, nullable=False, server_default="text"),
        sa.Column(
            "metadata_json",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=False,
            server_default=sa.text("'{}'"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["conversation_id"],
            ["assistant_conversations.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_assistant_messages_conversation_id"),
        "assistant_messages",
        ["conversation_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_assistant_messages_role"),
        "assistant_messages",
        ["role"],
        unique=False,
    )
    op.create_index(
        op.f("ix_assistant_messages_created_at"),
        "assistant_messages",
        ["created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_assistant_messages_created_at"), table_name="assistant_messages")
    op.drop_index(op.f("ix_assistant_messages_role"), table_name="assistant_messages")
    op.drop_index(op.f("ix_assistant_messages_conversation_id"), table_name="assistant_messages")
    op.drop_table("assistant_messages")
    op.drop_index(op.f("ix_assistant_conversations_created_at"), table_name="assistant_conversations")
    op.drop_index(
        op.f("ix_assistant_conversations_last_activity_at"),
        table_name="assistant_conversations",
    )
    op.drop_index(op.f("ix_assistant_conversations_status"), table_name="assistant_conversations")
    op.drop_index(op.f("ix_assistant_conversations_user_id"), table_name="assistant_conversations")
    op.drop_table("assistant_conversations")
    _message_type.drop(op.get_bind(), checkfirst=True)
    _message_role.drop(op.get_bind(), checkfirst=True)
    _conversation_status.drop(op.get_bind(), checkfirst=True)
