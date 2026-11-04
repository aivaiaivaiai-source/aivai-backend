"""Car Sale V2: engine_volume picker options (0.3–5.0 + Более 5.0→5.1).

Revision ID: w1x2y3z4a5b6
Revises: v0w1x2y3z4a5
Create Date: 2026-10-31

Updates category_core_fields.options for transport-car-sale engine_volume only.
Does not touch listing_field_values.
"""
from __future__ import annotations

import json

from alembic import op
from sqlalchemy import text

from app.seeds.car_sale_v2 import CAR_SALE_SLUG, _engine_volume_options

revision = "w1x2y3z4a5b6"
down_revision = "v0w1x2y3z4a5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    row = bind.execute(
        text("SELECT id FROM categories WHERE slug = :s"),
        {"s": CAR_SALE_SLUG},
    ).fetchone()
    if row is None:
        raise RuntimeError(f"{CAR_SALE_SLUG} missing")
    cid = int(row[0])
    opts = json.dumps(_engine_volume_options(), ensure_ascii=False)
    bind.execute(
        text(
            """
            UPDATE category_core_fields
            SET options = CAST(:opts AS jsonb),
                ai_hint = 'Объём в литрах',
                updated_at = now()
            WHERE category_id = :cid AND field_key = 'engine_volume'
            """
        ),
        {"cid": cid, "opts": opts},
    )


def downgrade() -> None:
    pass
