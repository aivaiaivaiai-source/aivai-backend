# -*- coding: utf-8 -*-
"""Stationery & Books V2 — taxonomy + Package A Create + Package B Search SoT.

Backend/API is Create + Search authority. Flutter is renderer / offline fallback.
"""
from __future__ import annotations

from typing import Any, Literal

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

STATIONERY_ROOT_SLUG = "stationery-books"
STATIONERY_ROOT_LABEL = "Канцтовары, книги и учебные товары"
STATIONERY_V2_ENTITY_TYPE = CategoryEntityType.object

STATIONERY_KIND_KEY = "stationery_kind"
STATIONERY_KIND_LABEL = "Товар"
STATIONERY_SELLER_KEY = "seller_type"
STATIONERY_SELLER_LABEL = "Продавец"
STATIONERY_CONDITION_KEY = "condition"
STATIONERY_CONDITION_LABEL = "Состояние"
STATIONERY_GRADE_KEY = "school_grade"
STATIONERY_GRADE_LABEL = "Класс"

# Package A shared-goods seller (no Компания).
STATIONERY_SELLER_TARGET: tuple[str, ...] = GOODS_SELLER_CHOICES
STATIONERY_CONDITION_CHOICES: tuple[str, ...] = ("Новое", "Б/у")

STATIONERY_V2_LEGACY_RETIRED_SLUGS: frozenset[str] = frozenset(
    {
        "books-fiction",
        "books-study",
    }
)

# Keep slug; rename display to content (not e-reader hardware).
STATIONERY_EBOOKS_SLUG = "stationery-books-elektronnye-knigi"
STATIONERY_EBOOKS_LABEL = "Электронные издания"
STATIONERY_STATIONERY_SLUG = "stationery-books-kantselyarskie-tovary"
STATIONERY_TEXTBOOKS_SLUG = "stationery-books-uchebniki-i-uchebnye-posobiya"

STATIONERY_V2_CANONICAL_LEAVES: tuple[tuple[str, str, int], ...] = (
    ("Канцелярские товары", STATIONERY_STATIONERY_SLUG, 10),
    ("Учебники и учебные пособия", STATIONERY_TEXTBOOKS_SLUG, 20),
    ("Художественная литература", "stationery-books-hudozhestvennaya-literatura", 30),
    ("Научная литература", "stationery-books-nauchnaya-literatura", 40),
    ("Религиозная литература", "stationery-books-religioznaya-literatura", 50),
    ("Иностранная литература", "stationery-books-inostrannaya-literatura", 60),
    (STATIONERY_EBOOKS_LABEL, STATIONERY_EBOOKS_SLUG, 70),
    (
        "Товары для творчества/рисования",
        "stationery-books-tovary-dlya-tvorchestva-risovaniya",
        80,
    ),
    ("Товары для офиса", "stationery-books-tovary-dlya-ofisa", 90),
    ("Глобусы, карты", "stationery-books-globusy-karty", 100),
    ("Музыкальные книги и ноты", "stationery-books-muzykalnye-knigi-i-noty", 110),
    (
        "Комиксы, манга/графич.е романы",
        "stationery-books-komiksy-manga-grafich-e-romany",
        120,
    ),
    (
        "Журналы и периодические издания",
        "stationery-books-zhurnaly-i-periodicheskie-izdaniya",
        130,
    ),
    (
        "Коллекционные и редкие издания",
        "stationery-books-kollektsionnye-i-redkie-izdaniya",
        140,
    ),
    (
        "Прочие книги и канцтовары",
        "stationery-books-prochie-knigi-i-kantstovary",
        150,
    ),
)

STATIONERY_V2_CANONICAL_SLUGS: frozenset[str] = frozenset(
    slug for _label, slug, _sort in STATIONERY_V2_CANONICAL_LEAVES
)
STATIONERY_V2_RETIRED_SLUGS: frozenset[str] = frozenset(
    STATIONERY_V2_LEGACY_RETIRED_SLUGS
)
STATIONERY_V2_EXPECTED_L2_COUNT = len(STATIONERY_V2_CANONICAL_LEAVES)  # 15

