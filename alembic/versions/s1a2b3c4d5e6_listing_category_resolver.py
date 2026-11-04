"""Add listing_category_resolver_results for shadow Category Resolver (3C-3).

Revision ID: s1a2b3c4d5e6
Revises: r0a1b2c3d4e5
Create Date: 2026-08-31
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "s1a2b3c4d5e6"
down_revision: Union[str, None] = "r0a1b2c3d4e5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    status_enum = postgresql.ENUM(
        "pending",
        "processing",
        "suggested",
        "ambiguous",
        "no_match",
        "failed",
        "stale",
        name="category_resolver_status_enum",
        create_type=False,
    )
    status_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "listing_category_resolver_results",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("listing_id", sa.Integer(), nullable=False),
        sa.Column("idempotency_key", sa.String(length=256), nullable=False),
        sa.Column("input_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("catalog_snapshot_hash", sa.String(length=64), nullable=False),
        sa.Column("intent_fingerprint", sa.String(length=64), nullable=False, server_default=""),
        sa.Column("intent_version", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("media_set_fingerprint", sa.String(length=128), nullable=False, server_default=""),
        sa.Column("visual_evidence_id", sa.Integer(), nullable=True),
        sa.Column("visual_model_version", sa.String(length=64), nullable=True),
        sa.Column("visual_prompt_version", sa.String(length=64), nullable=True),
        sa.Column("visual_calibration_version", sa.String(length=64), nullable=True),
        sa.Column("resolver_version", sa.String(length=64), nullable=False),
        sa.Column(
            "status",
            status_enum,
            nullable=False,
            server_default="pending",
        ),
        sa.Column("suggested_category_id", sa.Integer(), nullable=True),
        sa.Column("suggested_slug", sa.String(length=160), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("needs_confirmation", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "candidate_path_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
        sa.Column(
            "alternatives_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
        sa.Column(
            "evidence_summary_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column(
            "intent_semantics_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column("error_code", sa.String(length=64), nullable=True),
        sa.Column("error_message", sa.String(length=512), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
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
        sa.ForeignKeyConstraint(["listing_id"], ["listings.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["visual_evidence_id"], ["listing_visual_evidence.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["suggested_category_id"], ["categories.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("idempotency_key", name="uq_listing_category_resolver_idempotency_key"),
    )
    op.create_index(
        "ix_listing_category_resolver_listing_id",
        "listing_category_resolver_results",
        ["listing_id"],
    )
    op.create_index(
        "ix_listing_category_resolver_input_fingerprint",
        "listing_category_resolver_results",
        ["input_fingerprint"],
    )
    op.create_index(
        "ix_listing_category_resolver_status",
        "listing_category_resolver_results",
        ["status"],
    )


def downgrade() -> None:
    op.drop_index("ix_listing_category_resolver_status", table_name="listing_category_resolver_results")
    op.drop_index("ix_listing_category_resolver_input_fingerprint", table_name="listing_category_resolver_results")
    op.drop_index("ix_listing_category_resolver_listing_id", table_name="listing_category_resolver_results")
    op.drop_table("listing_category_resolver_results")
    postgresql.ENUM(name="category_resolver_status_enum").drop(op.get_bind(), checkfirst=True)
