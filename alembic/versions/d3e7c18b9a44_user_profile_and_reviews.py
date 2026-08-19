"""user profile fields and reviews

Revision ID: d3e7c18b9a44
Revises: c91f4ab12d33
Create Date: 2026-08-18 13:20:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d3e7c18b9a44"
down_revision: Union[str, None] = "c91f4ab12d33"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("city", sa.String(length=128), nullable=True))
    op.add_column("users", sa.Column("avatar_url", sa.String(length=2048), nullable=True))
    op.create_table(
        "user_reviews",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("author_id", sa.Integer(), nullable=False),
        sa.Column("subject_id", sa.Integer(), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("comment", sa.Text(), nullable=False),
        sa.Column("owner_reply", sa.String(length=2000), nullable=True),
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
        sa.ForeignKeyConstraint(["author_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["subject_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("author_id", "subject_id", name="uq_review_author_subject"),
    )
    op.create_index(op.f("ix_user_reviews_author_id"), "user_reviews", ["author_id"], unique=False)
    op.create_index(
        op.f("ix_user_reviews_subject_id"),
        "user_reviews",
        ["subject_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_user_reviews_created_at"),
        "user_reviews",
        ["created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_user_reviews_created_at"), table_name="user_reviews")
    op.drop_index(op.f("ix_user_reviews_subject_id"), table_name="user_reviews")
    op.drop_index(op.f("ix_user_reviews_author_id"), table_name="user_reviews")
    op.drop_table("user_reviews")
    op.drop_column("users", "avatar_url")
    op.drop_column("users", "city")
