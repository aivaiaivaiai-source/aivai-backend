# -*- coding: utf-8 -*-
"""Kids V2 — taxonomy + Package A Create SoT + Package B Search SoT.

Taxonomy: 16 active goods L2; legacy + education + school retired.
Create: Backend SoT; Age/Size/Condition = positive allowlists (default off).
Search: explicit allowlist; inherits Package A semantic depends_on / for_kinds.
"""
from __future__ import annotations

from typing import Any

from app.models.category_enums import (
    CategoryEntityType,
    CategoryFieldType,
    CategoryFilterType,
)
from app.seeds.shared_goods_create_contract import (
    CONTACT_METHOD_CHOICES,
    GOODS_NEGOTIABLE_CHOICES,
    GOODS_SELLER_CHOICES,
)

KIDS_ROOT_SLUG = "kids"
KIDS_ROOT_LABEL = "Детские товары"
KIDS_V2_ENTITY_TYPE = CategoryEntityType.object
KIDS_V2_KIND_KEY = "kids_kind"
KIDS_V2_CONDITION_KEY = "condition"
KIDS_V2_AGE_KEY = "age"
KIDS_V2_CLOTHING_SIZE_KEY = "size"
KIDS_V2_SHOE_SIZE_KEY = "shoe_size"
KIDS_V2_DIAPER_SIZE_KEY = "diaper_size"
KIDS_V2_MOUNTING_KEY = "mounting"

KIDS_V2_CANONICAL_GOODS_LEAVES: tuple[tuple[str, str, int], ...] = (
    ("kids-tovary-dlya-novorozhdennyh", "Товары для новорождённых", 10),
    ("kids-detskaya-odezhda", "Детская одежда", 20),
    ("kids-detskaya-obuv", "Детская обувь", 30),
    ("kids-detskie-kolyaski", "Детские коляски", 40),
    ("kids-avtokresla-i-perenoski", "Автокресла и переноски", 50),
    ("kids-detskoe-pitanie", "Детское питание", 60),
    ("kids-podguzniki-i-gigiena", "Подгузники и гигиена", 70),
    ("kids-igrushki-igry-i-konstruktory", "Игрушки/игры и конструкторы", 80),
    ("kids-detskie-knigi-i-razvitie", "Детские книги и развитие", 90),
    ("kids-detskaya-mebel", "Детская мебель", 110),
    ("kids-detskiy-transport", "Детский транспорт", 120),
    ("kids-detskiy-sport-aktivnyy-otdyh", "Детский спорт/активный отдых", 130),
    ("kids-detskaya-bezopasnost", "Детская безопасность", 140),
    ("kids-detskoe-zdorove-i-uhod", "Детское здоровье и уход", 150),
    ("kids-detskie-prazdniki-tvorchestvo", "Детские праздники/творчество", 170),
    ("kids-prochie-detskie-tovary", "Прочие детские товары", 180),
)

KIDS_V2_CANONICAL_GOODS_SLUGS: frozenset[str] = frozenset(
    slug for slug, _label, _sort in KIDS_V2_CANONICAL_GOODS_LEAVES
)

KIDS_V2_EDUCATION_SLUG = "kids-detskie-sady-i-obrazovanie"
KIDS_V2_SCHOOL_SLUG = "kids-tovary-dlya-shkoly"

KIDS_V2_LEGACY_RETIRED_SLUGS: frozenset[str] = frozenset(
    {"kids-toys", "kids-clothes", "kids-strollers"}
)

KIDS_V2_RETIRED_SLUGS: frozenset[str] = (
    KIDS_V2_LEGACY_RETIRED_SLUGS
    | frozenset({KIDS_V2_EDUCATION_SLUG, KIDS_V2_SCHOOL_SLUG})
)

KIDS_V2_SECTION_CANONICAL_SLUGS: dict[str, str] = {
    "newborn": "kids-tovary-dlya-novorozhdennyh",
    "clothes": "kids-detskaya-odezhda",
    "shoes": "kids-detskaya-obuv",
    "strollers": "kids-detskie-kolyaski",
    "seats": "kids-avtokresla-i-perenoski",
    "food": "kids-detskoe-pitanie",
    "hygiene": "kids-podguzniki-i-gigiena",
    "toys": "kids-igrushki-igry-i-konstruktory",
    "books": "kids-detskie-knigi-i-razvitie",
    "furniture": "kids-detskaya-mebel",
    "transport": "kids-detskiy-transport",
    "sport": "kids-detskiy-sport-aktivnyy-otdyh",
    "safety": "kids-detskaya-bezopasnost",
    "health": "kids-detskoe-zdorove-i-uhod",
    "party": "kids-detskie-prazdniki-tvorchestvo",
    "other": "kids-prochie-detskie-tovary",
}

