# -*- coding: utf-8 -*-
"""Fashion V2 Package A — simple Create SoT (size allowlist).

Product: classifieds board, not fashion e-commerce.
Shared base + fashion_kind; only special = structured Size where useful.
Season / gender / material / brand / color / style / watch_movement = CREATE 0.
"""
from __future__ import annotations

from typing import Any

from app.models.category_enums import (
    CategoryEntityType,
    CategoryFieldType,
    CategoryFilterType,
)
from app.seeds.fashion_sections_catalog import FASHION_SECTIONS

FASHION_ROOT_SLUG = "fashion"
FASHION_ROOT_LABEL = "Одежда, обувь и аксессуары"

FASHION_V2_CANONICAL_LEAVES: tuple[tuple[str, str, int], ...] = (
    ("fashion-zhenskaya-odezhda", "Женская одежда", 10),
    ("fashion-muzhskaya-odezhda", "Мужская одежда", 20),
    ("fashion-odezhda-dlya-beremennyh-kormyaschih", "Одежда для беременных/кормящих", 30),
    ("fashion-nizhnee-bele", "Нижнее бельё", 40),
    ("fashion-domashnyaya-odezhda", "Домашняя одежда", 50),
    ("fashion-musulmanskaya-odezhda-aksessuary", "Мусульманская одежда/аксессуары", 60),
    ("fashion-zhenskaya-obuv", "Женская обувь", 70),
    ("fashion-muzhskaya-obuv", "Мужская обувь", 80),
    ("fashion-sumki-i-chemodany", "Сумки и чемоданы", 90),
    ("fashion-ukrasheniya-i-bizhuteriya", "Украшения и бижутерия", 100),
    ("fashion-chasy", "Часы", 110),
    ("fashion-aksessuary", "Аксессуары", 120),
    ("fashion-spetsodezhda-i-uniforma", "Спецодежда и униформа", 140),
    ("fashion-natsionalnaya-odezhda", "Национальная одежда", 150),
    ("fashion-svadebnaya-i-vechernyaya-odezhda", "Свадебная и вечерняя одежда", 160),
    ("fashion-sportivnaya-odezhda-i-obuv", "Спортивная одежда и обувь", 170),
    ("fashion-prochee", "Прочее", 180),
)

FASHION_V2_CANONICAL_SLUGS: frozenset[str] = frozenset(
    slug for slug, _label, _sort in FASHION_V2_CANONICAL_LEAVES
)

FASHION_V2_RETIRED_SLUGS: frozenset[str] = frozenset(
    {
        "fashion-clothing",
        "fashion-shoes",
        "fashion-accessories",
        "fashion-tkani-i-furnitura",
    }
)

FASHION_V2_SECTION_TO_SLUG: dict[str, str] = {
    key: str(cat["category_slug"]) for key, cat in FASHION_SECTIONS.items()
}

FASHION_V2_ENTITY_TYPE = CategoryEntityType.object

_CONTACT_METHODS = (
    "Только чат",
    "Только телефон",
    "Чат + телефон",
    "Чат + Wapp",
    "Телефон + Wapp",
    "Чат + Тел. + Wapp",
)

_NEGOTIABLE = ("Есть торг", "Без торга")

# Semantic size catalogs (closed) — only for kinds on the positive allowlist.
_W_SIZE = ("40", "42", "44", "46", "48", "50", "52", "54", "56", "58", "60", "62", "64", "66")
_M_SIZE = ("46", "48", "50", "52", "54", "56", "58", "60", "62", "64", "66")
_W_SHOE = ("35", "36", "37", "38", "39", "40", "41", "42", "43", "44", "45", "46")
_M_SHOE = ("39", "40", "41", "42", "43", "44", "45", "46")

SEMANTIC_SIZE_CLOTHING_W = "clothing_w"
SEMANTIC_SIZE_CLOTHING_M = "clothing_m"
SEMANTIC_SIZE_SHOE_W = "shoe_w"
SEMANTIC_SIZE_SHOE_M = "shoe_m"
SEMANTIC_SIZE_NONE = "none"

_SEMANTIC_CATALOG: dict[str, tuple[str, ...]] = {
    SEMANTIC_SIZE_CLOTHING_W: _W_SIZE,
    SEMANTIC_SIZE_CLOTHING_M: _M_SIZE,
    SEMANTIC_SIZE_SHOE_W: _W_SHOE,
    SEMANTIC_SIZE_SHOE_M: _M_SHOE,
}

