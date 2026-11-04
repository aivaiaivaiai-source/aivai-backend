"""Add listing_visual_evidence + listings.description_mode (Substage 3C-2)."""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "q9a0b1c2d3e4"
down_revision: Union[str, None] = "p8f9a0b1c2d3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    status_enum = postgresql.ENUM(
        "pending",
        "processing",
        "ready",
        "no_match",
        "failed",
        "stale",
        name="visual_evidence_status_enum",
        create_type=False,
    )
    mode_enum = postgresql.ENUM(
        "ai_assisted",
        "manual",
        name="listing_description_mode_enum",
        create_type=False,
    )
    status_enum.create(op.get_bind(), checkfirst=True)
    mode_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "listing_visual_evidence",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("listing_id", sa.Integer(), nullable=False),
        sa.Column("idempotency_key", sa.String(length=256), nullable=False),
        sa.Column("media_set_fingerprint", sa.String(length=128), nullable=False),
        sa.Column("model_version", sa.String(length=64), nullable=False),
        sa.Column("prompt_version", sa.String(length=64), nullable=False),
        sa.Column("prompt_hash", sa.String(length=64), nullable=True),
        sa.Column(
            "status",
            status_enum,
            server_default="pending",
            nullable=False,
        ),
        sa.Column(
            "observations_json",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="[]",
            nullable=False,
        ),
        sa.Column(
            "top_concepts_json",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="[]",
            nullable=False,
        ),
        sa.Column("images_inspected", sa.Integer(), server_default="0", nullable=False),
        sa.Column("lease_owner", sa.String(length=128), nullable=True),
        sa.Column("lease_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("available_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("attempt_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("last_error_code", sa.String(length=64), nullable=True),
        sa.Column("last_error_message", sa.String(length=512), nullable=True),
        sa.Column("queue_wait_ms", sa.Integer(), nullable=True),
        sa.Column("inference_ms", sa.Integer(), nullable=True),
        sa.Column("processing_ms", sa.Integer(), nullable=True),
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
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("idempotency_key", name="uq_listing_visual_evidence_idempotency_key"),
    )
    op.create_index(
        "ix_listing_visual_evidence_listing_id",
        "listing_visual_evidence",
        ["listing_id"],
    )
    op.create_index(
        "ix_listing_visual_evidence_media_set_fingerprint",
        "listing_visual_evidence",
        ["media_set_fingerprint"],
    )
    op.create_index(
        "ix_listing_visual_evidence_status",
        "listing_visual_evidence",
        ["status"],
    )
    op.add_column(
        "listings",
        sa.Column("description_mode", mode_enum, nullable=True),
    )


def downgrade() -> None:
    op.drop_column("listings", "description_mode")
    op.drop_index("ix_listing_visual_evidence_status", table_name="listing_visual_evidence")
    op.drop_index(
        "ix_listing_visual_evidence_media_set_fingerprint",
        table_name="listing_visual_evidence",
    )
    op.drop_index("ix_listing_visual_evidence_listing_id", table_name="listing_visual_evidence")
    op.drop_table("listing_visual_evidence")
    op.execute("DROP TYPE IF EXISTS listing_description_mode_enum")
    op.execute("DROP TYPE IF EXISTS visual_evidence_status_enum")