STATIONERY_V2_SECTION_SLUGS: dict[str, str] = {
    "stationery": STATIONERY_STATIONERY_SLUG,
    "textbooks": STATIONERY_TEXTBOOKS_SLUG,
    "fiction": "stationery-books-hudozhestvennaya-literatura",
    "science": "stationery-books-nauchnaya-literatura",
    "religion": "stationery-books-religioznaya-literatura",
    "foreign": "stationery-books-inostrannaya-literatura",
    "ebooks": STATIONERY_EBOOKS_SLUG,
    "art": "stationery-books-tovary-dlya-tvorchestva-risovaniya",
    "office": "stationery-books-tovary-dlya-ofisa",
    "globes": "stationery-books-globusy-karty",
    "music": "stationery-books-muzykalnye-knigi-i-noty",
    "comics": "stationery-books-komiksy-manga-grafich-e-romany",
    "magazines": "stationery-books-zhurnaly-i-periodicheskie-izdaniya",
    "rare": "stationery-books-kollektsionnye-i-redkie-izdaniya",
    "other": "stationery-books-prochie-knigi-i-kantstovary",
}

STATIONERY_CREATE_FORBIDDEN: frozenset[str] = frozenset(
    {
        "language",
        "author",
        "publisher",
        "isbn",
        "year",
        "publication_year",
        "brand",
        "color",
        "material",
        "size",
        "paper_format",
        "quantity",
        "pack_count",
        "genre",
        "binding",
        "cover",
        "page_count",
        "edition",
        "item_type",
        "price_basis",
    }
)

_ALWAYS_CREATE: frozenset[str] = frozenset(
    {
        STATIONERY_KIND_KEY,
        STATIONERY_SELLER_KEY,
        STATIONERY_CONDITION_KEY,
        STATIONERY_GRADE_KEY,
        "price",
        "negotiable",
        "contact_methods",
    }
)

# Package B Search — explicit allowlist (Create ≠ Search).
# Geo is shared Search UX (region/city), not CategoryFilter rows.
STATIONERY_V2_SEARCH_ALLOWLIST: frozenset[str] = frozenset(
    {
        STATIONERY_KIND_KEY,
        STATIONERY_CONDITION_KEY,
        STATIONERY_GRADE_KEY,
        STATIONERY_SELLER_KEY,
        "geo",
    }
)

STATIONERY_V2_SEARCH_EAV_KEYS: frozenset[str] = frozenset(
    {
        STATIONERY_KIND_KEY,
        STATIONERY_CONDITION_KEY,
        STATIONERY_GRADE_KEY,
        STATIONERY_SELLER_KEY,
    }
)

STATIONERY_V2_SEARCH_EXCLUDE: frozenset[str] = frozenset(
    set(STATIONERY_CREATE_FORBIDDEN)
    | {
        "price",
        "negotiable",
        "contact_methods",
        "price_basis",
        "currency",
        "language",
        "author",
        "publisher",
        "isbn",
        "year",
        "brand",
        "color",
        "material",
        "size",
        "paper_format",
        "quantity",
        "item_type",
    }
)

STATIONERY_V2_SEARCH_POLICY_PREP: frozenset[str] = STATIONERY_V2_SEARCH_ALLOWLIST

# School kinds added under Канцтовары (Kids GAP closure).
STATIONERY_SCHOOL_DIARY_KIND = "Школьные дневники"
STATIONERY_SCHOOL_BACKPACK_KIND = "Школьные рюкзаки"
STATIONERY_SHOE_BAG_KIND = "Мешки для сменной обуви"

STATIONERY_SCHOOL_KIND_OWNERSHIP: dict[str, tuple[str, str, str]] = {
    "Школьная форма": (
        "MOVED",
        "kids-detskaya-odezhda",
        "Child garment — Kids clothing authority, not Stationery",
    ),
    STATIONERY_SCHOOL_DIARY_KIND: (
        "EXACT_DESTINATION",
        STATIONERY_STATIONERY_SLUG,
        "Canonical Stationery канцтовары kind",
    ),
    STATIONERY_SCHOOL_BACKPACK_KIND: (
        "EXACT_DESTINATION",
        STATIONERY_STATIONERY_SLUG,
        "School-purpose backpack — Stationery, not Fashion/Kids",
    ),
    STATIONERY_SHOE_BAG_KIND: (
        "EXACT_DESTINATION",
        STATIONERY_STATIONERY_SLUG,
        "School shoe-change bag — Stationery",
    ),
    "Другие товары для школы": (
        "NEAREST_DESTINATION",
        "stationery-books-prochie-knigi-i-kantstovary",
        "No broad school L2; use specific kinds or Прочие Другое",
    ),
}