# ---------------------------------------------------------------------------
# POSITIVE Size allowlist (Create + future Search).
# Default for any kind NOT listed: NO_SIZE → Description.
# Do NOT infer Size from “looks like clothing / wearable”.
#
# Independent product expectations (tests assert production == this contract;
# production mapping must NOT be used as its own proof of correctness).
# Proven groups only:
#   ordinary women clothing → clothing_w
#   ordinary men clothing   → clothing_m
#   women footwear          → shoe_w
#   men footwear            → shoe_m
# Underwear / ambiguous sections → NO_SIZE (explicit product decisions).
# ---------------------------------------------------------------------------

# Locked product NO_SIZE (must never appear on Size allowlist).
FASHION_V2_LOCKED_NO_SIZE_KINDS: frozenset[str] = frozenset(
    {
        # Entire underwear section (user product decision — no size systems yet)
        "Бюстгальтеры",
        "Трусы",
        "Носки",
        "Колготки",
        "Комплекты белья",
        "Боди",
        "Другое бельё",
        # Nursing lingerie
        "Бельё для кормления",
    }
)

# kind → semantic group. Sole product evidence for Size YES.
FASHION_V2_APPROVED_SIZE_EXPECTATIONS: dict[str, str] = {
    # Ordinary women clothing
    "Платья": SEMANTIC_SIZE_CLOTHING_W,
    "Юбки": SEMANTIC_SIZE_CLOTHING_W,
    "Блузки и рубашки": SEMANTIC_SIZE_CLOTHING_W,
    "Футболки и топы": SEMANTIC_SIZE_CLOTHING_W,
    "Женские джинсы": SEMANTIC_SIZE_CLOTHING_W,
    "Женские брюки": SEMANTIC_SIZE_CLOTHING_W,
    "Кофты и кардиганы": SEMANTIC_SIZE_CLOTHING_W,
    "Женская верхняя одежда": SEMANTIC_SIZE_CLOTHING_W,
    "Женские костюмы": SEMANTIC_SIZE_CLOTHING_W,
    "Другая женская одежда": SEMANTIC_SIZE_CLOTHING_W,
    # Ordinary men clothing
    "Рубашки": SEMANTIC_SIZE_CLOTHING_M,
    "Футболки и поло": SEMANTIC_SIZE_CLOTHING_M,
    "Мужские джинсы": SEMANTIC_SIZE_CLOTHING_M,
    "Мужские брюки": SEMANTIC_SIZE_CLOTHING_M,
    "Пиджаки и костюмы": SEMANTIC_SIZE_CLOTHING_M,
    "Мужская верхняя одежда": SEMANTIC_SIZE_CLOTHING_M,
    "Свитеры и толстовки": SEMANTIC_SIZE_CLOTHING_M,
    "Шорты": SEMANTIC_SIZE_CLOTHING_M,
    "Другая мужская одежда": SEMANTIC_SIZE_CLOTHING_M,
    # Women footwear
    "Туфли": SEMANTIC_SIZE_SHOE_W,
    "Босоножки": SEMANTIC_SIZE_SHOE_W,
    "Балетки": SEMANTIC_SIZE_SHOE_W,
    "Сапоги": SEMANTIC_SIZE_SHOE_W,
    "Женские ботинки": SEMANTIC_SIZE_SHOE_W,
    "Женские кроссовки": SEMANTIC_SIZE_SHOE_W,
    "Женские кеды": SEMANTIC_SIZE_SHOE_W,
    "Лоферы": SEMANTIC_SIZE_SHOE_W,
    "Женские тапочки": SEMANTIC_SIZE_SHOE_W,
    "Другая женская обувь": SEMANTIC_SIZE_SHOE_W,
    # Men footwear
    "Мужские туфли": SEMANTIC_SIZE_SHOE_M,
    "Мужские кроссовки": SEMANTIC_SIZE_SHOE_M,
    "Мужские ботинки": SEMANTIC_SIZE_SHOE_M,
    "Мужские кеды": SEMANTIC_SIZE_SHOE_M,
    "Сандалии": SEMANTIC_SIZE_SHOE_M,
    "Мужские тапочки": SEMANTIC_SIZE_SHOE_M,
    "Другая мужская обувь": SEMANTIC_SIZE_SHOE_M,
}

