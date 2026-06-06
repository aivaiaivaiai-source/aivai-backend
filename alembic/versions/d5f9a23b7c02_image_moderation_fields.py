"""image moderation fields on media

Revision ID: d5f9a23b7c02
Revises: c4d8e12f6a01
Create Date: 2026-05-21

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "d5f9a23b7c02"
down_revision: Union[str, None] = "c4d8e12f6a01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_moderation_status = sa.Enum(
    "pending",
    "approved",
    "rejected",
    "moderation_queue",
    name="media_moderation_status_enum",
)


def upgrade() -> None:
    _moderation_status.create(op.get_bind(), checkfirst=True)
    op.add_column(
        "media",
        sa.Column(
            "moderation_status",
            _moderation_status,
            nullable=False,
            server_default="approved",
        ),
    )
    op.add_column(
        "media",
        sa.Column("moderation_reason", sa.String(length=512), nullable=True),
    )
    op.add_column(
        "media",
        sa.Column("moderated_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("media", "moderated_at")
    op.drop_column("media", "moderation_reason")
    op.drop_column("media", "moderation_status")
    _moderation_status.drop(op.get_bind(), checkfirst=True)