# School subject kinds eligible for structured Класс (Package A candidate only).
STATIONERY_SCHOOL_GRADE_KINDS: frozenset[str] = frozenset(
    {
        "Математика",
        "Алгебра",
        "Геометрия",
        "Кыргызский язык",
        "Русский язык",
        "Английский язык",
        "Литература",
        "История",
        "Биология",
        "Химия",
        "Физика",
        "География",
        "Информатика",
        "Прописи",
        "Школьные атласы",
    }
)
STATIONERY_SCHOOL_GRADE_OPTIONS: tuple[str, ...] = tuple(
    f"{n} класс" for n in range(1, 12)
)
STATIONERY_GRADE_TARGET: Literal["RETAIN_STRUCTURED", "DROP"] = "RETAIN_STRUCTURED"
STATIONERY_GRADE_RATIONALE = (
    "Structured Класс materially improves Create/Search for school-subject "
    "textbooks/workbooks; exclude ORT/university/other textbooks via applies_to."
)

ConditionDecision = Literal["YES", "NO", "PRODUCT_DECISION"]


def _cond(decision: ConditionDecision, reason: str) -> tuple[ConditionDecision, str]:
    return decision, reason


# Independent Condition expectations (not derived from a production allowlist).
# Books / collectibles / durable bags / durable art-office → YES.
# Consumable pens/paper/glue/notebooks → NO.
STATIONERY_V2_CONDITION_MATRIX: dict[str, tuple[ConditionDecision, str]] = {
    # Канцтовары
    "Ручки": _cond("NO", "Consumable writing supply"),
    "Карандаши": _cond("NO", "Consumable writing supply"),
    "Тетради": _cond("NO", "Consumable paper goods"),
    "Блокноты": _cond("NO", "Consumable paper goods"),
    "Ежедневники": _cond("NO", "Consumable planner; weak second-hand signal"),
    STATIONERY_SCHOOL_DIARY_KIND: _cond(
        "NO", "Consumable school diary; weak second-hand signal"
    ),
    "Пеналы": _cond("YES", "Durable accessory with used market"),
    STATIONERY_SCHOOL_BACKPACK_KIND: _cond(
        "YES", "Durable school bag; strong used market"
    ),
    STATIONERY_SHOE_BAG_KIND: _cond("YES", "Durable school bag accessory"),
    "Линейки": _cond("NO", "Cheap consumable/tool"),
    "Клей": _cond("NO", "Consumable"),
    "Корректоры": _cond("NO", "Consumable"),
    "Канцелярские ножницы": _cond("YES", "Durable tool; used market exists"),
    "Другие канцелярские товары": _cond(
        "NO", "Catch-all defaults off; Description for exceptions"
    ),
    # Учебники
    **{
        k: _cond("YES", "Textbook/workbook second-hand market")
        for k in STATIONERY_SCHOOL_GRADE_KINDS
    },
    "Подготовка к ОРТ": _cond("YES", "Educational material used market"),
    "Вузские учебники": _cond("YES", "University textbook used market"),
    "Другие учебники": _cond("YES", "Educational book used market"),
    # Fiction / science / religion / foreign
    "Романы": _cond("YES", "Book used market"),
    "Детективы": _cond("YES", "Book used market"),
    "Фантастика": _cond("YES", "Book used market"),
    "Фэнтези": _cond("YES", "Book used market"),
    "Поэзия": _cond("YES", "Book used market"),
    "Повести и рассказы": _cond("YES", "Book used market"),
    "Пьесы": _cond("YES", "Book used market"),
    "Другая художественная литература": _cond("YES", "Book used market"),
    "Научно-популярные": _cond("YES", "Book used market"),
    "Психология": _cond("YES", "Book used market"),
    "Саморазвитие": _cond("YES", "Book used market"),
    "Бизнес-книги": _cond("YES", "Book used market"),
    "Философия": _cond("YES", "Book used market"),
    "Право": _cond("YES", "Book used market"),
    "Другая научная литература": _cond("YES", "Book used market"),
    "Коран": _cond("YES", "Book used market"),
    "Библия": _cond("YES", "Book used market"),
    "Исламская литература": _cond("YES", "Book used market"),
    "Христианская литература": _cond("YES", "Book used market"),
    "Другая религиозная литература": _cond("YES", "Book used market"),
    "Книги на английском": _cond("YES", "Book used market"),
    "Книги на немецком": _cond("YES", "Book used market"),
    "Книги на турецком": _cond("YES", "Book used market"),
    "Книги на китайском": _cond("YES", "Book used market"),
    "Книги на корейском": _cond("YES", "Book used market"),
    "Другая иностранная литература": _cond("YES", "Book used market"),
    # Digital publications (content, not hardware)
    "Аудиокниги": _cond("NO", "Digital content; condition weak"),
    "Электронные учебные издания": _cond("NO", "Digital content; condition weak"),
    "Электронная художественная литература": _cond(
        "NO", "Digital content; condition weak"
    ),
    "Другие электронные издания": _cond("NO", "Digital content; condition weak"),
    # Art
    "Краски для рисования": _cond("NO", "Consumable art supply"),
    "Кисти": _cond("YES", "Durable art tool"),
    "Цветные карандаши": _cond("NO", "Consumable"),
    "Фломастеры и маркеры": _cond("NO", "Consumable"),
    "Бумага для рисования": _cond("NO", "Consumable paper"),
    "Холсты": _cond("YES", "Durable art surface; used market"),
    "Пластилин": _cond("NO", "Consumable"),
    "Мольберты": _cond("YES", "Durable equipment"),
    "Другие товары для рисования": _cond("NO", "Catch-all defaults off"),
    # Office
    "Бумага": _cond("NO", "Consumable"),
    "Папки и файлы": _cond("NO", "Low-value consumable/office supply"),
    "Конверты": _cond("NO", "Consumable"),
    "Степлеры": _cond("YES", "Durable office tool"),
    "Дыроколы": _cond("YES", "Durable office tool"),
    "Штампы и печати": _cond("YES", "Durable office tool"),
    "Калькуляторы": _cond("YES", "Durable device; ordinary school/office keep here"),
    "Бейджи": _cond("NO", "Consumable/low-value"),
    "Другие офисные товары": _cond("NO", "Catch-all defaults off"),
    # Globes / maps
    "Глобусы": _cond("YES", "Durable educational object"),
    "Настенные карты": _cond("YES", "Durable educational object"),
    "Дорожные карты": _cond("NO", "Often disposable/paper"),
    "Другие карты и глобусы": _cond("NO", "Catch-all defaults off"),
    # Music books
    "Ноты": _cond("YES", "Printed edition used market"),
    "Самоучители": _cond("YES", "Book used market"),
    "Песенники": _cond("YES", "Book used market"),
    "Другие ноты и музыкальные книги": _cond("YES", "Book used market"),
    # Comics / magazines / collectibles
    "Комиксы": _cond("YES", "Collectible/book used market"),
    "Манга": _cond("YES", "Collectible/book used market"),
    "Манхва": _cond("YES", "Collectible/book used market"),
    "Графические романы": _cond("YES", "Book used market"),
    "Другие комиксы": _cond("YES", "Book used market"),
    "Журналы": _cond("YES", "Periodical used/collectible market"),
    "Газеты": _cond("NO", "Ephemeral consumable press"),
    "Каталоги": _cond("NO", "Ephemeral print"),
    "Другие периодические издания": _cond("NO", "Catch-all defaults off"),
    "Редкие книги": _cond("YES", "Collectible"),
    "Подарочные издания": _cond("YES", "Collectible/book"),
    "Книги с автографом": _cond("YES", "Collectible"),
    "Другие коллекционные издания": _cond("YES", "Collectible"),
    # Other
    "Закладки": _cond("NO", "Consumable accessory"),
    "Обложки для книг": _cond("NO", "Consumable accessory"),
    "CD и DVD": _cond("YES", "Physical media durable/used market"),
    "Другие книги и канцтовары": _cond("NO", "Catch-all defaults off"),
}


