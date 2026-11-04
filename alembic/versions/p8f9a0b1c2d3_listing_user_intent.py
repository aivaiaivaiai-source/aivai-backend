"""Add listing_user_intents for hybrid classification (Substage 3C-1).

Revision ID: p8f9a0b1c2d3
Revises: o7e8f9a0b1c2
Create Date: 2026-08-29
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "p8f9a0b1c2d3"
down_revision: Union[str, None] = "o7e8f9a0b1c2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    status_enum = postgresql.ENUM(
        "missing",
        "provided",
        name="listing_user_intent_status_enum",
        create_type=False,
    )
    status_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "listing_user_intents",
        sa.Column("listing_id", sa.Integer(), nullable=False),
        sa.Column("raw_intent_text", sa.Text(), nullable=True),
        sa.Column(
            "intent_status",
            status_enum,
            nullable=False,
            server_default="missing",
        ),
        sa.Column(
            "intent_fingerprint",
            sa.String(length=128),
            nullable=False,
            server_default="",
        ),
        sa.Column(
            "intent_version",
            sa.Integer(),
            nullable=False,
            server_default="0",
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
            ["listing_id"],
            ["listings.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("listing_id"),
    )


def downgrade() -> None:
    op.drop_table("listing_user_intents")
    postgresql.ENUM(
        name="listing_user_intent_status_enum",
    ).drop(op.get_bind(), checkfirst=True)