# Production wiring: slug → (field_key, kinds, semantic_group).
# Must equal FASHION_V2_APPROVED_SIZE_EXPECTATIONS (enforced in assert).
_SIZE_ALLOWLIST: dict[str, list[tuple[str, tuple[str, ...], str]]] = {
    "fashion-zhenskaya-odezhda": [
        (
            "size",
            tuple(
                k
                for k, g in FASHION_V2_APPROVED_SIZE_EXPECTATIONS.items()
                if g == SEMANTIC_SIZE_CLOTHING_W
                and k
                in {
                    "Платья",
                    "Юбки",
                    "Блузки и рубашки",
                    "Футболки и топы",
                    "Женские джинсы",
                    "Женские брюки",
                    "Кофты и кардиганы",
                    "Женская верхняя одежда",
                    "Женские костюмы",
                    "Другая женская одежда",
                }
            ),
            SEMANTIC_SIZE_CLOTHING_W,
        ),
    ],
    "fashion-muzhskaya-odezhda": [
        (
            "size",
            tuple(
                k
                for k, g in FASHION_V2_APPROVED_SIZE_EXPECTATIONS.items()
                if g == SEMANTIC_SIZE_CLOTHING_M
            ),
            SEMANTIC_SIZE_CLOTHING_M,
        ),
    ],
    "fashion-zhenskaya-obuv": [
        (
            "size",
            tuple(
                k
                for k, g in FASHION_V2_APPROVED_SIZE_EXPECTATIONS.items()
                if g == SEMANTIC_SIZE_SHOE_W
            ),
            SEMANTIC_SIZE_SHOE_W,
        ),
    ],
    "fashion-muzhskaya-obuv": [
        (
            "size",
            tuple(
                k
                for k, g in FASHION_V2_APPROVED_SIZE_EXPECTATIONS.items()
                if g == SEMANTIC_SIZE_SHOE_M
            ),
            SEMANTIC_SIZE_SHOE_M,
        ),
    ],
    # Maternity / underwear / home / muslim / uniform / national / wedding /
    # sport / prochee / bags / jewelry / watches / accessories → default NO_SIZE.
}

# Always-on Create base (not specialty Size/Condition).
# SHARED ≠ UNIVERSAL: condition is NOT here — semantic positive allowlist below.
_ALWAYS_SHARED_CREATE_KEYS: frozenset[str] = frozenset(
    {
        "fashion_kind",
        "seller_type",
        "price",
        "negotiable",
        "contact_methods",
    }
)

# Backward-compatible name used by older helpers/tests.
_SHARED_CREATE_KEYS: frozenset[str] = _ALWAYS_SHARED_CREATE_KEYS

# Approved size field keys (UX label always «Размер»).
FASHION_V2_SIZE_KEYS: frozenset[str] = frozenset({"size"})

FASHION_V2_CONDITION_KEY = "condition"
_CONDITION_OPTIONS = ("Новое", "Б/у")

# ---------------------------------------------------------------------------
# POSITIVE Condition allowlist (Create + future Search).
# Default: Condition ABSENT unless kind is explicitly approved.
# Shared vocabulary «Новое/Б/у» does NOT imply universal visibility.
#
# CONDITION_NO (locked / same-class intimate personal-use where «Б/у»
# is product-illogical for AiVai marketplace UX):
#   - entire Нижнее бельё (user decision)
#   - Бельё для кормления (nursing lingerie — same intimate class)
#   - Купальники / Плавки (intimate swimwear — proactive same-class)
# All other Fashion kinds: Condition YES (used-goods market is normal).
# ---------------------------------------------------------------------------

FASHION_V2_LOCKED_NO_CONDITION_KINDS: frozenset[str] = frozenset(
    {
        # Нижнее бельё (canonical section) — user product decision
        "Бюстгальтеры",
        "Трусы",
        "Комплекты белья",
        "Носки",
        "Колготки",
        "Боди",
        "Другое бельё",
        # Nursing lingerie — same intimate class
        "Бельё для кормления",
        # Intimate swimwear — proactive same-class (personal-use hygiene UX)
        "Купальники",
        "Плавки",
    }
)


def _build_approved_condition_kinds() -> frozenset[str]:
    """Positive Condition YES set = catalog kinds − locked NO."""
    return frozenset(fashion_v2_all_kinds() - set(FASHION_V2_LOCKED_NO_CONDITION_KINDS))