# School kinds retired from Kids; ownership vs Stationery (cross-root).
KIDS_V2_SCHOOL_KIND_OWNERSHIP: dict[str, tuple[str, str, str]] = {
    # kind → (decision, destination_or_gap, reason)
    "Школьная форма": (
        "MOVED",
        "kids-detskaya-odezhda",
        "Child garment — Kids clothing authority, not Stationery",
    ),
    "Школьные дневники": (
        "GAP",
        "stationery-books-kantselyarskie-tovary",
        "Nearest Stationery kind «Ежедневники» — not exact; Archi may expand Stationery",
    ),
    "Школьные рюкзаки": (
        "GAP",
        "stationery-books",
        "No backpack leaf in Stationery — do not invent destination",
    ),
    "Мешки для сменной обуви": (
        "GAP",
        "stationery-books",
        "No shoe-bag leaf in Stationery — do not invent destination",
    ),
    "Другие товары для школы": (
        "GAP",
        "stationery-books-prochie-knigi-i-kantstovary",
        "Catch-all only; no exact Kids duplicate owner",
    ),
}

# Kids books stay Kids — Stationery catalog explicitly scopes adult/general books.
KIDS_V2_BOOKS_OWNERSHIP_DECISION = (
    "KEEP_KIDS",
    "kids-detskie-knigi-i-razvitie",
    "Stationery owns general books; kids-specific books remain Kids (source note)",
)

KIDS_V2_LEGACY_CATALOG_SLUG_MISMATCHES: frozenset[str] = frozenset(
    {
        "kids-igrushki",
        "kids-detskie-knigi",
        "kids-detskiy-sport",
        "kids-detskoe-zdorove",
        "kids-detskie-sady",
        "kids-detskie-prazdniki",
        "kids-prochie",
    }
)

KIDS_V2_EDUCATION_SERVICE_KINDS: tuple[str, ...] = (
    "Место в детском саду",
    "Частный детский сад",
    "Ясли",
    "Другие образовательные предложения",
)
KIDS_V2_EDUCATION_NEAREST_SERVICES_SLUG = "services-obuchenie-i-repetitorstvo"
KIDS_V2_REMOVED_POOL_KIND = "Детские бассейны"
KIDS_V2_POOLS_HG_SLUG = "home-garden-basseyny-i-tovary-dlya-otdyha-detskie-basseyny"
KIDS_V2_ORDINARY_WATCH_KIND = "Детские часы"
KIDS_V2_ELECTRONICS_SMART_WATCH_KIND = "Умные часы"

# --- Package A shared vocabulary (canonical goods Create contract) ---
# seller / negotiable / contact_methods → shared_goods_create_contract (no Kids override).
_SELLER = GOODS_SELLER_CHOICES
_CONDITION = ("Новое", "Б/у")
_NEGOTIABLE = GOODS_NEGOTIABLE_CHOICES
_CONTACT = CONTACT_METHOD_CHOICES
_MOUNTING = ("Isofix", "Штатный ремень")

SEMANTIC_CLOTHING_GROWTH = "kids_clothing_growth"
SEMANTIC_AGE_TOYS = "kids_age_toys"
# Retired semantic groups (kept as names for Search-exclude / audit only).
SEMANTIC_SHOE_BUCKETS = "kids_shoe_buckets"
SEMANTIC_DIAPER_WEIGHT = "kids_diaper_weight"
SEMANTIC_AGE_BOOKS = "kids_age_books"
SEMANTIC_AGE_FOOD = "kids_age_food"

_CLOTHING_GROWTH = (
    "56", "62", "68", "74", "80", "86", "92", "98",
    "104", "110", "116", "122", "128", "134", "140", "146", "152", "158",
)
_AGE_TOYS = ("До года", "1-3 года", "3-6 лет", "От 6 лет")

