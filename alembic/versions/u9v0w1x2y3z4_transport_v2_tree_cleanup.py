"""Transport V2 Stage 1: canonical L2 tree cleanup.

Revision ID: u9v0w1x2y3z4
Revises: t8u9v0w1x2y3
Create Date: 2026-10-30

- Activate transport-auto-services + keep 10 children active
- Re-parent Автобусы/Микроавтобусы under buses L2 (preserve IDs)
- Soft-deactivate buyback children + leftover commercial actives
- Unique sort_order for 15 canonical active L2
- No DELETE; no listing category_id remaps (0 listings on affected nodes)
"""
from __future__ import annotations

from alembic import op
from sqlalchemy import text

revision = "u9v0w1x2y3z4"
down_revision = "t8u9v0w1x2y3"
branch_labels = None
depends_on = None

# (slug, name, sort_order)
_L2_ACTIVE: list[tuple[str, str, int]] = [
    ("transport-car-sale", "Продажа авто", 10),
    ("transport-auto-parts", "Автозапчасти", 20),
    ("transport-accessories-tuning", "Аксессуары и тюнинг", 30),
    ("transport-tires-wheels", "Шины и диски", 40),
    ("transport-auto-services", "Автоуслуги", 50),
    ("transport-moto-tech", "Мототехника", 60),
    ("transport-electric", "Электротранспорт", 70),
    ("transport-bicycles", "Велосипеды", 80),
    ("transport-buses-microbuses-motorhomes", "Автобусы, микроавтобусы и автодома", 90),
    ("transport-special-equipment", "Спецтехника", 100),
    ("transport-cargo", "Грузовой транспорт", 110),
    ("transport-watercraft", "Водный транспорт", 120),
    ("transport-trailers", "Прицепы и полуприцепы", 130),
    ("transport-farm-machinery", "Сельхозтехника", 140),
    ("transport-rental", "Аренда транспорта", 150),
]

_AUTO_SERVICES_CHILDREN: tuple[str, ...] = (
    "transport-auto-services-remont-i-obsluzhivanie",
    "transport-auto-services-avtoelektrika",
    "transport-auto-services-kuzovnoy-remont",
    "transport-auto-services-deteyling-i-uhod",
    "transport-auto-services-shinomontazh",
    "transport-auto-services-evakuatsiya-i-pomosch-na-doroge",
    "transport-auto-services-tyuning-i-doosnaschenie",
    "transport-auto-services-avtostekla",
    "transport-auto-services-gbo-gazoballonnoe-oborudovanie",
    "transport-auto-services-proverka-i-oformlenie",
)

_BUYBACK_CHILDREN: tuple[str, ...] = (
    "transport-buyback-exchange-skupka-avtomobiley",
    "transport-buyback-exchange-skupka-kommercheskogo-transporta",
    "transport-buyback-exchange-skupka-gruzovogo-transporta",
    "transport-buyback-exchange-skupka-spetstehniki",
    "transport-buyback-exchange-skupka-mototehniki",
    "transport-buyback-exchange-obmen-transporta",
    "transport-buyback-exchange-vykup-posle-dtp",
    "transport-buyback-exchange-vykup-na-zapchasti",
)

_BUS_CHILDREN: list[tuple[str, int]] = [
    ("transport-commercial-avtobusy", 10),
    ("transport-commercial-mikroavtobusy", 20),
    ("transport-buses-avtodoma", 30),
]


def _id(bind, slug: str) -> int | None:
    row = bind.execute(
        text("SELECT id FROM categories WHERE slug = :s"),
        {"s": slug},
    ).fetchone()
    return int(row[0]) if row else None