# Filled after fashion_v2_all_kinds is defined — see module tail.
FASHION_V2_APPROVED_CONDITION_EXPECTATIONS: frozenset[str] = frozenset()

# Forbidden Create extras (never seed).
FASHION_V2_CREATE_FORBIDDEN: frozenset[str] = frozenset(
    {
        "season",
        "gender",
        "for_whom",
        "material",
        "brand",
        "color",
        "style",
        "watch_movement",
        "underwear_size",
        "bra_size",
        "sock_size",
        "tights_size",
        "suit_size",
        "clothing_size",
        "shoe_size",
    }
)


def _choices(*labels: str) -> dict[str, Any]:
    return {"choices": [{"value": label, "label": label} for label in labels]}


def _dep_field(
    key: str,
    label: str,
    ftype: CategoryFieldType,
    required: bool,
    sort: int,
    options: dict[str, Any] | None,
    *,
    hint: str | None = None,
) -> tuple:
    return (key, label, ftype, required, sort, options, hint)


def _labels(roles: list[dict[str, Any]]) -> list[str]:
    return [str(r["label"]) for r in roles]


def fashion_v2_kind_count() -> int:
    seen: set[str] = set()
    for cat in FASHION_SECTIONS.values():
        for role in cat["roles"]:
            seen.add(str(role["label"]))
    return len(seen)


def fashion_v2_all_kinds() -> set[str]:
    seen: set[str] = set()
    for cat in FASHION_SECTIONS.values():
        for role in cat["roles"]:
            seen.add(str(role["label"]))
    return seen


def fashion_v2_semantic_kind_map() -> dict[str, tuple[str, str, tuple[str, ...]]]:
    """kind → (size_field_key, semantic_group, options). Positive allowlist only."""
    out: dict[str, tuple[str, str, tuple[str, ...]]] = {}
    for _slug, specs in _SIZE_ALLOWLIST.items():
        for key, kinds, group in specs:
            options = _SEMANTIC_CATALOG.get(group)
            if options is None:
                raise RuntimeError(f"unknown semantic size group: {group}")
            for kind in kinds:
                if kind in out:
                    raise RuntimeError(f"duplicate size allowlist kind: {kind}")
                if kind in FASHION_V2_LOCKED_NO_SIZE_KINDS:
                    raise RuntimeError(
                        f"locked NO_SIZE kind {kind!r} on Size allowlist"
                    )
                out[kind] = (key, group, options)
    return out


def fashion_v2_size_kind_map() -> dict[str, tuple[str, int]]:
    """kind → (size_field_key, options_count). Absent = default NO_SIZE."""
    return {
        kind: (key, len(options))
        for kind, (key, _group, options) in fashion_v2_semantic_kind_map().items()
    }


def fashion_v2_no_size_kinds() -> set[str]:
    """Default NO_SIZE = all catalog kinds not on the positive Size allowlist."""
    return fashion_v2_all_kinds() - set(fashion_v2_size_kind_map())


def fashion_v2_kind_matrix() -> list[tuple[str, str, str, str, int]]:
    """Rows: (section_label, kind, YES/NO, size_key_or_-, options_count)."""
    size_map = fashion_v2_size_kind_map()
    rows: list[tuple[str, str, str, str, int]] = []
    for _key, cat in FASHION_SECTIONS.items():
        section = str(cat["label"])
        for role in cat["roles"]:
            kind = str(role["label"])
            if kind in size_map:
                skey, n = size_map[kind]
                rows.append((section, kind, "YES", skey, n))
            else:
                rows.append((section, kind, "NO", "-", 0))
    return rows