_SEMANTIC_SIZE_CATALOG: dict[str, tuple[str, ...]] = {
    SEMANTIC_CLOTHING_GROWTH: _CLOTHING_GROWTH,
}
_SEMANTIC_AGE_CATALOG: dict[str, tuple[str, ...]] = {
    SEMANTIC_AGE_TOYS: _AGE_TOYS,
}

# Clothing Size YES — actual garments with growth scale.
# Socks/underwear/hats = NO. Shoes/diapers = NO (user/product: Description).
_CLOTHING_SIZE_KINDS: frozenset[str] = frozenset(
    {
        "Боди и распашонки",
        "Ползунки",
        "Футболки и рубашки",
        "Платья и юбки",
        "Кофты и свитера",
        "Верхняя одежда",
        "Другая детская одежда",
        "Школьная форма",
    }
)
_SHOE_SIZE_KINDS: frozenset[str] = frozenset()  # DROP — coarse buckets not approved
_DIAPER_SIZE_KINDS: frozenset[str] = frozenset()  # DROP — user decision → Description

# Age YES — toys only (kind alone weak; single year-band scale).
# Books: kind already age-ish → NO_AGE. Food/formula: user NO_AGE → Description.
_AGE_TOY_KINDS: frozenset[str] = frozenset(
    {
        "Погремушки и прорезыватели",
        "Мягкие игрушки",
        "Куклы",
        "Машинки",
        "Конструкторы",
        "Детские настольные игры",
        "Развивающие коврики",
        "Радиоуправляемые игрушки",
        "Другие игрушки",
    }
)
_AGE_BOOK_KINDS: frozenset[str] = frozenset()
_AGE_FOOD_KINDS: frozenset[str] = frozenset()

# Condition NO — personal-use / consumables / sealed hygiene-feeding.
KIDS_V2_LOCKED_NO_CONDITION_KINDS: frozenset[str] = frozenset(
    {
        "Нижнее бельё и пижамы",
        "Носки и колготки",
        "Пелёнки",
        "Товары для кормления",
        "Подгузники",
        "Подгузники-трусики",
        "Одноразовые пелёнки",
        "Влажные салфетки",
        "Крем и присыпка",
        "Другие товары гигиены",
        "Молочные смеси",
        "Каши для прикорма",
        "Пюре для прикорма",
        "Другое детское питание",
        "Аспираторы для малышей",
        "Детские маникюрные наборы",
        "Воздушные шары и декор",
    }
)

KIDS_V2_MOUNTING_KINDS: frozenset[str] = frozenset(
    {
        "Автолюльки",
        "Автокресла группы 1",
        "Автокресла группы 2-3",
        "Автокресла группы 1-2-3",
        "Бустеры",
    }
)

KIDS_V2_CREATE_FORBIDDEN: frozenset[str] = frozenset(
    {
        "season",
        "gender",
        "kids_brand",
        "brand",
        "material",
        "color",
        "bed_size",
        "wheel_diameter",
        "occasion",
        "school_grade",
        "package_state",
        "clothing_size",
        "underwear_size",
        KIDS_V2_SHOE_SIZE_KEY,
        KIDS_V2_DIAPER_SIZE_KEY,
    }
)

KIDS_V2_EXPECTED_KIND_COUNT = 111
KIDS_V2_EXPECTED_L2_COUNT = 16

_ALWAYS_SHARED = frozenset(
    {
        KIDS_V2_KIND_KEY,
        "seller_type",
        "price",
        "negotiable",
        "contact_methods",
    }
)


def _kids_sections() -> dict[str, Any]:
    from app.seeds.kids_sections_catalog import KIDS_SECTIONS

    return KIDS_SECTIONS


def kids_v2_all_kinds() -> set[str]:
    seen: set[str] = set()
    for cat in _kids_sections().values():
        for role in cat["roles"]:
            seen.add(str(role["label"]))
    return seen


def kids_v2_kind_count() -> int:
    return len(kids_v2_all_kinds())


def kids_v2_section_kinds(slug: str) -> list[str]:
    sections = _kids_sections()
    for key, expected in KIDS_V2_SECTION_CANONICAL_SLUGS.items():
        if expected != slug:
            continue
        return [str(r["label"]) for r in sections[key]["roles"]]
    raise RuntimeError(f"unknown Kids L2 slug: {slug}")