def upgrade() -> None:
    bind = op.get_bind()
    transport_id = _id(bind, "transport")
    if transport_id is None:
        raise RuntimeError("transport root missing")

    buses_id = _id(bind, "transport-buses-microbuses-motorhomes")
    if buses_id is None:
        raise RuntimeError("transport-buses-microbuses-motorhomes missing")

    services_id = _id(bind, "transport-auto-services")
    if services_id is None:
        raise RuntimeError("transport-auto-services missing")

    # Reference safety — refuse remap if unexpected listings on moved/deactivated nodes
    watch_slugs = (
        [s for s, _ in _BUS_CHILDREN]
        + list(_BUYBACK_CHILDREN)
        + list(_AUTO_SERVICES_CHILDREN)
        + [
            "transport-auto-services",
            "transport-commercial",
            "transport-buyback-exchange",
        ]
    )
    listing_hits = bind.execute(
        text(
            """
            SELECT c.slug, COUNT(*) AS n
            FROM listings l
            JOIN categories c ON c.id = l.category_id
            WHERE c.slug = ANY(:slugs)
            GROUP BY c.slug
            """
        ),
        {"slugs": watch_slugs},
    ).fetchall()
    if listing_hits:
        detail = ", ".join(f"{s}:{n}" for s, n in listing_hits)
        raise RuntimeError(
            f"Transport tree cleanup blocked: listings present on watched slugs ({detail})"
        )

    # Activate + order canonical L2
    keep = {slug for slug, _, _ in _L2_ACTIVE}
    for slug, name, sort_order in _L2_ACTIVE:
        cid = _id(bind, slug)
        if cid is None:
            raise RuntimeError(f"Required L2 missing: {slug}")
        bind.execute(
            text(
                """
                UPDATE categories
                SET name = :name,
                    sort_order = :ord,
                    parent_id = :pid,
                    is_active = true,
                    updated_at = NOW()
                WHERE id = :id
                """
            ),
            {
                "name": name,
                "ord": sort_order,
                "pid": transport_id,
                "id": cid,
            },
        )

    # Soft-deactivate non-canonical active L2 under transport
    others = bind.execute(
        text(
            """
            SELECT id, slug FROM categories
            WHERE parent_id = :pid AND is_active = true
            """
        ),
        {"pid": transport_id},
    ).fetchall()
    for cid, slug in others:
        if slug in keep:
            continue
        bind.execute(
            text(
                "UPDATE categories SET is_active = false, updated_at = NOW() WHERE id = :id"
            ),
            {"id": cid},
        )

    # Re-parent buses / microbuses / motorhomes under canonical buses L2
    for slug, sort_order in _BUS_CHILDREN:
        cid = _id(bind, slug)
        if cid is None:
            raise RuntimeError(f"Required buses child missing: {slug}")
        bind.execute(
            text(
                """
                UPDATE categories
                SET parent_id = :pid,
                    is_active = true,
                    sort_order = :ord,
                    updated_at = NOW()
                WHERE id = :id
                """
            ),
            {"pid": buses_id, "ord": sort_order, "id": cid},
        )

    # Auto-services children stay active under parent
    for slug in _AUTO_SERVICES_CHILDREN:
        cid = _id(bind, slug)
        if cid is None:
            continue
        bind.execute(
            text(
                """
                UPDATE categories
                SET parent_id = :pid,
                    is_active = true,
                    updated_at = NOW()
                WHERE id = :id
                """
            ),
            {"pid": services_id, "id": cid},
        )

    # Soft-deactivate buyback children
    for slug in _BUYBACK_CHILDREN:
        cid = _id(bind, slug)
        if cid is None:
            continue
        bind.execute(
            text(
                "UPDATE categories SET is_active = false, updated_at = NOW() WHERE id = :id"
            ),
            {"id": cid},
        )

    # Soft-deactivate remaining active children under commercial (after re-parent)
    commercial_id = _id(bind, "transport-commercial")
    if commercial_id is not None:
        bind.execute(
            text(
                """
                UPDATE categories
                SET is_active = false, updated_at = NOW()
                WHERE parent_id = :pid AND is_active = true
                """
            ),
            {"pid": commercial_id},
        )
        bind.execute(
            text(
                "UPDATE categories SET is_active = false, updated_at = NOW() WHERE id = :id"
            ),
            {"id": commercial_id},
        )

    buyback_id = _id(bind, "transport-buyback-exchange")
    if buyback_id is not None:
        bind.execute(
            text(
                "UPDATE categories SET is_active = false, updated_at = NOW() WHERE id = :id"
            ),
            {"id": buyback_id},
        )


def downgrade() -> None:
    # Non-destructive reverse is intentionally omitted (tree cleanup is forward-only).
    pass