def stationery_v2_all_kinds() -> list[str]:
    from app.seeds.stationery_sections_catalog import STATIONERY_SECTIONS

    out: list[str] = []
    for sec in STATIONERY_SECTIONS.values():
        for role in sec["roles"]:
            out.append(role["label"])
    return out


def stationery_v2_condition_yes_kinds() -> frozenset[str]:
    return frozenset(
        k for k, (d, _r) in STATIONERY_V2_CONDITION_MATRIX.items() if d == "YES"
    )


def stationery_v2_assert_cleanup_contracts() -> None:
    assert STATIONERY_V2_EXPECTED_L2_COUNT == 15
    assert len(STATIONERY_V2_CANONICAL_SLUGS) == 15
    assert STATIONERY_V2_LEGACY_RETIRED_SLUGS.isdisjoint(STATIONERY_V2_CANONICAL_SLUGS)
    assert STATIONERY_EBOOKS_SLUG in STATIONERY_V2_CANONICAL_SLUGS
    labels = {label for label, _s, _o in STATIONERY_V2_CANONICAL_LEAVES}
    assert STATIONERY_EBOOKS_LABEL in labels
    assert "Электронные книги" not in labels
    assert STATIONERY_SELLER_TARGET == ("Частное лицо", "Магазин", "Другой")
    assert "Компания" not in STATIONERY_SELLER_TARGET

    from app.seeds.stationery_sections_catalog import STATIONERY_SECTIONS

    assert len(STATIONERY_SECTIONS) == 15
    stationery = STATIONERY_SECTIONS["stationery"]
    assert stationery["category_slug"] == STATIONERY_STATIONERY_SLUG
    kinds = [r["label"] for r in stationery["roles"]]
    for required in (
        STATIONERY_SCHOOL_DIARY_KIND,
        STATIONERY_SCHOOL_BACKPACK_KIND,
        STATIONERY_SHOE_BAG_KIND,
    ):
        assert required in kinds, required
    ebooks = STATIONERY_SECTIONS["ebooks"]
    assert ebooks["label"] == STATIONERY_EBOOKS_LABEL
    assert ebooks["category_slug"] == STATIONERY_EBOOKS_SLUG

    all_kinds = stationery_v2_all_kinds()
    assert len(all_kinds) == len(set(all_kinds)), "duplicate kind labels"
    missing = [k for k in all_kinds if k not in STATIONERY_V2_CONDITION_MATRIX]
    assert not missing, f"Condition matrix gaps: {missing}"
    unknown = [
        k
        for k, (d, _) in STATIONERY_V2_CONDITION_MATRIX.items()
        if d == "PRODUCT_DECISION"
    ]
    assert not unknown, f"Unresolved Condition PRODUCT_DECISION: {unknown}"
    # Matrix must not invent kinds absent from catalog.
    extra = sorted(set(STATIONERY_V2_CONDITION_MATRIX) - set(all_kinds))
    assert not extra, f"Condition matrix extras: {extra}"

    assert STATIONERY_GRADE_TARGET == "RETAIN_STRUCTURED"
    assert STATIONERY_SCHOOL_GRADE_KINDS
    assert STATIONERY_SCHOOL_GRADE_OPTIONS[0] == "1 класс"
    assert STATIONERY_SCHOOL_GRADE_OPTIONS[-1] == "11 класс"