def kids_v2_size_semantic_map() -> dict[str, tuple[str, str, tuple[str, ...]]]:
    """kind → (field_key, semantic_group, options). Absent = NO_SIZE."""
    out: dict[str, tuple[str, str, tuple[str, ...]]] = {}
    for kind in _CLOTHING_SIZE_KINDS:
        out[kind] = (
            KIDS_V2_CLOTHING_SIZE_KEY,
            SEMANTIC_CLOTHING_GROWTH,
            _CLOTHING_GROWTH,
        )
    for kind in _SHOE_SIZE_KINDS:
        if kind in out:
            raise RuntimeError(f"size collision on kind {kind}")
        out[kind] = (KIDS_V2_SHOE_SIZE_KEY, SEMANTIC_SHOE_BUCKETS, _SHOE_BUCKETS)
    for kind in _DIAPER_SIZE_KINDS:
        if kind in out:
            raise RuntimeError(f"size collision on kind {kind}")
        out[kind] = (
            KIDS_V2_DIAPER_SIZE_KEY,
            SEMANTIC_DIAPER_WEIGHT,
            _DIAPER_WEIGHT,
        )
    return out


def kids_v2_age_semantic_map() -> dict[str, tuple[str, tuple[str, ...]]]:
    """kind → (semantic_group, options). Absent = NO_AGE."""
    out: dict[str, tuple[str, tuple[str, ...]]] = {}
    for kind in _AGE_TOY_KINDS:
        out[kind] = (SEMANTIC_AGE_TOYS, _AGE_TOYS)
    for kind in _AGE_BOOK_KINDS:
        if kind in out:
            raise RuntimeError(f"age collision on kind {kind}")
        out[kind] = (SEMANTIC_AGE_BOOKS, _AGE_BOOKS)
    for kind in _AGE_FOOD_KINDS:
        if kind in out:
            raise RuntimeError(f"age collision on kind {kind}")
        out[kind] = (SEMANTIC_AGE_FOOD, _AGE_FOOD)
    return out


# Independent approved expectations (cannot self-prove via production map alone).
KIDS_V2_APPROVED_SIZE_EXPECTATIONS: dict[str, str] = {
    **{k: SEMANTIC_CLOTHING_GROWTH for k in _CLOTHING_SIZE_KINDS},
    **{k: SEMANTIC_SHOE_BUCKETS for k in _SHOE_SIZE_KINDS},
    **{k: SEMANTIC_DIAPER_WEIGHT for k in _DIAPER_SIZE_KINDS},
}
KIDS_V2_APPROVED_AGE_EXPECTATIONS: dict[str, str] = {
    **{k: SEMANTIC_AGE_TOYS for k in _AGE_TOY_KINDS},
    **{k: SEMANTIC_AGE_BOOKS for k in _AGE_BOOK_KINDS},
    **{k: SEMANTIC_AGE_FOOD for k in _AGE_FOOD_KINDS},
}
def kids_v2_approved_condition_kinds() -> frozenset[str]:
    return frozenset(kids_v2_all_kinds() - set(KIDS_V2_LOCKED_NO_CONDITION_KINDS))


# Back-compat alias refreshed lazily via kids_v2_approved_condition_kinds().
KIDS_V2_APPROVED_CONDITION_EXPECTATIONS: frozenset[str] = frozenset()