def fashion_v2_assert_semantic_partition() -> None:
    """Positive allowlist integrity + independent product expectations.

    Size YES only via allowlist. Default = NO_SIZE.
    Production wiring must equal FASHION_V2_APPROVED_SIZE_EXPECTATIONS
    (allowlist cannot prove its own semantic correctness).
    """
    all_kinds = fashion_v2_all_kinds()
    sized = fashion_v2_semantic_kind_map()
    sized_kinds = set(sized)

    # Independent contract: production == approved expectations.
    approved = dict(FASHION_V2_APPROVED_SIZE_EXPECTATIONS)
    if set(approved) != sized_kinds:
        raise RuntimeError(
            "production Size allowlist != approved expectations: "
            f"extra={sorted(sized_kinds - set(approved))} "
            f"missing={sorted(set(approved) - sized_kinds)}"
        )
    for kind, (_key, group, options) in sized.items():
        if approved[kind] != group:
            raise RuntimeError(
                f"kind {kind!r} group {group} != approved {approved[kind]}"
            )
        if options != _SEMANTIC_CATALOG[group]:
            raise RuntimeError(
                f"kind {kind!r} options do not match catalog for {group}"
            )

    # Locked product NO_SIZE must remain absent from Size.
    locked = set(FASHION_V2_LOCKED_NO_SIZE_KINDS)
    unknown_locked = locked - all_kinds
    if unknown_locked:
        raise RuntimeError(f"locked NO_SIZE kinds not in catalog: {unknown_locked}")
    overlap = sized_kinds & locked
    if overlap:
        raise RuntimeError(f"locked NO_SIZE kinds still sized: {sorted(overlap)}")

    extra = sized_kinds - all_kinds
    if extra:
        raise RuntimeError(f"size allowlist kinds not in catalog: {extra}")

    # Fingerprint: clothing vs shoe catalogs must not cross.
    for kind, (_key, group, options) in sized.items():
        if group in (SEMANTIC_SIZE_CLOTHING_W, SEMANTIC_SIZE_CLOTHING_M):
            if options in (_W_SHOE, _M_SHOE):
                raise RuntimeError(f"clothing kind {kind!r} has shoe catalog")
        if group in (SEMANTIC_SIZE_SHOE_W, SEMANTIC_SIZE_SHOE_M):
            if options in (_W_SIZE, _M_SIZE):
                raise RuntimeError(f"shoe kind {kind!r} has clothing catalog")


def fashion_v2_assert_condition_contract() -> None:
    """Positive Condition allowlist integrity (independent of Size)."""
    all_kinds = fashion_v2_all_kinds()
    locked = set(FASHION_V2_LOCKED_NO_CONDITION_KINDS)
    approved = set(FASHION_V2_APPROVED_CONDITION_EXPECTATIONS)

    unknown_locked = locked - all_kinds
    if unknown_locked:
        raise RuntimeError(f"locked NO_CONDITION kinds not in catalog: {unknown_locked}")
    if locked & approved:
        raise RuntimeError(
            f"kinds both CONDITION YES and locked NO: {sorted(locked & approved)}"
        )
    if approved | locked != all_kinds:
        raise RuntimeError(
            "Condition partition incomplete: "
            f"missing={sorted(all_kinds - approved - locked)} "
            f"extra={sorted((approved | locked) - all_kinds)}"
        )
    # Positive allowlist must equal catalog − locked (default-off for locked).
    if approved != all_kinds - locked:
        raise RuntimeError("CONDITION YES set != catalog − locked NO")


def fashion_v2_condition_visible_for_kind(kind: str) -> bool:
    return kind in FASHION_V2_APPROVED_CONDITION_EXPECTATIONS