def stationery_v2_kids_school_gap_report() -> list[dict[str, Any]]:
    return [
        {
            "kind": kind,
            "decision": decision,
            "destination": dest,
            "reason": reason,
        }
        for kind, (decision, dest, reason) in STATIONERY_SCHOOL_KIND_OWNERSHIP.items()
    ]


def _choices(*labels: str) -> dict[str, Any]:
    return {"choices": [{"value": label, "label": label} for label in labels]}


def _dep_field(
    key: str,
    label: str,
    ftype: CategoryFieldType,
    required: bool,
    sort: int,
    options: dict[str, Any] | None,
    hint: str | None = None,
) -> tuple:
    return (key, label, ftype, required, sort, options, hint)


def _stationery_sections() -> dict[str, dict[str, Any]]:
    from app.seeds.stationery_sections_catalog import STATIONERY_SECTIONS

    return STATIONERY_SECTIONS


def stationery_v2_kind_count() -> int:
    return len(stationery_v2_all_kinds())


def stationery_v2_condition_visible_for_kind(kind: str) -> bool:
    return kind in stationery_v2_condition_yes_kinds()


def stationery_v2_grade_visible_for_kind(kind: str) -> bool:
    return kind in STATIONERY_SCHOOL_GRADE_KINDS


def stationery_v2_assert_package_a_contracts() -> None:
    stationery_v2_assert_cleanup_contracts()
    sections = _stationery_sections()
    if len(sections) != STATIONERY_V2_EXPECTED_L2_COUNT:
        raise RuntimeError(
            f"Stationery expected {STATIONERY_V2_EXPECTED_L2_COUNT} sections, "
            f"got {len(sections)}"
        )
    catalog_slugs = {cat["category_slug"] for cat in sections.values()}
    if catalog_slugs != STATIONERY_V2_CANONICAL_SLUGS:
        raise RuntimeError("Stationery catalog slugs ≠ canonical L2 set")
    if set(STATIONERY_V2_SECTION_SLUGS.values()) != STATIONERY_V2_CANONICAL_SLUGS:
        raise RuntimeError("SECTION_SLUGS ≠ canonical L2 set")
    if STATIONERY_SELLER_TARGET != GOODS_SELLER_CHOICES:
        raise RuntimeError("Stationery seller must match goods shared seller")
    kinds = set(stationery_v2_all_kinds())
    if stationery_v2_kind_count() != 105:
        raise RuntimeError(
            f"Stationery kind count expected 105, got {stationery_v2_kind_count()}"
        )
    yes = stationery_v2_condition_yes_kinds()
    if not yes <= kinds:
        raise RuntimeError(f"Condition YES kinds missing from catalog: {yes - kinds}")
    if not STATIONERY_SCHOOL_GRADE_KINDS <= kinds:
        raise RuntimeError(
            f"Grade kinds missing: {STATIONERY_SCHOOL_GRADE_KINDS - kinds}"
        )
    if STATIONERY_GRADE_TARGET != "RETAIN_STRUCTURED":
        raise RuntimeError("Grade target must stay RETAIN_STRUCTURED for Package A")