def kids_v2_assert_contracts() -> None:
    sections = _kids_sections()
    all_kinds = kids_v2_all_kinds()
    if len(all_kinds) != KIDS_V2_EXPECTED_KIND_COUNT:
        raise RuntimeError(
            f"expected {KIDS_V2_EXPECTED_KIND_COUNT} Kids kinds, got {len(all_kinds)}"
        )
    if len(KIDS_V2_CANONICAL_GOODS_SLUGS) != KIDS_V2_EXPECTED_L2_COUNT:
        raise RuntimeError(
            f"expected {KIDS_V2_EXPECTED_L2_COUNT} L2, got {len(KIDS_V2_CANONICAL_GOODS_SLUGS)}"
        )
    if KIDS_V2_SCHOOL_SLUG in KIDS_V2_CANONICAL_GOODS_SLUGS:
        raise RuntimeError("school L2 must be retired from Kids")
    if "school" in sections:
        raise RuntimeError("school section must be removed from Kids catalog")
    if set(sections) != set(KIDS_V2_SECTION_CANONICAL_SLUGS):
        raise RuntimeError("Kids sections keys != canonical section map")
    for key, slug in KIDS_V2_SECTION_CANONICAL_SLUGS.items():
        if sections[key]["category_slug"] != slug:
            raise RuntimeError(f"section {key} slug mismatch")
        if slug not in KIDS_V2_CANONICAL_GOODS_SLUGS:
            raise RuntimeError(f"section slug not canonical goods: {slug}")
    clothes_kinds = {str(r["label"]) for r in sections["clothes"]["roles"]}
    if "Школьная форма" not in clothes_kinds:
        raise RuntimeError("Школьная форма must live under Kids clothing")

    size_map = kids_v2_size_semantic_map()
    if set(size_map) != set(KIDS_V2_APPROVED_SIZE_EXPECTATIONS):
        raise RuntimeError(
            "Size production != approved: "
            f"extra={sorted(set(size_map) - set(KIDS_V2_APPROVED_SIZE_EXPECTATIONS))} "
            f"missing={sorted(set(KIDS_V2_APPROVED_SIZE_EXPECTATIONS) - set(size_map))}"
        )
    for kind, (_key, group, options) in size_map.items():
        if KIDS_V2_APPROVED_SIZE_EXPECTATIONS[kind] != group:
            raise RuntimeError(f"size group mismatch for {kind}")
        if options != _SEMANTIC_SIZE_CATALOG[group]:
            raise RuntimeError(f"size options mismatch for {kind}/{group}")
        if kind not in all_kinds:
            raise RuntimeError(f"size kind not in catalog: {kind}")

    # Only clothing growth size is retained Create SoT (shoes/diapers DROP).
    for kind, (key, group, options) in size_map.items():
        if key != KIDS_V2_CLOTHING_SIZE_KEY or group != SEMANTIC_CLOTHING_GROWTH:
            raise RuntimeError(f"unexpected size group for {kind}: {key}/{group}")
        if options != _CLOTHING_GROWTH:
            raise RuntimeError(f"clothing growth options mismatch for {kind}")

    age_map = kids_v2_age_semantic_map()
    if set(age_map) != set(KIDS_V2_APPROVED_AGE_EXPECTATIONS):
        raise RuntimeError("Age production != approved expectations")
    for kind, (group, options) in age_map.items():
        if KIDS_V2_APPROVED_AGE_EXPECTATIONS[kind] != group:
            raise RuntimeError(f"age group mismatch for {kind}")
        if options != _SEMANTIC_AGE_CATALOG[group]:
            raise RuntimeError(f"age options mismatch for {kind}/{group}")
        if kind not in all_kinds:
            raise RuntimeError(f"age kind not in catalog: {kind}")

    locked = set(KIDS_V2_LOCKED_NO_CONDITION_KINDS)
    approved = set(kids_v2_approved_condition_kinds())
    global KIDS_V2_APPROVED_CONDITION_EXPECTATIONS
    KIDS_V2_APPROVED_CONDITION_EXPECTATIONS = frozenset(approved)
    if locked - all_kinds:
        raise RuntimeError(f"unknown NO_CONDITION: {sorted(locked - all_kinds)}")
    if locked & approved:
        raise RuntimeError("Condition YES∩NO overlap")
    if approved | locked != all_kinds:
        raise RuntimeError(
            "Condition partition incomplete: "
            f"missing={sorted(all_kinds - approved - locked)}"
        )
    if approved != all_kinds - locked:
        raise RuntimeError("CONDITION YES != catalog − locked NO")

    mount_unknown = set(KIDS_V2_MOUNTING_KINDS) - all_kinds
    if mount_unknown:
        raise RuntimeError(f"mounting kinds unknown: {mount_unknown}")


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