def build_fashion_v2_core_fields() -> dict[str, list]:
    """Canonical Create cores: always-shared + scoped Condition + Size."""
    fashion_v2_assert_semantic_partition()
    fashion_v2_assert_condition_contract()
    out: dict[str, list] = {}
    for section_key, slug in FASHION_V2_SECTION_TO_SLUG.items():
        catalog = FASHION_SECTIONS[section_key]
        assert catalog["category_slug"] == slug
        kinds = _labels(catalog["roles"])
        fields: list = [
            _dep_field(
                "fashion_kind",
                "Товар",
                CategoryFieldType.enum,
                True,
                10,
                _choices(*kinds),
                hint=str(catalog.get("question") or "Какой товар?"),
            ),
            _dep_field(
                "seller_type",
                "Продавец",
                CategoryFieldType.enum,
                True,
                20,
                _choices("Частное лицо", "Магазин", "Другой"),
            ),
        ]

        condition_kinds = [
            k for k in kinds if k in FASHION_V2_APPROVED_CONDITION_EXPECTATIONS
        ]
        if condition_kinds:
            cond_opts: dict[str, Any] = {
                "choices": [
                    {"value": o, "label": o} for o in _CONDITION_OPTIONS
                ],
            }
            # Mixed sections: scope by fashion_kind (positive allowlist).
            if set(condition_kinds) != set(kinds):
                cond_opts["depends_on"] = {
                    "field": "fashion_kind",
                    "values": list(condition_kinds),
                }
            fields.append(
                _dep_field(
                    FASHION_V2_CONDITION_KEY,
                    "Состояние",
                    CategoryFieldType.enum,
                    True,
                    30,
                    cond_opts,
                )
            )
        # Else: entire section CONDITION_NO → omit field (underwear).

        sort = 40
        for key, size_kinds, group in _SIZE_ALLOWLIST.get(slug, []):
            options = _SEMANTIC_CATALOG[group]
            unknown = set(size_kinds) - set(kinds)
            if unknown:
                raise RuntimeError(
                    f"Fashion size allowlist unknown kinds for {slug}: {unknown}"
                )
            if not options:
                raise RuntimeError(f"Fashion size options empty for {slug}/{key}")
            opts: dict[str, Any] = {
                "choices": [
                    {"value": o, "label": o, "for_kinds": list(size_kinds)}
                    for o in options
                ],
                "depends_on": {
                    "field": "fashion_kind",
                    "values": list(size_kinds),
                },
                "semantic_size_group": group,
            }
            fields.append(
                _dep_field(
                    key,
                    "Размер",
                    CategoryFieldType.multi_select,
                    False,
                    sort,
                    opts,
                )
            )
            sort += 10

        fields.extend(
            [
                (
                    "price",
                    "Цена",
                    CategoryFieldType.price,
                    True,
                    200,
                    None,
                    "Цена товара",
                ),
                _dep_field(
                    "negotiable",
                    "Торг",
                    CategoryFieldType.enum,
                    False,
                    210,
                    _choices(*_NEGOTIABLE),
                ),
                _dep_field(
                    "contact_methods",
                    "Способы связи",
                    CategoryFieldType.enum,
                    True,
                    220,
                    _choices(*_CONTACT_METHODS),
                ),
            ]
        )

        allowed_keys = (
            _ALWAYS_SHARED_CREATE_KEYS
            | FASHION_V2_SIZE_KEYS
            | {FASHION_V2_CONDITION_KEY}
        )
        for row in fields:
            key = row[0]
            assert key not in FASHION_V2_CREATE_FORBIDDEN, (slug, key)
            if key not in allowed_keys:
                raise RuntimeError(f"unapproved Create field {slug}.{key}")
            opts = row[5]
            if opts and opts.get("choices") is not None:
                if len(opts["choices"]) == 0:
                    raise RuntimeError(f"empty picker options {slug}.{key}")

        out[slug] = fields
    return out


def visible_specials_for_kind(slug: str, kind: str) -> list[tuple[str, int]]:
    """Size (and other non-always-shared specialty) visible for kind."""
    cores = build_fashion_v2_core_fields()[slug]
    out: list[tuple[str, int]] = []
    for row in cores:
        key = row[0]
        if key in _ALWAYS_SHARED_CREATE_KEYS:
            continue
        if key == FASHION_V2_CONDITION_KEY:
            continue  # audited via fashion_v2_condition_visible_for_kind
        opts = row[5] or {}
        depends = opts.get("depends_on") or {}
        values = depends.get("values") or []
        if values and kind not in values:
            continue
        choices = opts.get("choices") or []
        n = 0
        for c in choices:
            fk = c.get("for_kinds")
            if fk and kind not in fk:
                continue
            n += 1
        if n == 0 and values and kind in values:
            out.append((key, 0))
        elif n > 0:
            out.append((key, n))
        elif not values:
            out.append((key, len(choices)))
    return out


def fashion_v2_shared_field_matrix() -> list[tuple[str, ...]]:
    """Rows for local audit artifact (not commit-required)."""
    size_map = fashion_v2_size_kind_map()
    rows: list[tuple[str, ...]] = []
    for _key, cat in FASHION_SECTIONS.items():
        section = str(cat["label"])
        for role in cat["roles"]:
            kind = str(role["label"])
            size_yes = "YES" if kind in size_map else "NO"
            cond_yes = (
                "YES" if fashion_v2_condition_visible_for_kind(kind) else "NO"
            )
            basis = "approved_size" if size_yes == "YES" else "default_no_size"
            if cond_yes == "NO":
                basis = (
                    "locked_intimate_no_condition"
                    if kind in FASHION_V2_LOCKED_NO_CONDITION_KINDS
                    else "no_condition"
                )
            elif size_yes == "YES":
                basis = "approved_size+condition"
            else:
                basis = "condition_only_no_size"
            rows.append(
                (
                    section,
                    kind,
                    size_yes,
                    cond_yes,
                    "YES",  # seller
                    "YES",  # price
                    "YES",  # negotiable
                    "YES",  # contacts
                    basis,
                )
            )
    return rows