def build_stationery_v2_core_fields() -> dict[str, list]:
    """Create cores for all active Stationery L2 (Package A SoT)."""
    stationery_v2_assert_package_a_contracts()
    sections = _stationery_sections()
    cond_approved = stationery_v2_condition_yes_kinds()
    out: dict[str, list] = {}

    for section_key, slug in STATIONERY_V2_SECTION_SLUGS.items():
        catalog = sections[section_key]
        kinds = [str(r["label"]) for r in catalog["roles"]]
        fields: list = [
            _dep_field(
                STATIONERY_KIND_KEY,
                STATIONERY_KIND_LABEL,
                CategoryFieldType.enum,
                True,
                10,
                _choices(*kinds),
                hint=str(catalog.get("question") or "Какой товар?"),
            ),
            _dep_field(
                STATIONERY_SELLER_KEY,
                STATIONERY_SELLER_LABEL,
                CategoryFieldType.enum,
                True,
                20,
                _choices(*STATIONERY_SELLER_TARGET),
            ),
        ]

        cond_kinds = [k for k in kinds if k in cond_approved]
        if cond_kinds:
            cond_opts: dict[str, Any] = _choices(*STATIONERY_CONDITION_CHOICES)
            if set(cond_kinds) != set(kinds):
                cond_opts["depends_on"] = {
                    "field": STATIONERY_KIND_KEY,
                    "values": list(cond_kinds),
                }
            fields.append(
                _dep_field(
                    STATIONERY_CONDITION_KEY,
                    STATIONERY_CONDITION_LABEL,
                    CategoryFieldType.enum,
                    False,
                    30,
                    cond_opts,
                )
            )

        grade_kinds = [k for k in kinds if k in STATIONERY_SCHOOL_GRADE_KINDS]
        if grade_kinds:
            grade_opts: dict[str, Any] = _choices(*STATIONERY_SCHOOL_GRADE_OPTIONS)
            grade_opts["depends_on"] = {
                "field": STATIONERY_KIND_KEY,
                "values": list(grade_kinds),
            }
            fields.append(
                _dep_field(
                    STATIONERY_GRADE_KEY,
                    STATIONERY_GRADE_LABEL,
                    CategoryFieldType.enum,
                    False,
                    40,
                    grade_opts,
                )
            )

        fields.extend(
            [
                _dep_field(
                    "price",
                    "Цена",
                    CategoryFieldType.price,
                    True,
                    50,
                    None,
                    hint="Цена (СОМ / KGS)",
                ),
                _dep_field(
                    "negotiable",
                    "Торг",
                    CategoryFieldType.enum,
                    False,
                    60,
                    _choices(*GOODS_NEGOTIABLE_CHOICES),
                ),
                _dep_field(
                    "contact_methods",
                    "Способы связи",
                    CategoryFieldType.enum,
                    True,
                    70,
                    _choices(*CONTACT_METHOD_CHOICES),
                ),
            ]
        )

        for row in fields:
            key = row[0]
            if key in STATIONERY_CREATE_FORBIDDEN:
                raise RuntimeError(f"forbidden Create field {slug}.{key}")
            if key not in _ALWAYS_CREATE:
                raise RuntimeError(f"unapproved Create field {slug}.{key}")
            opts = row[5]
            if opts and opts.get("choices") is not None and len(opts["choices"]) == 0:
                raise RuntimeError(f"empty picker {slug}.{key}")

        out[slug] = fields
    return out