def build_kids_v2_core_fields() -> dict[str, list]:
    """Create cores for all 17 canonical Kids goods L2."""
    kids_v2_assert_contracts()
    approved_condition = kids_v2_approved_condition_kinds()

    size_map = kids_v2_size_semantic_map()
    age_map = kids_v2_age_semantic_map()
    out: dict[str, list] = {}

    sections = _kids_sections()
    for section_key, slug in KIDS_V2_SECTION_CANONICAL_SLUGS.items():
        catalog = sections[section_key]
        kinds = [str(r["label"]) for r in catalog["roles"]]
        fields: list = [
            _dep_field(
                KIDS_V2_KIND_KEY,
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
                _choices(*_SELLER),
            ),
        ]

        condition_kinds = [k for k in kinds if k in approved_condition]
        if condition_kinds:
            cond_opts: dict[str, Any] = {
                "choices": [{"value": o, "label": o} for o in _CONDITION],
            }
            if set(condition_kinds) != set(kinds):
                cond_opts["depends_on"] = {
                    "field": KIDS_V2_KIND_KEY,
                    "values": list(condition_kinds),
                }
            fields.append(
                _dep_field(
                    KIDS_V2_CONDITION_KEY,
                    "Состояние",
                    CategoryFieldType.enum,
                    True,
                    30,
                    cond_opts,
                )
            )

        # Age — one field, options scoped by for_kinds to semantic group.
        age_kinds_here = [k for k in kinds if k in age_map]
        if age_kinds_here:
            choices: list[dict[str, Any]] = []
            # Emit each scale's options once, tagged with kinds of that scale in section.
            by_group: dict[str, list[str]] = {}
            for k in age_kinds_here:
                group, _opts = age_map[k]
                by_group.setdefault(group, []).append(k)
            for group, group_kinds in by_group.items():
                for opt in _SEMANTIC_AGE_CATALOG[group]:
                    choices.append(
                        {
                            "value": opt,
                            "label": opt,
                            "for_kinds": list(group_kinds),
                        }
                    )
            fields.append(
                _dep_field(
                    KIDS_V2_AGE_KEY,
                    "Возраст",
                    CategoryFieldType.enum,
                    False,
                    40,
                    {
                        "choices": choices,
                        "depends_on": {
                            "field": KIDS_V2_KIND_KEY,
                            "values": list(age_kinds_here),
                        },
                    },
                )
            )

        # Size — clothing growth only (shoes/diapers DROP → Description).
        sort = 50
        clothing_sized = [
            k
            for k in kinds
            if size_map.get(k, (None, None, None))[1] == SEMANTIC_CLOTHING_GROWTH
        ]
        if clothing_sized:
            fields.append(
                _dep_field(
                    KIDS_V2_CLOTHING_SIZE_KEY,
                    "Размер",
                    CategoryFieldType.multi_select,
                    False,
                    sort,
                    {
                        "choices": [
                            {
                                "value": o,
                                "label": o,
                                "for_kinds": list(clothing_sized),
                            }
                            for o in _CLOTHING_GROWTH
                        ],
                        "depends_on": {
                            "field": KIDS_V2_KIND_KEY,
                            "values": list(clothing_sized),
                        },
                        "semantic_size_group": SEMANTIC_CLOTHING_GROWTH,
                    },
                )
            )
            sort += 10

        mount_kinds = [k for k in kinds if k in KIDS_V2_MOUNTING_KINDS]
        if mount_kinds:
            fields.append(
                _dep_field(
                    KIDS_V2_MOUNTING_KEY,
                    "Крепление",
                    CategoryFieldType.enum,
                    False,
                    sort,
                    {
                        "choices": [
                            {"value": o, "label": o} for o in _MOUNTING
                        ],
                        "depends_on": {
                            "field": KIDS_V2_KIND_KEY,
                            "values": list(mount_kinds),
                        },
                    },
                )
            )

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
                    _choices(*_CONTACT),
                ),
            ]
        )

        allowed = (
            _ALWAYS_SHARED
            | {
                KIDS_V2_CONDITION_KEY,
                KIDS_V2_AGE_KEY,
                KIDS_V2_CLOTHING_SIZE_KEY,
                KIDS_V2_MOUNTING_KEY,
            }
        )
        for row in fields:
            key = row[0]
            if key in KIDS_V2_CREATE_FORBIDDEN:
                raise RuntimeError(f"forbidden Create field {slug}.{key}")
            if key not in allowed:
                raise RuntimeError(f"unapproved Create field {slug}.{key}")
            opts = row[5]
            if opts and opts.get("choices") is not None and len(opts["choices"]) == 0:
                raise RuntimeError(f"empty picker {slug}.{key}")
        out[slug] = fields

    if set(out) != KIDS_V2_CANONICAL_GOODS_SLUGS:
        raise RuntimeError(
            f"Create schemas must cover exactly {KIDS_V2_EXPECTED_L2_COUNT} "
            "canonical L2"
        )
    return out


def kids_v2_condition_visible_for_kind(kind: str) -> bool:
    return kind in kids_v2_approved_condition_kinds()


