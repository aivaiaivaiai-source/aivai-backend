# -*- coding: utf-8 -*-
"""Sport / Recreation / Hobbies V2 — taxonomy + Package A Create contracts.

Package B Search filters are NOT seeded here.
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

SPORT_ROOT_SLUG = "sports-hobby"
SPORT_ROOT_LABEL = "Спорт, отдых и хобби"
SPORT_V2_ENTITY_TYPE = CategoryEntityType.object

# Legacy triad from category_data (soft-retired).
SPORT_V2_LEGACY_L2_SLUGS = frozenset(
    {
        "sports-equipment",
        "sports-tourism",
        "sports-music",
    }
)

# National craft L2 — wrong root; no destination in this cleanup.
SPORT_V2_RETIRED_NATIONAL_CRAFT_SLUGS = frozenset(
    {
        "sports-hobby-yurty-i-natsionalnye-izdeliya",
        "sports-hobby-shyrdaki-i-izdeliya-iz-voyloka",
    }
)

SPORT_V2_RETIRED_SLUGS = frozenset(
    set(SPORT_V2_LEGACY_L2_SLUGS) | set(SPORT_V2_RETIRED_NATIONAL_CRAFT_SLUGS)
)

SPORT_V2_RETIRED_KINDS: dict[str, tuple[str, str]] = {
    "Охотничьи ножи": (
        "RETIRED_POLICY_RESTRICTED_NO_DESTINATION",
        "Restricted hunting knives removed from active AiVai Sport catalog.",
    ),
    "Юрты": (
        "RETIRED_NO_CANONICAL_DESTINATION",
        "National craft / housing identity is not Sport/Hobby.",
    ),
    "Тундуки": (
        "RETIRED_NO_CANONICAL_DESTINATION",
        "National craft identity is not Sport/Hobby.",
    ),
    "Ууки": (
        "RETIRED_NO_CANONICAL_DESTINATION",
        "National craft identity is not Sport/Hobby.",
    ),
    "Канаты для юрты": (
        "RETIRED_NO_CANONICAL_DESTINATION",
        "National craft identity is not Sport/Hobby.",
    ),
    "Боо": (
        "RETIRED_NO_CANONICAL_DESTINATION",
        "National craft identity is not Sport/Hobby.",
    ),
    "Другие национальные изделия": (
        "RETIRED_NO_CANONICAL_DESTINATION",
        "National craft identity is not Sport/Hobby.",
    ),
    "Шырдаки": (
        "RETIRED_NO_CANONICAL_DESTINATION",
        "Felt craft / decor identity is not Sport/Hobby.",
    ),
    "Ала кийиз": (
        "RETIRED_NO_CANONICAL_DESTINATION",
        "Felt craft / decor identity is not Sport/Hobby.",
    ),
    "Войлочные ковры": (
        "RETIRED_NO_CANONICAL_DESTINATION",
        "Felt craft / decor identity is not Sport/Hobby.",
    ),
    "Войлочные сумки": (
        "RETIRED_NO_CANONICAL_DESTINATION",
        "Felt craft / decor identity is not Sport/Hobby.",
    ),
    "Войлочные тапочки": (
        "RETIRED_NO_CANONICAL_DESTINATION",
        "Felt craft / decor identity is not Sport/Hobby.",
    ),
    "Другие изделия из войлока": (
        "RETIRED_NO_CANONICAL_DESTINATION",
        "Felt craft / decor identity is not Sport/Hobby.",
    ),
}

KindClass = Literal[
    "SPORT_GOOD",
    "FITNESS_GOOD",
    "NUTRITION_CONSUMABLE",
    "OUTDOOR_GOOD",
    "FISHING_GOOD",
    "MUSIC_INSTRUMENT",
    "HORSE_GEAR",
    "COLLECTIBLE",
    "BOARD_GAME",
    "CRAFT_HOBBY",
    "ANTIQUE_ART",
    "HOBBY_OTHER",
]

SPORT_SELLER_OPTIONS = GOODS_SELLER_CHOICES
SPORT_CONDITION_OPTIONS = ("Новое", "Б/у")
SPORT_KIND_KEY = "sport_kind"
SPORT_KIND_LABEL = "Товар"
SPORT_SELLER_KEY = "seller_type"
SPORT_SELLER_LABEL = "Продавец"
SPORT_CONDITION_KEY = "condition"
SPORT_CONDITION_LABEL = "Состояние"

SPORT_AI_CHARACTERISTIC_RULE = (
    "AI must not invent brand, model, size, weight, length, power, material, "
    "color, technical compatibility, sport level, or condition unless "
    "explicitly supplied by the user and permitted by the Backend schema."
)

SPORT_CREATE_FORBIDDEN: frozenset[str] = frozenset(
    {
        "size",
        "brand",
        "model",
        "material",
        "color",
        "weight",
        "length",
        "diameter",
        "power",
        "capacity",
        "resistance",
        "gear_count",
        "frame_size",
        "price_basis",
        "gender",
        "age",
        "level",
        "Компания",
        "Мастерская",
    }
)

_ALWAYS_CREATE: frozenset[str] = frozenset(
    {
        SPORT_KIND_KEY,
        SPORT_SELLER_KEY,
        SPORT_CONDITION_KEY,
        "price",
        "negotiable",
        "contact_methods",
    }
)

SPORT_V2_SEARCH_POLICY = "SIMPLE"

# Package B Search — explicit allowlist (Create ≠ Search).
# Geo is shared Search UX (region/city), not CategoryFilter rows.
SPORT_V2_SEARCH_ALLOWLIST: frozenset[str] = frozenset(
    {
        SPORT_KIND_KEY,
        SPORT_CONDITION_KEY,
        SPORT_SELLER_KEY,
        "geo",
    }
)

SPORT_V2_SEARCH_EAV_KEYS: frozenset[str] = frozenset(
    {
        SPORT_KIND_KEY,
        SPORT_CONDITION_KEY,
        SPORT_SELLER_KEY,
    }
)

SPORT_V2_SEARCH_EXCLUDE: frozenset[str] = frozenset(
    set(SPORT_CREATE_FORBIDDEN)
    | {
        "price",
        "negotiable",
        "contact_methods",
        "price_basis",
        "currency",
        "rental",
        "ticket",
        "membership",
        "ski_pass",
        "subscription",
    }
)

SPORT_V2_SEARCH_FUTURE = (
    SPORT_KIND_KEY,
    SPORT_CONDITION_KEY,
    SPORT_SELLER_KEY,
    "geo",
)

# Canonical modern L2 after national-craft retirement (13).
SPORT_V2_CANONICAL_LEAVES: tuple[tuple[str, str, int], ...] = (
    ("Спортивные товары", "sports-hobby-sportivnye-tovary", 10),
    ("Фитнес и тренажёры", "sports-hobby-fitnes-i-trenazhery", 20),
    ("Спортивное питание", "sports-hobby-sportivnoe-pitanie", 30),
    ("Туризм и кемпинг", "sports-hobby-turizm-i-kemping", 40),
    ("Охота и рыбалка", "sports-hobby-ohota-i-rybalka", 50),
    ("Музыкальные инструменты", "sports-hobby-muzykalnye-instrumenty", 60),
    ("Кыргызские музыкальные инструменты", "sports-hobby-kyrgyzskie-muzyk-nye-inst-menty", 70),
    ("Конный спорт и верховая езда", "sports-hobby-konnyy-sport-i-verhovaya-ezda", 100),
    ("Коллекционирование", "sports-hobby-kollektsionirovanie", 110),
    ("Настольные игры", "sports-hobby-nastolnye-igry", 120),
    ("Рукоделие и творчество", "sports-hobby-rukodelie-i-tvorchestvo", 130),
    ("Антиквариат и предметы искусства", "sports-hobby-antikvariat-i-predmety-iskusstva", 140),
    ("Прочее для спорта, отдыха и хобби", "sports-hobby-prochee-dlya-sporta-otdyha-i-hobbi", 150),
)

SPORT_V2_CANONICAL_SLUGS = frozenset(slug for _, slug, _ in SPORT_V2_CANONICAL_LEAVES)
SPORT_V2_EXPECTED_L2_COUNT = len(SPORT_V2_CANONICAL_LEAVES)

# Section key → kinds (hunting knife removed; national craft sections gone).
SPORT_V2_SECTION_KINDS: dict[str, tuple[str, ...]] = {
    "sport": (
        "Мячи",
        "Ракетки",
        "Клюшки",
        "Боксёрские перчатки",
        "Шлемы",
        "Коньки",
        "Лыжи",
        "Сноуборды",
        "Роликовые коньки",
        "Скейтборды",
        "Другие спортивные товары",
    ),
    "fitness": (
        "Беговые дорожки",
        "Велотренажёры",
        "Эллиптические тренажёры",
        "Гантели",
        "Гири",
        "Штанги и блины",
        "Коврики для йоги",
        "Эспандеры",
        "Другие тренажёры",
    ),
    "nutrition": (
        "Протеин",
        "Гейнеры",
        "Креатин",
        "Аминокислоты",
        "Изотоники",
        "Спортивные батончики",
        "Другое спортивное питание",
    ),
    "camping": (
        "Палатки",
        "Спальники",
        "Туристические коврики",
        "Туристические рюкзаки",
        "Туристические горелки",
        "Термосы",
        "Треккинговые палки",
        "Другие товары для кемпинга",
    ),
    "hunting": (
        "Удочки",
        "Спиннинги",
        "Катушки",
        "Блёсны и приманки",
        "Садки и подсачеки",
        "Эхолоты",
        "Манки",
        "Другие товары для рыбалки и охоты",
    ),
    "music": (
        "Гитары",
        "Скрипки",
        "Барабаны",
        "Пианино",
        "Синтезаторы",
        "Духовые инструменты",
        "Укулеле",
        "Другие музыкальные инструменты",
    ),
    "kyrgyz": (
        "Комуз",
        "Кыл кыяк",
        "Темир комуз",
        "Чоор",
        "Сыбызгы",
        "Добулбас",
        "Другие кыргызские инструменты",
    ),
    "horse": (
        "Сёдла",
        "Уздечки",
        "Вальтрапы",
        "Стремена",
        "Хлысты",
        "Амуниция",
        "Другие товары для верховой езды",
    ),
    "collect": (
        "Монеты",
        "Банкноты",
        "Марки",
        "Значки",
        "Модели",
        "Другие предметы коллекционирования",
    ),
    "board": (
        "Тогуз коргоол",
        "Шахматы",
        "Шашки",
        "Нарды",
        "Карты",
        "Настольные стратегии",
        "Пазлы",
        "Другие настольные игры",
    ),
    "craft": (
        "Спицы и крючки",
        "Наборы для вышивания",
        "Бисер",
        "Макраме",
        "Валяние",
        "Мыловарение",
        "Другие товары для рукоделия",
    ),
    "antique": (
        "Картины",
        "Скульптуры",
        "Иконы",
        "Старинная посуда",
        "Антикварные часы",
        "Другие предметы искусства",
    ),
    "other": (
        "Металлоискатели",
        "Бинокли",
        "Воздушные змеи",
        "Другие товары для хобби",
    ),
}

SPORT_V2_SECTION_META: dict[str, tuple[str, str]] = {
    "sport": ("sports-hobby-sportivnye-tovary", "Спортивные товары"),
    "fitness": ("sports-hobby-fitnes-i-trenazhery", "Фитнес и тренажёры"),
    "nutrition": ("sports-hobby-sportivnoe-pitanie", "Спортивное питание"),
    "camping": ("sports-hobby-turizm-i-kemping", "Туризм и кемпинг"),
    "hunting": ("sports-hobby-ohota-i-rybalka", "Охота и рыбалка"),
    "music": ("sports-hobby-muzykalnye-instrumenty", "Музыкальные инструменты"),
    "kyrgyz": (
        "sports-hobby-kyrgyzskie-muzyk-nye-inst-menty",
        "Кыргызские музыкальные инструменты",
    ),
    "horse": ("sports-hobby-konnyy-sport-i-verhovaya-ezda", "Конный спорт и верховая езда"),
    "collect": ("sports-hobby-kollektsionirovanie", "Коллекционирование"),
    "board": ("sports-hobby-nastolnye-igry", "Настольные игры"),
    "craft": ("sports-hobby-rukodelie-i-tvorchestvo", "Рукоделие и творчество"),
    "antique": (
        "sports-hobby-antikvariat-i-predmety-iskusstva",
        "Антиквариат и предметы искусства",
    ),
    "other": (
        "sports-hobby-prochee-dlya-sporta-otdyha-i-hobbi",
        "Прочее для спорта, отдыха и хобби",
    ),
}

# Independent Condition YES/NO — default NO; positive allowlist of durable goods.
_CONDITION_NO = frozenset(
    {
        # Nutrition / consumables
        "Протеин",
        "Гейнеры",
        "Креатин",
        "Аминокислоты",
        "Изотоники",
        "Спортивные батончики",
        "Другое спортивное питание",
        # Fishing consumables / soft baits
        "Блёсны и приманки",
        # Craft consumables / soft supplies
        "Бисер",
        "Валяние",
        "Мыловарение",
    }
)

# Platform coherence banned identities (must not appear in active Sport kinds).
SPORT_V2_BANNED_KINDS = frozenset(
    {
        "Велосипеды",
        "Детские велосипеды",
        "Детские самокаты",
        "Беговелы",
        "Санки и снегокаты",
        "Рюкзаки",
        "Перчатки",
        "Бутсы",
        "Кроссовки для бега",
        "Футбольная форма",
        "Спортивные костюмы",
        "Купальники",
        "Плавки",
        "Часы",
        "Бильярдные столы",
        "Игровые автоматы",
        "Тренажёры для залов",
        "Коммерческие батуты",
        "Игровые приставки",
        "Геймпады",
        "Игры",
        "Наушники",
        "Микрофоны",
        "Ноты",
        "Краски для рисования",
        "Холсты",
        "Пластилин",
        "Пряжа",
        "Нитки",
        "Ткани",
        "Лошади",
        "Кобылы",
        "Массажёры",
        "Витаминные комплексы",
        "Детские настольные игры",
        "Конструкторы",
        "Редкие книги",
        "Комиксы",
        "Охотничьи ножи",
        "Юрты",
        "Шырдаки",
        "Огнестрельное оружие",
        "Патроны",
        "Арбалеты",
    }
)


def sport_v2_all_kinds() -> tuple[str, ...]:
    out: list[str] = []
    for kinds in SPORT_V2_SECTION_KINDS.values():
        out.extend(kinds)
    return tuple(out)


def sport_v2_kind_count() -> int:
    return len(sport_v2_all_kinds())


def sport_v2_kind_class(kind: str) -> KindClass:
    if kind in SPORT_V2_RETIRED_KINDS:
        raise ValueError(f"Retired kind has no active class: {kind}")
    section = sport_v2_section_for_kind(kind)
    mapping: dict[str, KindClass] = {
        "sport": "SPORT_GOOD",
        "fitness": "FITNESS_GOOD",
        "nutrition": "NUTRITION_CONSUMABLE",
        "camping": "OUTDOOR_GOOD",
        "hunting": "FISHING_GOOD",
        "music": "MUSIC_INSTRUMENT",
        "kyrgyz": "MUSIC_INSTRUMENT",
        "horse": "HORSE_GEAR",
        "collect": "COLLECTIBLE",
        "board": "BOARD_GAME",
        "craft": "CRAFT_HOBBY",
        "antique": "ANTIQUE_ART",
        "other": "HOBBY_OTHER",
    }
    return mapping[section]


def sport_v2_section_for_kind(kind: str) -> str:
    for key, kinds in SPORT_V2_SECTION_KINDS.items():
        if kind in kinds:
            return key
    raise ValueError(f"Unknown Sport kind: {kind}")


def sport_v2_condition_decision(kind: str) -> Literal["YES", "NO"]:
    """Independent YES/NO expectation — not a self-proving schema copy."""
    assert kind in set(sport_v2_all_kinds())
    if kind in _CONDITION_NO:
        return "NO"
    return "YES"


def sport_v2_condition_yes_kinds() -> frozenset[str]:
    return frozenset(
        k for k in sport_v2_all_kinds() if sport_v2_condition_decision(k) == "YES"
    )


def sport_v2_condition_matrix() -> dict[str, int]:
    kinds = sport_v2_all_kinds()
    yes = sum(1 for k in kinds if sport_v2_condition_decision(k) == "YES")
    no = sum(1 for k in kinds if sport_v2_condition_decision(k) == "NO")
    return {"YES": yes, "NO": no}


def _item(label: str) -> dict[str, Any]:
    return {"value": label, "label": label}


def _opts(*labels: str) -> list[dict[str, Any]]:
    return [_item(label) for label in labels]


def _group(label: str, options: tuple[str, ...]) -> dict[str, Any]:
    return {"label": label, "options": _opts(*options)}


def _seller() -> dict[str, Any]:
    return _group(SPORT_SELLER_LABEL, SPORT_SELLER_OPTIONS)


def _condition() -> dict[str, Any]:
    return _group(SPORT_CONDITION_LABEL, SPORT_CONDITION_OPTIONS)


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


def build_sport_v2_sections() -> dict[str, dict[str, Any]]:
    """Offline/API section catalog (Flutter fallback + Search prep)."""
    out: dict[str, dict[str, Any]] = {}
    for key, kinds in SPORT_V2_SECTION_KINDS.items():
        slug, label = SPORT_V2_SECTION_META[key]
        any_condition = any(sport_v2_condition_decision(k) == "YES" for k in kinds)
        filters = [_seller()]
        if any_condition:
            filters.append(_condition())
        out[key] = {
            "category_slug": slug,
            "label": label,
            "question": "Какой товар?",
            "roles": _opts(*kinds),
            "filters": filters,
        }
    return out


def sport_v2_assert_cleanup_contracts() -> None:
    assert SPORT_ROOT_SLUG == "sports-hobby"
    assert SPORT_ROOT_LABEL == "Спорт, отдых и хобби"
    assert SPORT_V2_EXPECTED_L2_COUNT == 13
    assert set(SPORT_V2_SECTION_KINDS) == set(SPORT_V2_SECTION_META)
    assert len(SPORT_V2_CANONICAL_LEAVES) == 13
    assert SPORT_V2_CANONICAL_SLUGS.isdisjoint(SPORT_V2_RETIRED_SLUGS)
    assert "Охотничьи ножи" in SPORT_V2_RETIRED_KINDS
    assert "Охотничьи ножи" not in sport_v2_all_kinds()
    assert "Эхолоты" in sport_v2_all_kinds()
    assert sport_v2_kind_class("Эхолоты") == "FISHING_GOOD"
    assert sport_v2_kind_class("Синтезаторы") == "MUSIC_INSTRUMENT"
    assert sport_v2_kind_class("Гитары") == "MUSIC_INSTRUMENT"
    assert SPORT_SELLER_OPTIONS == GOODS_SELLER_CHOICES
    assert "Компания" not in SPORT_SELLER_OPTIONS
    assert "Мастерская" not in SPORT_SELLER_OPTIONS
    kinds = sport_v2_all_kinds()
    assert len(kinds) == len(set(kinds))
    assert SPORT_V2_BANNED_KINDS.isdisjoint(set(kinds))
    matrix = sport_v2_condition_matrix()
    assert matrix["YES"] + matrix["NO"] == len(kinds)
    assert matrix["YES"] == 85
    assert matrix["NO"] == 11
    for slug in SPORT_V2_RETIRED_NATIONAL_CRAFT_SLUGS:
        assert slug not in SPORT_V2_CANONICAL_SLUGS
    target = sport_v2_package_a_field_target()
    for forbidden in (
        "size",
        "brand",
        "model",
        "material",
        "color",
        "weight",
        "length",
        "price_basis",
        "gender",
        "age",
        "level",
    ):
        assert forbidden in target["forbidden"]
    assert target["price_basis"] == "ABSENT"
    assert target["size"] == "ABSENT_DESCRIPTION"


def sport_v2_package_a_field_target() -> dict[str, Any]:
    return {
        "kind": SPORT_KIND_KEY,
        "kind_label": SPORT_KIND_LABEL,
        "seller": SPORT_SELLER_KEY,
        "seller_options": list(SPORT_SELLER_OPTIONS),
        "condition": SPORT_CONDITION_KEY,
        "condition_scope": "POSITIVE_ALLOWLIST_DEFAULT_OFF",
        "condition_options": list(SPORT_CONDITION_OPTIONS),
        "price": "price",
        "price_ui": "PriceDialog",
        "price_basis": "ABSENT",
        "negotiable": "CANONICAL",
        "contact_methods": "CANONICAL_SIX",
        "size": "ABSENT_DESCRIPTION",
        "brand": "ABSENT_DESCRIPTION",
        "model": "ABSENT_DESCRIPTION",
        "material": "ABSENT_DESCRIPTION",
        "color": "ABSENT_DESCRIPTION",
        "tech_specs": "ABSENT_DESCRIPTION",
        "ai_characteristic_rule": SPORT_AI_CHARACTERISTIC_RULE,
        "forbidden": sorted(SPORT_CREATE_FORBIDDEN),
        "required": (SPORT_KIND_KEY, SPORT_SELLER_KEY, "price", "contact_methods"),
        "optional": (SPORT_CONDITION_KEY, "negotiable"),
        "search_future": SPORT_V2_SEARCH_FUTURE,
        "search_exclude": sorted(SPORT_V2_SEARCH_EXCLUDE),
    }


def sport_v2_assert_package_a_contracts() -> None:
    sport_v2_assert_cleanup_contracts()
    if SPORT_KIND_KEY != "sport_kind":
        raise RuntimeError("sport_kind key lock broken")
    if SPORT_KIND_LABEL != "Товар":
        raise RuntimeError("Sport kind label must be Товар")
    if SPORT_SELLER_OPTIONS != GOODS_SELLER_CHOICES:
        raise RuntimeError("Sport seller must match shared goods")
    if GOODS_NEGOTIABLE_CHOICES != ("Есть торг", "Без торга"):
        raise RuntimeError("negotiable contract drifted")
    if len(CONTACT_METHOD_CHOICES) != 6:
        raise RuntimeError("contact_methods must stay six-option")
    if sport_v2_kind_count() != 96:
        raise RuntimeError(
            f"Sport Package A expects 96 kinds, got {sport_v2_kind_count()}"
        )
    matrix = sport_v2_condition_matrix()
    if matrix != {"YES": 85, "NO": 11}:
        raise RuntimeError(f"Sport Condition matrix lock broken: {matrix}")
    yes = sport_v2_condition_yes_kinds()
    if not yes <= set(sport_v2_all_kinds()):
        raise RuntimeError("Condition YES kinds missing from catalog")
    # Approved NO samples must stay NO.
    for kind in (
        "Протеин",
        "Гейнеры",
        "Креатин",
        "Аминокислоты",
        "Изотоники",
        "Спортивные батончики",
        "Другое спортивное питание",
        "Блёсны и приманки",
        "Бисер",
        "Валяние",
        "Мыловарение",
    ):
        if sport_v2_condition_decision(kind) != "NO":
            raise RuntimeError(f"Condition NO lock broken for {kind}")
    if "size" not in SPORT_CREATE_FORBIDDEN:
        raise RuntimeError("size must stay forbidden")
    if "price_basis" not in SPORT_CREATE_FORBIDDEN:
        raise RuntimeError("price_basis must stay forbidden")


def build_sport_v2_core_fields() -> dict[str, list]:
    """Create cores for all 13 active Sport L2 (Package A SoT)."""
    sport_v2_assert_package_a_contracts()
    cond_approved = sport_v2_condition_yes_kinds()
    out: dict[str, list] = {}

    for section_key, kinds in SPORT_V2_SECTION_KINDS.items():
        slug, _label = SPORT_V2_SECTION_META[section_key]
        fields: list = [
            _dep_field(
                SPORT_KIND_KEY,
                SPORT_KIND_LABEL,
                CategoryFieldType.enum,
                True,
                10,
                _choices(*kinds),
                hint="Какой товар?",
            ),
            _dep_field(
                SPORT_SELLER_KEY,
                SPORT_SELLER_LABEL,
                CategoryFieldType.enum,
                True,
                20,
                _choices(*SPORT_SELLER_OPTIONS),
            ),
        ]

        cond_kinds = [k for k in kinds if k in cond_approved]
        if cond_kinds:
            cond_opts: dict[str, Any] = _choices(*SPORT_CONDITION_OPTIONS)
            if set(cond_kinds) != set(kinds):
                cond_opts["depends_on"] = {
                    "field": SPORT_KIND_KEY,
                    "values": list(cond_kinds),
                }
            fields.append(
                _dep_field(
                    SPORT_CONDITION_KEY,
                    SPORT_CONDITION_LABEL,
                    CategoryFieldType.enum,
                    False,
                    30,
                    cond_opts,
                )
            )

        fields.extend(
            [
                _dep_field(
                    "price",
                    "Цена",
                    CategoryFieldType.price,
                    True,
                    40,
                    None,
                    hint="Цена (СОМ / KGS)",
                ),
                _dep_field(
                    "negotiable",
                    "Торг",
                    CategoryFieldType.enum,
                    False,
                    50,
                    _choices(*GOODS_NEGOTIABLE_CHOICES),
                ),
                _dep_field(
                    "contact_methods",
                    "Способы связи",
                    CategoryFieldType.enum,
                    True,
                    60,
                    _choices(*CONTACT_METHOD_CHOICES),
                ),
            ]
        )

        for row in fields:
            key = row[0]
            if key in SPORT_CREATE_FORBIDDEN:
                raise RuntimeError(f"forbidden Create field {slug}.{key}")
            if key not in _ALWAYS_CREATE:
                raise RuntimeError(f"unapproved Create field {slug}.{key}")
            opts = row[5]
            if opts and opts.get("choices") is not None and len(opts["choices"]) == 0:
                raise RuntimeError(f"empty picker {slug}.{key}")

        out[slug] = fields
    return out


def sport_v2_all_kind_audit() -> list[dict[str, Any]]:
    """All-96 kind audit rows (Package A)."""
    cores = build_sport_v2_core_fields()
    rows: list[dict[str, Any]] = []
    for section_key, kinds in SPORT_V2_SECTION_KINDS.items():
        slug, label = SPORT_V2_SECTION_META[section_key]
        fields = cores[slug]
        keys = [r[0] for r in fields]
        kind_row = next(r for r in fields if r[0] == SPORT_KIND_KEY)
        kind_opts = [c["value"] for c in kind_row[5]["choices"]]
        seller_row = next(r for r in fields if r[0] == SPORT_SELLER_KEY)
        seller_opts = [c["value"] for c in seller_row[5]["choices"]]
        cond_row = next((r for r in fields if r[0] == SPORT_CONDITION_KEY), None)
        cond_values = (
            set((cond_row[5].get("depends_on") or {}).get("values") or kind_opts)
            if cond_row is not None
            else set()
        )
        if cond_row is not None and "depends_on" not in (cond_row[5] or {}):
            cond_values = set(kind_opts)
        specials = [
            k
            for k in keys
            if k
            not in {
                SPORT_KIND_KEY,
                SPORT_SELLER_KEY,
                "price",
                "negotiable",
                "contact_methods",
            }
        ]
        for kind in kinds:
            cond = sport_v2_condition_decision(kind)
            rows.append(
                {
                    "kind": kind,
                    "section_key": section_key,
                    "l2_slug": slug,
                    "l2_label": label,
                    "ownership": sport_v2_kind_class(kind),
                    "kind_valid": kind in kind_opts,
                    "condition": cond,
                    "condition_in_schema": (kind in cond_values) == (cond == "YES"),
                    "seller": seller_opts,
                    "price": "price" in keys,
                    "size": "NO",
                    "brand": "NO",
                    "tech": "NO",
                    "special_count": len(specials) if cond == "YES" else 0,
                    "forbidden": sorted(set(keys) & SPORT_CREATE_FORBIDDEN),
                    "components": {
                        SPORT_KIND_KEY: "enum",
                        SPORT_SELLER_KEY: "enum",
                        "price": "price",
                        "negotiable": "enum",
                        "contact_methods": "enum",
                        **(
                            {SPORT_CONDITION_KEY: "enum"}
                            if cond == "YES"
                            else {}
                        ),
                    },
                    "retired_resurrected": False,
                    "weapons": False,
                    "platform_owner": "SPORT_HOBBY",
                }
            )
    return rows


def sport_v2_complexity_histogram() -> dict[str, int]:
    hist = {"0": 0, "1": 0, "2": 0, "3+": 0}
    for row in sport_v2_all_kind_audit():
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


def sport_v2_echo_sounder_ownership() -> dict[str, str]:
    return {
        "kind": "Эхолоты",
        "owner": "SPORT_FISHING",
        "slug": "sports-hobby-ohota-i-rybalka",
        "rule": "Marketplace intent = fishing equipment; not general Electronics.",
    }


def sport_v2_hg_overlap_matrix() -> list[dict[str, str]]:
    return [
        {
            "item": "Туристические термосы (camping)",
            "owner": "SPORT",
            "note": "Camping-specific outdoor gear stays Sport.",
        },
        {
            "item": "Household thermos (HG kitchen)",
            "owner": "HOME_GARDEN",
            "note": "Kitchen housewares remain HG.",
        },
        {
            "item": "Мангалы / household grill",
            "owner": "HOME_GARDEN",
            "note": "Not Sport camping.",
        },
        {
            "item": "Палатки / спальники",
            "owner": "SPORT",
            "note": "Genuine camping goods.",
        },
    ]


def _search_filter(
    key: str,
    label: str,
    ftype: CategoryFilterType,
    sort: int,
    config: dict[str, Any] | None,
) -> tuple:
    return (key, label, ftype, sort, config)


def build_sport_v2_search_filters() -> dict[str, list]:
    """Package B Search SoT per canonical Sport L2.

    Allowlist: sport_kind + seller_type + condition (Package A semantic matrix).
    Price / negotiable / contacts / size / brand / tech never Search.
    Geo is shared Search UX, not CategoryFilter rows.
    """
    cores = build_sport_v2_core_fields()
    out: dict[str, list] = {}
    for slug, fields in cores.items():
        filters: list = []
        for key, label, _ftype, _required, sort, options, _hint in fields:
            if key not in SPORT_V2_SEARCH_EAV_KEYS:
                continue
            if key in SPORT_V2_SEARCH_EXCLUDE:
                continue
            if key not in SPORT_V2_SEARCH_ALLOWLIST:
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
    if set(out) != SPORT_V2_CANONICAL_SLUGS:
        raise RuntimeError(
            "Sport Search filter map != canonical L2 slugs: "
            f"extra={sorted(set(out) - SPORT_V2_CANONICAL_SLUGS)} "
            f"missing={sorted(SPORT_V2_CANONICAL_SLUGS - set(out))}"
        )
    return out


def sport_v2_search_kind_audit_row(
    section_key: str, slug: str, kind: str
) -> dict[str, Any]:
    cond = sport_v2_condition_decision(kind)
    visible = [SPORT_KIND_KEY, SPORT_SELLER_KEY]
    if cond == "YES":
        visible.append(SPORT_CONDITION_KEY)
    return {
        "l2": slug,
        "section": section_key,
        "kind": kind,
        "ownership": sport_v2_kind_class(kind),
        "search_sport_kind": "YES",
        "search_seller": "YES",
        "search_condition": cond,
        "search_size": "NO",
        "search_brand": "NO",
        "search_model": "NO",
        "search_tech": "NO",
        "search_price": "NO",
        "search_negotiable": "NO",
        "search_contacts": "NO",
        "search_price_basis": "NO",
        "search_rental": "NO",
        "search_ticket": "NO",
        "search_geo": "YES",
        "retired_resurrected": slug in SPORT_V2_RETIRED_SLUGS,
        "platform_owner": "SPORT_HOBBY",
        "visible_search_keys": visible,
        "ui_components": {
            SPORT_KIND_KEY: "multi_select",
            SPORT_SELLER_KEY: "multi_select",
            **({SPORT_CONDITION_KEY: "multi_select"} if cond == "YES" else {}),
            "geo": "region_city",
        },
    }


def sport_v2_all_search_kind_audit() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for section_key, kinds in SPORT_V2_SECTION_KINDS.items():
        slug, _label = SPORT_V2_SECTION_META[section_key]
        for kind in kinds:
            rows.append(sport_v2_search_kind_audit_row(section_key, slug, kind))
    return rows


def sport_v2_assert_package_b_contracts() -> None:
    sport_v2_assert_package_a_contracts()
    if SPORT_V2_SEARCH_POLICY != "SIMPLE":
        raise RuntimeError("Sport Search policy must stay SIMPLE")
    if SPORT_KIND_KEY not in SPORT_V2_SEARCH_EAV_KEYS:
        raise RuntimeError("sport_kind must stay Search EAV")
    if SPORT_SELLER_KEY not in SPORT_V2_SEARCH_EAV_KEYS:
        raise RuntimeError("seller_type must stay Search EAV")
    if "geo" not in SPORT_V2_SEARCH_ALLOWLIST:
        raise RuntimeError("geo must remain on Search allowlist")
    if "price" in SPORT_V2_SEARCH_EAV_KEYS:
        raise RuntimeError("price must not be Search EAV")
    if "size" in SPORT_V2_SEARCH_ALLOWLIST:
        raise RuntimeError("size must not be Search")
    filters = build_sport_v2_search_filters()
    if set(filters) != SPORT_V2_CANONICAL_SLUGS:
        raise RuntimeError("Package B Search map ≠ canonical L2")
    if set(filters) & SPORT_V2_RETIRED_SLUGS:
        raise RuntimeError("Retired Sport slugs must not appear in Search")
    for slug, rows in filters.items():
        keys = {r[0] for r in rows}
        if keys & SPORT_CREATE_FORBIDDEN:
            raise RuntimeError(f"Forbidden Search keys: {slug}")
        if keys & {"price", "negotiable", "contact_methods", "size", "brand"}:
            raise RuntimeError(f"Create-only leaked into Search: {slug}")
        if SPORT_KIND_KEY not in keys or SPORT_SELLER_KEY not in keys:
            raise RuntimeError(f"Search missing kind/seller: {slug}")
        if not rows:
            raise RuntimeError(f"Empty Search filters: {slug}")
        cores = {r[0] for r in build_sport_v2_core_fields()[slug]}
        if SPORT_CONDITION_KEY in cores:
            assert SPORT_CONDITION_KEY in keys, slug
        else:
            assert SPORT_CONDITION_KEY not in keys, slug
        for _key, _label, _ftype, _sort, cfg in rows:
            if cfg and cfg.get("choices") is not None and len(cfg["choices"]) == 0:
                raise RuntimeError(f"Empty Search picker: {slug}.{_key}")
    audit = sport_v2_all_search_kind_audit()
    if len(audit) != 96:
        raise RuntimeError(f"Search audit expects 96, got {len(audit)}")
    yes = sum(1 for r in audit if r["search_condition"] == "YES")
    no = sum(1 for r in audit if r["search_condition"] == "NO")
    if yes != 85 or no != 11:
        raise RuntimeError(f"Search Condition matrix drifted: YES={yes} NO={no}")
    if any(r["search_size"] != "NO" for r in audit):
        raise RuntimeError("Size leaked into Search audit")
    if "Охотничьи ножи" in {r["kind"] for r in audit}:
        raise RuntimeError("Hunting knives leaked into Search")