def stationery_v2_all_kind_audit() -> list[dict[str, Any]]:
    """All-kind audit rows (Package A). Pair with independent expectations in tests."""
    cores = build_stationery_v2_core_fields()
    sections = _stationery_sections()
    rows: list[dict[str, Any]] = []
    for section_key, slug in STATIONERY_V2_SECTION_SLUGS.items():
        catalog = sections[section_key]
        fields = cores[slug]
        keys = [r[0] for r in fields]
        kind_row = next(r for r in fields if r[0] == STATIONERY_KIND_KEY)
        kind_opts = [c["value"] for c in kind_row[5]["choices"]]
        seller_row = next(r for r in fields if r[0] == STATIONERY_SELLER_KEY)
        seller_opts = [c["value"] for c in seller_row[5]["choices"]]
        cond_row = next((r for r in fields if r[0] == STATIONERY_CONDITION_KEY), None)
        cond_values = (
            set((cond_row[5].get("depends_on") or {}).get("values") or kind_opts)
            if cond_row is not None
            else set()
        )
        if cond_row is not None and "depends_on" not in (cond_row[5] or {}):
            cond_values = set(kind_opts)
        grade_row = next((r for r in fields if r[0] == STATIONERY_GRADE_KEY), None)
        grade_values = (
            set((grade_row[5].get("depends_on") or {}).get("values") or [])
            if grade_row is not None
            else set()
        )

        specials = [
            k
            for k in keys
            if k
            not in {
                STATIONERY_KIND_KEY,
                STATIONERY_SELLER_KEY,
                "price",
                "negotiable",
                "contact_methods",
            }
        ]

        for role in catalog["roles"]:
            kind = str(role["label"])
            cond_yes = stationery_v2_condition_visible_for_kind(kind)
            grade_yes = stationery_v2_grade_visible_for_kind(kind)
            kind_specials = list(specials)
            if not cond_yes:
                kind_specials = [
                    k for k in kind_specials if k != STATIONERY_CONDITION_KEY
                ]
            if not grade_yes:
                kind_specials = [k for k in kind_specials if k != STATIONERY_GRADE_KEY]
            rows.append(
                {
                    "kind": kind,
                    "section": section_key,
                    "slug": slug,
                    "stationery_kind_valid": kind in kind_opts,
                    "condition": "YES" if cond_yes else "NO",
                    "condition_in_schema": cond_yes == (kind in cond_values),
                    "grade": "YES" if grade_yes else "NO",
                    "grade_in_schema": grade_yes == (kind in grade_values),
                    "seller": seller_opts,
                    "price": "price" in keys,
                    "special_count": len(kind_specials),
                    "forbidden": sorted(set(keys) & STATIONERY_CREATE_FORBIDDEN),
                    "language_absent": "language" not in keys,
                    "item_type_absent": "item_type" not in keys,
                    "components": {
                        STATIONERY_KIND_KEY: "enum",
                        "price": "price",
                        STATIONERY_SELLER_KEY: "enum",
                        "contact_methods": "enum",
                    },
                    "ownership": "stationery",
                }
            )
    return rows


def stationery_v2_complexity_histogram() -> dict[str, int]:
    """special_count histogram: kind + 0–2 specials (condition/grade)."""
    hist = {"0": 0, "1": 0, "2": 0, "3+": 0}
    for row in stationery_v2_all_kind_audit():
        n = int(row["special_count"])
        if n <= 0:
            hist["0"] += 1
        elif n == 1:
            hist["1"] += 1
        elif n == 2:
            hist["2"] += 1
        else:
            hist["3+"] += 1
    return hist