def kids_v2_kind_audit_row(slug: str, kind: str) -> dict[str, Any]:
    """One kind row for all-115 Package A audit."""
    size_map = kids_v2_size_semantic_map()
    age_map = kids_v2_age_semantic_map()
    size_info = size_map.get(kind)
    age_info = age_map.get(kind)
    specials: list[str] = []
    if kids_v2_condition_visible_for_kind(kind):
        specials.append(KIDS_V2_CONDITION_KEY)
    if age_info:
        specials.append(KIDS_V2_AGE_KEY)
    if size_info:
        specials.append(size_info[0])
    if kind in KIDS_V2_MOUNTING_KINDS:
        specials.append(KIDS_V2_MOUNTING_KEY)
    visible = ["kids_kind", "seller_type", *specials, "price", "negotiable", "contact_methods"]
    return {
        "l2": slug,
        "kind": kind,
        "age": "YES" if age_info else "NO",
        "age_group": age_info[0] if age_info else None,
        "size": "YES" if size_info else "NO",
        "size_group": size_info[1] if size_info else None,
        "size_key": size_info[0] if size_info else None,
        "condition": "YES" if kids_v2_condition_visible_for_kind(kind) else "NO",
        "specials": specials,
        "special_count": len(specials),
        "visible_components": visible,
    }


def kids_v2_all_kind_audit() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for slug in sorted(KIDS_V2_CANONICAL_GOODS_SLUGS):
        for kind in kids_v2_section_kinds(slug):
            rows.append(kids_v2_kind_audit_row(slug, kind))
    return rows


def kids_v2_complexity_histogram() -> dict[str, int]:
    """Specials beyond always-shared base (kind/seller/price/negotiable/contacts)."""
    cores = build_kids_v2_core_fields()
    hist = {"0": 0, "1": 0, "2": 0, "3+": 0}
    for slug, fields in cores.items():
        kinds = kids_v2_section_kinds(slug)
        for kind in kinds:
            n = 0
            for row in fields:
                key = row[0]
                if key in _ALWAYS_SHARED:
                    continue
                opts = row[5] or {}
                depends = opts.get("depends_on") or {}
                values = depends.get("values") or []
                if values and kind not in values:
                    continue
                # condition / age / sizes / mounting
                if key == KIDS_V2_CONDITION_KEY:
                    if kids_v2_condition_visible_for_kind(kind):
                        n += 1
                    continue
                choices = opts.get("choices") or []
                if choices:
                    visible = 0
                    for c in choices:
                        fk = c.get("for_kinds")
                        if fk and kind not in fk:
                            continue
                        visible += 1
                    if visible > 0 or (values and kind in values):
                        n += 1
                elif not values:
                    n += 1
            bucket = "3+" if n >= 3 else str(n)
            hist[bucket] += 1
    return hist


# --- Package B Search SoT (Create ≠ Search) ---
# Geo region/city = shared Search UX (not leaf EAV CategoryFilter rows).
KIDS_V2_SEARCH_ALLOWLIST: frozenset[str] = frozenset(
    {
        KIDS_V2_KIND_KEY,
        KIDS_V2_CLOTHING_SIZE_KEY,
        KIDS_V2_AGE_KEY,
        KIDS_V2_CONDITION_KEY,
        KIDS_V2_MOUNTING_KEY,
        "seller_type",
        "region",
        "city",
    }
)

KIDS_V2_SEARCH_EAV_KEYS: frozenset[str] = frozenset(
    {
        KIDS_V2_KIND_KEY,
        KIDS_V2_CLOTHING_SIZE_KEY,
        KIDS_V2_AGE_KEY,
        KIDS_V2_CONDITION_KEY,
        KIDS_V2_MOUNTING_KEY,
        "seller_type",
    }
)

KIDS_V2_SEARCH_SIZE_KIND_ALLOWLIST: frozenset[str] = frozenset(
    KIDS_V2_APPROVED_SIZE_EXPECTATIONS
)
KIDS_V2_SEARCH_AGE_KIND_ALLOWLIST: frozenset[str] = frozenset(
    KIDS_V2_APPROVED_AGE_EXPECTATIONS
)
KIDS_V2_SEARCH_MOUNTING_KIND_ALLOWLIST: frozenset[str] = frozenset(
    KIDS_V2_MOUNTING_KINDS
)