# Package B Search allowlist (simple). Create ≠ Search.
# Size / Condition filters only for positive allowlisted kinds.
# Geo region/city are shared Search UX (not leaf EAV CategoryFilter rows).
FASHION_V2_SEARCH_ALLOWLIST: frozenset[str] = frozenset(
    {
        "fashion_kind",
        "size",
        "condition",
        "seller_type",
        "region",
        "city",
    }
)

# Leaf EAV Search filter keys seeded into category_filters.
FASHION_V2_SEARCH_EAV_KEYS: frozenset[str] = frozenset(
    {
        "fashion_kind",
        "size",
        "condition",
        "seller_type",
    }
)

FASHION_V2_SEARCH_SIZE_KIND_ALLOWLIST: frozenset[str] = frozenset(
    FASHION_V2_APPROVED_SIZE_EXPECTATIONS
)

# Set after APPROVED_CONDITION is materialized below.
FASHION_V2_SEARCH_CONDITION_KIND_ALLOWLIST: frozenset[str] = frozenset()

FASHION_V2_SEARCH_EXCLUDE: frozenset[str] = frozenset(
    {
        "season",
        "gender",
        "for_whom",
        "material",
        "brand",
        "color",
        "style",
        "watch_movement",
        "underwear_size",
        "bra_size",
        "sock_size",
        "tights_size",
        "suit_size",
        "clothing_size",
        "shoe_size",
    }
)

# Materialize positive Condition allowlist + derived Size NO set.
FASHION_V2_APPROVED_CONDITION_EXPECTATIONS = _build_approved_condition_kinds()
FASHION_V2_SEARCH_CONDITION_KIND_ALLOWLIST = frozenset(
    FASHION_V2_APPROVED_CONDITION_EXPECTATIONS
)
FASHION_V2_NO_SIZE_KINDS: frozenset[str] = frozenset(fashion_v2_no_size_kinds())
FASHION_V2_NO_CONDITION_KINDS: frozenset[str] = frozenset(
    fashion_v2_all_kinds() - set(FASHION_V2_APPROVED_CONDITION_EXPECTATIONS)
)


def _search_filter(
    key: str,
    label: str,
    ftype: CategoryFilterType,
    sort: int,
    config: dict[str, Any] | None,
) -> tuple:
    return (key, label, ftype, sort, config)


def build_fashion_v2_search_filters() -> dict[str, list]:
    """Package B Search SoT per canonical Fashion L2.

    Explicit allowlist only. Size/Condition inherit Package A semantic
    depends_on / for_kinds from Create cores (Create↔Search parity).
    Price / negotiable / contacts / removed fields are never Search filters.
    """
    cores = build_fashion_v2_core_fields()
    out: dict[str, list] = {}
    for slug, fields in cores.items():
        filters: list = []
        for key, label, _ftype, _required, sort, options, _hint in fields:
            if key not in FASHION_V2_SEARCH_EAV_KEYS:
                continue
            if key in FASHION_V2_SEARCH_EXCLUDE:
                continue
            if key not in FASHION_V2_SEARCH_ALLOWLIST:
                continue
            cfg: dict[str, Any] | None = None
            if options:
                cfg = dict(options)
                if "choices" in cfg and "options" not in cfg:
                    cfg["options"] = list(cfg["choices"])
            filters.append(
                _search_filter(
                    key,
                    label,
                    CategoryFilterType.multi_select,
                    int(sort),
                    cfg,
                )
            )
        out[slug] = filters
    if set(out) != FASHION_V2_CANONICAL_SLUGS:
        raise RuntimeError(
            "Fashion Search filter map != canonical L2 slugs: "
            f"extra={sorted(set(out) - FASHION_V2_CANONICAL_SLUGS)} "
            f"missing={sorted(FASHION_V2_CANONICAL_SLUGS - set(out))}"
        )
    return out