def stationery_v2_section_kinds(slug: str) -> list[str]:
    """Kinds for a canonical Stationery L2 slug (catalog order)."""
    for section_key, section_slug in STATIONERY_V2_SECTION_SLUGS.items():
        if section_slug != slug:
            continue
        catalog = _stationery_sections()[section_key]
        return [str(r["label"]) for r in catalog["roles"]]
    raise KeyError(f"Unknown Stationery L2 slug: {slug}")


def _search_filter(
    key: str,
    label: str,
    ftype: CategoryFilterType,
    sort: int,
    config: dict[str, Any] | None,
) -> tuple:
    return (key, label, ftype, sort, config)


def build_stationery_v2_search_filters() -> dict[str, list]:
    """Package B Search SoT per canonical Stationery L2.

    Explicit allowlist only. Condition/Grade inherit Package A depends_on
    from Create cores (Create↔Search parity). Price / negotiable / contacts /
    Language / author / ISBN / brand / size never Search.
    Geo is shared Search UX, not CategoryFilter rows.
    """
    cores = build_stationery_v2_core_fields()
    out: dict[str, list] = {}
    for slug, fields in cores.items():
        filters: list = []
        for key, label, _ftype, _required, sort, options, _hint in fields:
            if key not in STATIONERY_V2_SEARCH_EAV_KEYS:
                continue
            if key in STATIONERY_V2_SEARCH_EXCLUDE:
                continue
            if key not in STATIONERY_V2_SEARCH_ALLOWLIST:
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
    if set(out) != STATIONERY_V2_CANONICAL_SLUGS:
        raise RuntimeError(
            "Stationery Search filter map != canonical L2 slugs: "
            f"extra={sorted(set(out) - STATIONERY_V2_CANONICAL_SLUGS)} "
            f"missing={sorted(STATIONERY_V2_CANONICAL_SLUGS - set(out))}"
        )
    return out


def stationery_v2_search_kind_audit_row(
    section_key: str, slug: str, kind: str
) -> dict[str, Any]:
    """All-kind Search audit row (independent of Create visible_components)."""
    cond_yes = stationery_v2_condition_visible_for_kind(kind)
    grade_yes = stationery_v2_grade_visible_for_kind(kind)
    visible = [STATIONERY_KIND_KEY, STATIONERY_SELLER_KEY]
    if cond_yes:
        visible.append(STATIONERY_CONDITION_KEY)
    if grade_yes:
        visible.append(STATIONERY_GRADE_KEY)
    return {
        "l2": slug,
        "section": section_key,
        "kind": kind,
        "search_stationery_kind": "YES",
        "search_seller": "YES",
        "search_condition": "YES" if cond_yes else "NO",
        "search_grade": "YES" if grade_yes else "NO",
        "search_language": "NO",
        "search_author": "NO",
        "search_publisher": "NO",
        "search_isbn": "NO",
        "search_year": "NO",
        "search_brand": "NO",
        "search_color": "NO",
        "search_material": "NO",
        "search_size": "NO",
        "search_price": "NO",
        "search_negotiable": "NO",
        "search_contacts": "NO",
        "search_geo": "YES",
        "retired_resurrected": slug in STATIONERY_V2_RETIRED_SLUGS,
        "ownership": "stationery",
        "visible_search_keys": visible,
        "ui_components": {
            STATIONERY_KIND_KEY: "multi_select",
            STATIONERY_SELLER_KEY: "multi_select",
            **(
                {STATIONERY_CONDITION_KEY: "multi_select"}
                if cond_yes
                else {}
            ),
            **({STATIONERY_GRADE_KEY: "multi_select"} if grade_yes else {}),
            "geo": "region_city",
        },
    }


def stationery_v2_all_search_kind_audit() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    sections = _stationery_sections()
    for section_key, slug in STATIONERY_V2_SECTION_SLUGS.items():
        catalog = sections[section_key]
        for role in catalog["roles"]:
            rows.append(
                stationery_v2_search_kind_audit_row(
                    section_key, slug, str(role["label"])
                )
            )
    return rows


def stationery_v2_search_policy_prep() -> dict[str, Any]:
    return {
        "allow": sorted(STATIONERY_V2_SEARCH_ALLOWLIST),
        "eav": sorted(STATIONERY_V2_SEARCH_EAV_KEYS),
        "exclude": sorted(STATIONERY_V2_SEARCH_EXCLUDE),
    }