KIDS_V2_SEARCH_EXCLUDE: frozenset[str] = frozenset(
    set(KIDS_V2_CREATE_FORBIDDEN)
    | {
        "price",
        "negotiable",
        "contact_methods",
        KIDS_V2_SHOE_SIZE_KEY,
        KIDS_V2_DIAPER_SIZE_KEY,
        "gender",
        "season",
        "brand",
        "kids_brand",
        "school_grade",
        "packaging",
        "package_state",
        "bed_size",
        "wheel_diameter",
        "occasion",
        "material",
        "color",
    }
)


def kids_v2_search_condition_kind_allowlist() -> frozenset[str]:
    """Lazy — avoids circular import with kids_sections_catalog at module import."""
    return frozenset(kids_v2_approved_condition_kinds())


# Alias used by tests; refreshed when build_kids_v2_search_filters runs.
KIDS_V2_SEARCH_CONDITION_KIND_ALLOWLIST: frozenset[str] = frozenset()


def _search_filter(
    key: str,
    label: str,
    ftype: CategoryFilterType,
    sort: int,
    config: dict[str, Any] | None,
) -> tuple:
    return (key, label, ftype, sort, config)


def build_kids_v2_search_filters() -> dict[str, list]:
    """Package B Search SoT per canonical Kids L2.

    Explicit allowlist only. Size/Age/Condition/Mounting inherit Package A
    semantic depends_on / for_kinds from Create cores (Create↔Search parity).
    Price / negotiable / contacts / removed fields are never Search filters.
    """
    global KIDS_V2_SEARCH_CONDITION_KIND_ALLOWLIST
    KIDS_V2_SEARCH_CONDITION_KIND_ALLOWLIST = kids_v2_search_condition_kind_allowlist()
    cores = build_kids_v2_core_fields()
    out: dict[str, list] = {}
    for slug, fields in cores.items():
        filters: list = []
        for key, label, _ftype, _required, sort, options, _hint in fields:
            if key not in KIDS_V2_SEARCH_EAV_KEYS:
                continue
            if key in KIDS_V2_SEARCH_EXCLUDE:
                continue
            if key not in KIDS_V2_SEARCH_ALLOWLIST:
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
    if set(out) != KIDS_V2_CANONICAL_GOODS_SLUGS:
        raise RuntimeError(
            "Kids Search filter map != canonical L2 slugs: "
            f"extra={sorted(set(out) - KIDS_V2_CANONICAL_GOODS_SLUGS)} "
            f"missing={sorted(KIDS_V2_CANONICAL_GOODS_SLUGS - set(out))}"
        )
    return out


def kids_v2_search_kind_audit_row(slug: str, kind: str) -> dict[str, Any]:
    """All-kind Search audit row (independent of Create visible_components)."""
    create_row = kids_v2_kind_audit_row(slug, kind)
    return {
        "l2": slug,
        "kind": kind,
        "search_size": create_row["size"],
        "search_age": create_row["age"],
        "search_condition": create_row["condition"],
        "search_mounting": "YES" if kind in KIDS_V2_MOUNTING_KINDS else "NO",
        "search_seller": "YES",
        "size_group": create_row["size_group"],
        "age_group": create_row["age_group"],
        "visible_search_keys": [
            KIDS_V2_KIND_KEY,
            "seller_type",
            *(
                [KIDS_V2_CONDITION_KEY]
                if create_row["condition"] == "YES"
                else []
            ),
            *([KIDS_V2_AGE_KEY] if create_row["age"] == "YES" else []),
            *(
                [create_row["size_key"]]
                if create_row["size"] == "YES" and create_row["size_key"]
                else []
            ),
            *(
                [KIDS_V2_MOUNTING_KEY]
                if kind in KIDS_V2_MOUNTING_KINDS
                else []
            ),
        ],
    }


def kids_v2_all_search_kind_audit() -> list[dict[str, Any]]:
    return [
        kids_v2_search_kind_audit_row(slug, kind)
        for slug in sorted(KIDS_V2_CANONICAL_GOODS_SLUGS)
        for kind in kids_v2_section_kinds(slug)
    ]


def kids_v2_search_policy_prep() -> dict[str, Any]:
    """Explicit Search allowlist (Package B)."""
    return {
        "allow": sorted(KIDS_V2_SEARCH_ALLOWLIST),
        "eav": sorted(KIDS_V2_SEARCH_EAV_KEYS),
        "exclude": sorted(KIDS_V2_SEARCH_EXCLUDE),
    }

