"""Allow null category drafts already applied; add media_classifications.

Revision ID: o7e8f9a0b1c2
Revises: n6d7e8f9a0b1
Create Date: 2026-08-25
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "o7e8f9a0b1c2"
down_revision: Union[str, None] = "n6d7e8f9a0b1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    status_enum = postgresql.ENUM(
        "pending",
        "running",
        "succeeded",
        "failed",
        "no_match",
        "stale",
        "confirmed",
        name="media_classification_status_enum",
        create_type=False,
    )
    band_enum = postgresql.ENUM(
        "high",
        "medium",
        "low",
        "none",
        name="media_classification_confidence_band_enum",
        create_type=False,
    )
    status_enum.create(op.get_bind(), checkfirst=True)
    band_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "media_classifications",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("listing_id", sa.Integer(), nullable=False),
        sa.Column("idempotency_key", sa.String(length=256), nullable=False),
        sa.Column("media_set_fingerprint", sa.String(length=128), nullable=False),
        sa.Column("classifier_version", sa.String(length=64), nullable=False),
        sa.Column(
            "status",
            status_enum,
            server_default="pending",
            nullable=False,
        ),
        sa.Column(
            "confidence_band",
            band_enum,
            server_default="none",
            nullable=False,
        ),
        sa.Column("top_confidence", sa.Float(), nullable=True),
        sa.Column(
            "candidates_json",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "evidence_media_ids",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column("images_inspected", sa.Integer(), server_default="0", nullable=False),
        sa.Column("selected_category_id", sa.Integer(), nullable=True),
        sa.Column("predicted_category_id", sa.Integer(), nullable=True),
        sa.Column("user_overridden", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("lease_owner", sa.String(length=128), nullable=True),
        sa.Column("lease_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("available_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("attempt_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("last_error_code", sa.String(length=64), nullable=True),
        sa.Column("last_error_message", sa.String(length=512), nullable=True),
        sa.Column("queue_wait_ms", sa.Integer(), nullable=True),
        sa.Column("inference_ms", sa.Integer(), nullable=True),
        sa.Column("total_ms", sa.Integer(), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("suggested_attributes_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["listing_id"], ["listings.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["selected_category_id"], ["categories.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["predicted_category_id"], ["categories.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("idempotency_key", name="uq_media_classifications_idempotency_key"),
    )
    op.create_index(
        "ix_media_classifications_listing_id",
        "media_classifications",
        ["listing_id"],
    )
    op.create_index(
        "ix_media_classifications_media_set_fingerprint",
        "media_classifications",
        ["media_set_fingerprint"],
    )
    op.create_index(
        "ix_media_classifications_status",
        "media_classifications",
        ["status"],
    )


def downgrade() -> None:
    op.drop_index("ix_media_classifications_status", table_name="media_classifications")
    op.drop_index(
        "ix_media_classifications_media_set_fingerprint",
        table_name="media_classifications",
    )
    op.drop_index("ix_media_classifications_listing_id", table_name="media_classifications")
    op.drop_table("media_classifications")
    op.execute("DROP TYPE IF EXISTS media_classification_status_enum")
    op.execute("DROP TYPE IF EXISTS media_classification_confidence_band_enum")
