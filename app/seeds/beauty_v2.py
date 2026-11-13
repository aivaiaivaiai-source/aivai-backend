# -*- coding: utf-8 -*-
"""Beauty & Personal Care V2 — taxonomy + Package A Create SoT.

Package A Create cores via `build_beauty_v2_core_fields` (16 L2).
Package B Search filters are NOT seeded here.
Brand/model/volume/SKU cascades removed from V2 target (Description sink).
package_state removed — consumables have no opened/used structured state.
"""
from __future__ import annotations

from typing import Any, Literal

from app.models.category_enums import CategoryFieldType, CategoryFilterType
from app.seeds.shared_goods_create_contract import (
    CONTACT_METHOD_CHOICES,
    GOODS_NEGOTIABLE_CHOICES,
    GOODS_SELLER_CHOICES,
)

BEAUTY_ROOT_SLUG = "beauty"
BEAUTY_ROOT_LABEL = "Красота и личный уход"

BEAUTY_V2_LEGACY_L2_SLUGS = frozenset(
    {
        "beauty-cosmetics",
        "beauty-hair",
    }
)
BEAUTY_V2_RETIRED_SLUGS = BEAUTY_V2_LEGACY_L2_SLUGS

# Medical V2 supplements stay retired elsewhere — never absorb into Beauty.
BEAUTY_V2_SUPPLEMENTS_STATUS = "RETIRED_NO_CANONICAL_DESTINATION"

KindClass = Literal[
    "BEAUTY_GOOD",
    "PERSONAL_CARE_GOOD",
    "HYGIENE_GOOD",
    "DURABLE_BEAUTY_DEVICE",
    "CONSUMABLE",
    "PRO_CONSUMABLE",
    "PRO_TOOL",
    "WIG_BEAUTY",
]

BEAUTY_SELLER_OPTIONS = GOODS_SELLER_CHOICES
BEAUTY_CONDITION_OPTIONS = ("Новое", "Б/у")
BEAUTY_KIND_KEY = "beauty_kind"
BEAUTY_KIND_LABEL = "Товар"
BEAUTY_SELLER_KEY = "seller_type"
BEAUTY_SELLER_LABEL = "Продавец"
BEAUTY_CONDITION_KEY = "condition"
BEAUTY_CONDITION_LABEL = "Состояние"

BEAUTY_AI_CHARACTERISTIC_RULE = (
    "AI must not invent brand, model, volume, shade, ingredients, expiry, "
    "skin type, hair type, SPF, finish, gender, oxidizer percent, power source, "
    "curl, size, authenticity/originality, package_state, or condition unless "
    "explicitly supplied by the user and permitted by the Backend schema."
)

BEAUTY_AI_MEDICAL_CLAIM_RULE = (
    "AI must not invent or strengthen therapeutic/medical claims for Beauty goods "
    "(e.g. лечит, лечебный, устраняет заболевание, гарантирует медицинский результат, "
    "лечит акне/дерматит/выпадение волос, dermatologically proven medical effect) "
    "unless exact user-provided factual text is allowed by existing platform policy. "
    "Structured fill must never manufacture medical claims."
)

BEAUTY_AI_MEDICAL_CLAIM_FORBIDDEN_PATTERNS: frozenset[str] = frozenset(
    {
        "лечит",
        "лечебный",
        "лечебная",
        "лечебное",
        "устраняет заболевание",
        "гарантирует медицинский результат",
        "лечит акне",
        "лечит дерматит",
        "лечит выпадение волос",
        "dermatologically proven",
    }
)

BEAUTY_CREATE_FORBIDDEN: frozenset[str] = frozenset(
    {
        "beauty_brand",
        "beauty_model",
        "brand",
        "model",
        "volume",
        "spf",
        "skin_type",
        "hair_type",
        "finish",
        "gender",
        "oxidizer_percent",
        "power_source",
        "curl",
        "size",
        "shade",
        "color",
        "ingredients",
        "expiry",
        "package_state",
        "price_basis",
        "authenticity",
        "original",
        "replica",
        "Салон",
        "Мастер",
        "Косметолог",
        "Аптека",
        "Компания",
    }
)

BEAUTY_V2_SEARCH_POLICY = "SIMPLE"

# Package B Search — explicit allowlist (Create ≠ Search).
# Geo is shared Search UX (region/city), not CategoryFilter rows.
BEAUTY_V2_SEARCH_ALLOWLIST: frozenset[str] = frozenset(
    {
        BEAUTY_KIND_KEY,
        BEAUTY_CONDITION_KEY,
        BEAUTY_SELLER_KEY,
        "geo",
    }
)

BEAUTY_V2_SEARCH_EAV_KEYS: frozenset[str] = frozenset(
    {
        BEAUTY_KIND_KEY,
        BEAUTY_CONDITION_KEY,
        BEAUTY_SELLER_KEY,
    }
)

BEAUTY_V2_SEARCH_EXCLUDE: frozenset[str] = frozenset(
    set(BEAUTY_CREATE_FORBIDDEN)
    | {
        "price",
        "negotiable",
        "contact_methods",
        "price_basis",
        "currency",
        "package_state",
        "beauty_brand",
        "beauty_model",
        "volume",
        "shade",
        "spf",
        "skin_type",
        "hair_type",
        "finish",
        "gender",
        "size",
        "ingredients",
        "expiry",
        "authenticity",
    }
)

BEAUTY_V2_SEARCH_FUTURE = (
    BEAUTY_KIND_KEY,
    BEAUTY_CONDITION_KEY,
    BEAUTY_SELLER_KEY,
    "geo",
)

# Search/Package B blockers (documented; not fixed in this cleanup).
BEAUTY_V2_SEARCH_BLOCKERS: frozenset[str] = frozenset(
    {
        "JobVacancyFilterPanel",
        "fake_count_55443",
        "no_backend_category_filters",
    }
)

BEAUTY_V2_CANONICAL_LEAVES: tuple[tuple[str, str, int], ...] = (
    ("Косметика", "beauty-kosmetika", 10),
    ("Парфюмерия", "beauty-parfyumeriya", 20),
    ("Уход за волосами", "beauty-uhod-za-volosami", 30),
    ("Уход за лицом", "beauty-uhod-za-litsom", 40),
    ("Уход за телом", "beauty-uhod-za-telom", 50),
    ("Мужской уход и бритьё", "beauty-muzhskoy-uhod-i-brite", 60),
    ("Товары для маникюра и педикюра", "beauty-manikyur-i-pedikyur", 70),
    ("Брови, ресницы и губы", "beauty-brovi-resnitsy-i-guby", 80),
    ("Депиляция и эпиляция", "beauty-depilyatsiya-i-epilyatsiya", 90),
    ("Профессиональная косметика", "beauty-professionalnaya-kosmetika", 100),
    (
        "Инструменты/оборуд.е для красоты",
        "beauty-instrumenty-oborud-e-dlya-krasoty",
        110,
    ),
    (
        "Расходные материалы для салонов",
        "beauty-rashodnye-materialy-dlya-salonov",
        120,
    ),
    ("Средства гигиены", "beauty-sredstva-gigieny", 130),
    ("Товары для барбершопов", "beauty-tovary-dlya-barbershopov", 140),
    ("Товары для тату", "beauty-tovary-dlya-tatu-i-pirsinga", 150),
    ("Прочее для красоты и ухода", "beauty-prochee-dlya-krasoty-i-uhoda", 160),
)

BEAUTY_V2_CANONICAL_SLUGS = frozenset(slug for _, slug, _ in BEAUTY_V2_CANONICAL_LEAVES)
BEAUTY_V2_EXPECTED_L2_COUNT = len(BEAUTY_V2_CANONICAL_LEAVES)

BEAUTY_V2_SECTION_META: dict[str, tuple[str, str]] = {
    "cosmetics": ("beauty-kosmetika", "Косметика"),
    "perfume": ("beauty-parfyumeriya", "Парфюмерия"),
    "hair": ("beauty-uhod-za-volosami", "Уход за волосами"),
    "face": ("beauty-uhod-za-litsom", "Уход за лицом"),
    "body": ("beauty-uhod-za-telom", "Уход за телом"),
    "men": ("beauty-muzhskoy-uhod-i-brite", "Мужской уход и бритьё"),
    "nails": ("beauty-manikyur-i-pedikyur", "Товары для маникюра и педикюра"),
    "brows": ("beauty-brovi-resnitsy-i-guby", "Брови, ресницы и губы"),
    "depilation": ("beauty-depilyatsiya-i-epilyatsiya", "Депиляция и эпиляция"),
    "pro": ("beauty-professionalnaya-kosmetika", "Профессиональная косметика"),
    "tools": (
        "beauty-instrumenty-oborud-e-dlya-krasoty",
        "Инструменты/оборуд.е для красоты",
    ),
    "salon-supplies": (
        "beauty-rashodnye-materialy-dlya-salonov",
        "Расходные материалы для салонов",
    ),
    "hygiene": ("beauty-sredstva-gigieny", "Средства гигиены"),
    "barber": ("beauty-tovary-dlya-barbershopov", "Товары для барбершопов"),
    "tattoo": ("beauty-tovary-dlya-tatu-i-pirsinga", "Товары для тату"),
    "other": ("beauty-prochee-dlya-krasoty-i-uhoda", "Прочее для красоты и ухода"),
}

BEAUTY_V2_SECTION_KINDS: dict[str, tuple[str, ...]] = {
    "cosmetics": (
        "Тональные средства",
        "Консилеры",
        "Пудра",
        "Тушь",
        "Тени",
        "Помады",
        "Румяна",
        "Другая косметика",
    ),
    "perfume": (
        "Духи",
        "Парфюмерная вода",
        "Туалетная вода",
        "Одеколон",
        "Парфюмерные наборы",
        "Другая парфюмерия",
    ),
    "hair": (
        "Шампуни",
        "Бальзамы и маски",
        "Краски для волос",
        "Средства для укладки",
        "Масла для волос",
        "Другие средства для волос",
    ),
    "face": (
        "Кремы для лица",
        "Сыворотки",
        "Тоники и мицеллярная вода",
        "Маски для лица",
        "Солнцезащита",
        "Средства для умывания",
        "Другой уход за лицом",
    ),
    "body": (
        "Кремы и лосьоны для тела",
        "Гели для душа",
        "Скрабы для тела",
        "Кремы для рук и ног",
        "Масла для тела",
        "Другой уход за телом",
    ),
    "men": (
        "Станки для бритья",
        "Кассеты и лезвия",
        "Пены и гели для бритья",
        "Средства после бритья",
        "Масла и бальзамы для бороды",
        "Другой мужской уход",
    ),
    "nails": (
        "Гель-лаки",
        "Лаки для ногтей",
        "Базы и топы",
        "Жидкости для снятия",
        "Дизайн ногтей",
        "Другие товары для маникюра",
    ),
    "brows": (
        "Краски и хна для бровей",
        "Гели для бровей",
        "Ресницы для наращивания",
        "Клей для ресниц",
        "Наборы для ламинирования",
        "Бальзамы для губ",
        "Другие товары для бровей и ресниц",
    ),
    "depilation": (
        "Воск для депиляции",
        "Сахарная паста",
        "Полоски для депиляции",
        "Кремы для депиляции",
        "Другие средства для депиляции",
    ),
    "pro": (
        "Профессиональные краски",
        "Окислители",
        "Профессиональные шампуни",
        "Профессиональные маски",
        "Косметика для косметологов",
        "Другая профессиональная косметика",
    ),
    "tools": (
        "Фены",
        "Плойки и выпрямители",
        "Домашние машинки для стрижки",
        "Электробритвы",
        "Эпиляторы",
        "Лампы для маникюра",
        "Аппараты для маникюра",
        "Воскоплавы",
        "Другие персональные устройства для красоты",
    ),
    "salon-supplies": (
        "Одноразовые простыни",
        "Одноразовые пеньюары",
        "Воротнички",
        "Шпатели",
        "Бахилы",
        "Безворсовые салфетки",
        "Другие расходники для салонов",
    ),
    "hygiene": (
        "Зубные пасты",
        "Зубные щётки",
        "Мыло",
        "Дезодоранты",
        "Женская гигиена",
        "Средства интимной гигиены",
        "Другие средства гигиены",
    ),
    "barber": (
        "Машинки для барберов",
        "Ножницы для барберов",
        "Опасные бритвы",
        "Пеньюары для барберов",
        "Средства для барбершопа",
        "Другие товары для барбершопов",
    ),
    "tattoo": (
        "Машинки для тату",
        "Картриджи и иглы",
        "Краски для тату",
        "Другие товары для тату",
    ),
    "other": (
        "Парики и шиньоны",
        "Косметические зеркала",
        "Другие товары для красоты",
    ),
}

# Moved out of Beauty — Fashion ownership (exact leaf/kind may be GAP).
BEAUTY_V2_MOVED_TO_FASHION: dict[str, dict[str, str]] = {
    "Косметички": {
        "owner": "FASHION",
        "preferred_slug": "fashion-sumki-i-chemodany",
        "preferred_section": "Сумки и чемоданы",
        "exact_kind": "GAP",
        "nearest_kind": "Другие сумки",
        "note": "Removed from Beauty; no exact Fashion kind — GAP documented.",
    },
    "Украшения для пирсинга": {
        "owner": "FASHION",
        "preferred_slug": "fashion-ukrasheniya-i-bizhuteriya",
        "preferred_section": "Украшения и бижутерия",
        "exact_kind": "GAP",
        "nearest_kind": "Другие украшения",
        "note": "Removed from Beauty; no exact Fashion piercing kind — GAP documented.",
    },
}

BEAUTY_V2_RETIRED_KINDS: dict[str, tuple[str, str]] = {
    "Косметички": (
        "MOVED_FASHION_GAP",
        "Fashion owns cosmetic bags; exact Fashion kind absent (GAP).",
    ),
    "Украшения для пирсинга": (
        "MOVED_FASHION_GAP",
        "Fashion owns piercing jewelry; exact Fashion kind absent (GAP).",
    ),
    "Другое оборудование для красоты": (
        "RENAMED_NARROWED",
        "Catch-all narrowed to personal devices only.",
    ),
}

BEAUTY_V2_BANNED_KINDS = frozenset(
    {
        # Services procedures
        "Парикмахерские услуги",
        "Маникюр и педикюр",  # Services identity — Beauty L2 goods label is different
        "Брови и ресницы",
        "Косметология",
        "Депиляция",
        "Массаж",
        "Макияж",
        "Тату и пирсинг",
        "Стрижка",
        "Окрашивание",
        "Визаж",
        "SPA",
        # Kids
        "Подгузники",
        "Влажные салфетки",
        "Детские маникюрные наборы",
        "Крем и присыпка",
        # Medical / supplements
        "БАДы и товары для здоровья",
        "Другие БАДы",
        "Лекарства",
        # BE commercial installations
        "Парикмахерские кресла",
        "Мойки для салонов",
        "Педикюрные кресла",
        "Маникюрные столы",
        "Косметологические кушетки",
        "Сушуары",
        "Вапоризаторы",
        "Стерилизаторы",
        "Аппараты лазерной эпиляции",
        "Аппараты для перманентного макияжа",
        "Кресло барбера",
        # Fashion-moved / unrestricted catch-all
        "Косметички",
        "Украшения для пирсинга",
        "Другое оборудование для красоты",
    }
)

# Durable reusable allowlist — Condition YES. Default for all other kinds = NO.
_CONDITION_YES = frozenset(
    {
        "Фены",
        "Плойки и выпрямители",
        "Домашние машинки для стрижки",
        "Электробритвы",
        "Эпиляторы",
        "Лампы для маникюра",
        "Аппараты для маникюра",
        "Воскоплавы",
        "Другие персональные устройства для красоты",
        "Машинки для барберов",
        "Ножницы для барберов",
        "Опасные бритвы",
        "Другие товары для барбершопов",
        "Машинки для тату",
        "Другие товары для тату",
        "Парики и шиньоны",
        "Косметические зеркала",
        "Другие товары для красоты",
    }
)

_KIND_CLASS: dict[str, KindClass] = {}


def _register_classes() -> None:
    for k in BEAUTY_V2_SECTION_KINDS["cosmetics"]:
        _KIND_CLASS[k] = "BEAUTY_GOOD"
    for k in BEAUTY_V2_SECTION_KINDS["perfume"]:
        _KIND_CLASS[k] = "BEAUTY_GOOD"
    for section in ("hair", "face", "body", "men", "nails", "brows", "depilation"):
        for k in BEAUTY_V2_SECTION_KINDS[section]:
            _KIND_CLASS[k] = "PERSONAL_CARE_GOOD"
    for k in BEAUTY_V2_SECTION_KINDS["pro"]:
        _KIND_CLASS[k] = "PRO_CONSUMABLE"
    for k in BEAUTY_V2_SECTION_KINDS["tools"]:
        _KIND_CLASS[k] = "DURABLE_BEAUTY_DEVICE"
    for k in BEAUTY_V2_SECTION_KINDS["salon-supplies"]:
        _KIND_CLASS[k] = "PRO_CONSUMABLE"
    for k in BEAUTY_V2_SECTION_KINDS["hygiene"]:
        _KIND_CLASS[k] = "HYGIENE_GOOD"
    for k in (
        "Машинки для барберов",
        "Ножницы для барберов",
        "Опасные бритвы",
        "Другие товары для барбершопов",
    ):
        _KIND_CLASS[k] = "PRO_TOOL"
    for k in ("Пеньюары для барберов", "Средства для барбершопа"):
        _KIND_CLASS[k] = "PRO_CONSUMABLE"
    _KIND_CLASS["Машинки для тату"] = "PRO_TOOL"
    _KIND_CLASS["Другие товары для тату"] = "PRO_TOOL"
    for k in ("Картриджи и иглы", "Краски для тату"):
        _KIND_CLASS[k] = "PRO_CONSUMABLE"
    _KIND_CLASS["Парики и шиньоны"] = "WIG_BEAUTY"
    _KIND_CLASS["Косметические зеркала"] = "DURABLE_BEAUTY_DEVICE"
    _KIND_CLASS["Другие товары для красоты"] = "BEAUTY_GOOD"


_register_classes()


def _item(label: str) -> dict[str, Any]:
    return {"value": label, "label": label}


def _opts(*labels: str) -> list[dict[str, Any]]:
    return [_item(label) for label in labels]


def _seller() -> dict[str, Any]:
    return {
        "label": BEAUTY_SELLER_LABEL,
        "options": _opts(*BEAUTY_SELLER_OPTIONS),
    }


def _condition(applies_to: tuple[str, ...] | None = None) -> dict[str, Any]:
    group: dict[str, Any] = {
        "label": BEAUTY_CONDITION_LABEL,
        "options": _opts(*BEAUTY_CONDITION_OPTIONS),
    }
    if applies_to is not None:
        group["applies_to"] = list(applies_to)
    return group


def beauty_v2_all_kinds() -> tuple[str, ...]:
    out: list[str] = []
    for kinds in BEAUTY_V2_SECTION_KINDS.values():
        out.extend(kinds)
    return tuple(out)


def beauty_v2_kind_count() -> int:
    return len(beauty_v2_all_kinds())


def beauty_v2_kind_class(kind: str) -> KindClass:
    if kind not in _KIND_CLASS:
        raise KeyError(f"unknown Beauty kind: {kind}")
    return _KIND_CLASS[kind]


def beauty_v2_condition_decision(kind: str) -> Literal["YES", "NO"]:
    if kind not in set(beauty_v2_all_kinds()):
        raise KeyError(f"unknown Beauty kind: {kind}")
    return "YES" if kind in _CONDITION_YES else "NO"


def beauty_v2_condition_yes_kinds() -> frozenset[str]:
    return frozenset(
        k for k in beauty_v2_all_kinds() if beauty_v2_condition_decision(k) == "YES"
    )


def beauty_v2_condition_matrix() -> dict[str, int]:
    yes = no = 0
    for kind in beauty_v2_all_kinds():
        if beauty_v2_condition_decision(kind) == "YES":
            yes += 1
        else:
            no += 1
    return {"YES": yes, "NO": no}


def beauty_v2_consumable_kinds() -> frozenset[str]:
    return frozenset(
        k for k in beauty_v2_all_kinds() if beauty_v2_condition_decision(k) == "NO"
    )


def beauty_v2_package_a_field_target() -> dict[str, Any]:
    return {
        "kind": BEAUTY_KIND_KEY,
        "kind_label": BEAUTY_KIND_LABEL,
        "condition": "SEMANTIC_ALLOWLIST_ONLY",
        "seller": list(BEAUTY_SELLER_OPTIONS),
        "price": "PRICE_DIALOG_KGS",
        "price_basis": "ABSENT",
        "negotiable": ("Есть торг", "Без торга"),
        "contact_methods": "CANONICAL_SIX",
        "package_state": "ABSENT",
        "brand": "ABSENT_DESCRIPTION",
        "model": "ABSENT_DESCRIPTION",
        "volume": "ABSENT_DESCRIPTION",
        "spf": "ABSENT_DESCRIPTION",
        "skin_type": "ABSENT_DESCRIPTION",
        "hair_type": "ABSENT_DESCRIPTION",
        "finish": "ABSENT_DESCRIPTION",
        "gender": "ABSENT_DESCRIPTION",
        "forbidden": sorted(BEAUTY_CREATE_FORBIDDEN),
        "ai_characteristic_rule": BEAUTY_AI_CHARACTERISTIC_RULE,
        "ai_medical_claim_rule": BEAUTY_AI_MEDICAL_CLAIM_RULE,
    }


def beauty_v2_device_ownership_matrix() -> list[dict[str, str]]:
    rows = [
        {"kind": "Фены", "owner": "BEAUTY", "vs": "Electronics=NO Medical=NO BE=NO"},
        {
            "kind": "Плойки и выпрямители",
            "owner": "BEAUTY",
            "vs": "Electronics=NO Medical=NO BE=NO",
        },
        {
            "kind": "Домашние машинки для стрижки",
            "owner": "BEAUTY",
            "vs": "Electronics=NO Medical=NO BE=NO",
        },
        {
            "kind": "Электробритвы",
            "owner": "BEAUTY",
            "vs": "Electronics=NO Medical=NO BE=NO",
        },
        {"kind": "Эпиляторы", "owner": "BEAUTY", "vs": "Electronics=NO Medical=NO BE=NO"},
        {
            "kind": "Лампы для маникюра",
            "owner": "BEAUTY",
            "vs": "Electronics=NO Medical=NO BE=commercial_furniture_NO",
        },
        {
            "kind": "Аппараты для маникюра",
            "owner": "BEAUTY",
            "vs": "personal/small tool; commercial install → BE",
        },
        {"kind": "Воскоплавы", "owner": "BEAUTY", "vs": "Electronics=NO BE=NO"},
        {
            "kind": "Другие персональные устройства для красоты",
            "owner": "BEAUTY",
            "vs": "personal/home only; commercial/medical forbidden",
        },
        {
            "kind": "Машинки для барберов",
            "owner": "BEAUTY",
            "vs": "handheld tool; furniture → BE",
        },
        {"kind": "Машинки для тату", "owner": "BEAUTY", "vs": "tool; service → Services"},
        {
            "kind": "Парикмахерские кресла",
            "owner": "BUSINESS_EQUIPMENT",
            "vs": "not Beauty",
        },
        {
            "kind": "Аппараты лазерной эпиляции",
            "owner": "BUSINESS_EQUIPMENT",
            "vs": "professional installation",
        },
        {
            "kind": "Стерилизаторы",
            "owner": "BUSINESS_EQUIPMENT_MEDICAL",
            "vs": "not Beauty",
        },
    ]
    return rows


def beauty_v2_other_equipment_decision() -> dict[str, str]:
    return {
        "old_kind": "Другое оборудование для красоты",
        "decision": "RENAME_NARROW",
        "new_kind": "Другие персональные устройства для красоты",
        "reason": (
            "Unrestricted equipment catch-all could absorb BE/Medical installations; "
            "narrowed to personal/home beauty devices only."
        ),
    }


def build_beauty_v2_sections() -> dict[str, dict[str, Any]]:
    """Offline/API section catalog (Flutter fallback mirror). No Package A cores."""
    out: dict[str, dict[str, Any]] = {}
    for key, kinds in BEAUTY_V2_SECTION_KINDS.items():
        slug, label = BEAUTY_V2_SECTION_META[key]
        yes_kinds = tuple(k for k in kinds if beauty_v2_condition_decision(k) == "YES")
        filters: list[dict[str, Any]] = [_seller()]
        if yes_kinds:
            if set(yes_kinds) == set(kinds):
                filters.append(_condition())
            else:
                filters.append(_condition(applies_to=yes_kinds))
        out[key] = {
            "category_slug": slug,
            "label": label,
            "question": "Какой товар?",
            "roles": _opts(*kinds),
            "filters": filters,
        }
    return out


def beauty_v2_assert_cleanup_contracts() -> None:
    assert BEAUTY_ROOT_SLUG == "beauty"
    assert BEAUTY_ROOT_LABEL == "Красота и личный уход"
    assert BEAUTY_V2_EXPECTED_L2_COUNT == 16
    assert len(BEAUTY_V2_CANONICAL_LEAVES) == 16
    assert set(BEAUTY_V2_SECTION_KINDS) == set(BEAUTY_V2_SECTION_META)
    assert BEAUTY_V2_CANONICAL_SLUGS.isdisjoint(BEAUTY_V2_RETIRED_SLUGS)
    assert BEAUTY_SELLER_OPTIONS == GOODS_SELLER_CHOICES
    for banned_seller in ("Салон", "Мастер", "Косметолог", "Аптека", "Компания"):
        assert banned_seller not in BEAUTY_SELLER_OPTIONS

    kinds = beauty_v2_all_kinds()
    assert len(kinds) == len(set(kinds))
    assert beauty_v2_kind_count() == 99
    assert BEAUTY_V2_BANNED_KINDS.isdisjoint(set(kinds))
    assert "Косметички" not in kinds
    assert "Украшения для пирсинга" not in kinds
    assert "Другое оборудование для красоты" not in kinds
    assert "Другие персональные устройства для красоты" in kinds
    assert "Парики и шиньоны" in kinds

    # Manicure goods label must not equal Services identity string as section label.
    nails_label = BEAUTY_V2_SECTION_META["nails"][1]
    assert nails_label == "Товары для маникюра и педикюра"
    assert nails_label != "Маникюр и педикюр"

    matrix = beauty_v2_condition_matrix()
    assert matrix["YES"] + matrix["NO"] == len(kinds)
    assert matrix["YES"] == 18
    assert matrix["NO"] == 81

    for kind in beauty_v2_consumable_kinds():
        assert beauty_v2_condition_decision(kind) == "NO"

    for kind in _CONDITION_YES:
        assert kind in set(kinds)
        assert beauty_v2_condition_decision(kind) == "YES"

    target = beauty_v2_package_a_field_target()
    assert target["package_state"] == "ABSENT"
    assert target["brand"] == "ABSENT_DESCRIPTION"
    assert target["price_basis"] == "ABSENT"
    for forbidden in (
        "beauty_brand",
        "beauty_model",
        "volume",
        "package_state",
        "spf",
        "price_basis",
    ):
        assert forbidden in target["forbidden"]

    assert BEAUTY_V2_SUPPLEMENTS_STATUS == "RETIRED_NO_CANONICAL_DESTINATION"
    assert "лечеб" in BEAUTY_AI_MEDICAL_CLAIM_RULE or "лечит" in BEAUTY_AI_MEDICAL_CLAIM_RULE
    assert "AI must not invent" in BEAUTY_AI_CHARACTERISTIC_RULE

    decision = beauty_v2_other_equipment_decision()
    assert decision["decision"] == "RENAME_NARROW"

    for moved in BEAUTY_V2_MOVED_TO_FASHION.values():
        assert moved["exact_kind"] == "GAP"

    # Structured SKU fields must not appear in section filters.
    for catalog in build_beauty_v2_sections().values():
        labels = [g["label"] for g in catalog["filters"]]
        assert "Продавец" in labels
        for banned in (
            "Марка",
            "Модель",
            "Упаковка",
            "Объём",
            "SPF",
            "Тип кожи",
            "Тип волос",
            "Финиш",
            "Пол",
            "Питание",
            "Изгиб",
            "Размер",
            "Процент",
        ):
            assert banned not in labels
        if "Состояние" in labels:
            cond = next(g for g in catalog["filters"] if g["label"] == "Состояние")
            assert [o["label"] for o in cond["options"]] == list(BEAUTY_CONDITION_OPTIONS)


_ALWAYS_CREATE: frozenset[str] = frozenset(
    {
        BEAUTY_KIND_KEY,
        BEAUTY_SELLER_KEY,
        BEAUTY_CONDITION_KEY,
        "price",
        "negotiable",
        "contact_methods",
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
    hint: str | None = None,
) -> tuple:
    return (key, label, ftype, required, sort, options, hint)


def beauty_v2_assert_package_a_contracts() -> None:
    beauty_v2_assert_cleanup_contracts()
    if BEAUTY_KIND_KEY != "beauty_kind":
        raise RuntimeError("beauty_kind key lock broken")
    if BEAUTY_KIND_LABEL != "Товар":
        raise RuntimeError("Beauty kind label must be Товар")
    if BEAUTY_SELLER_OPTIONS != GOODS_SELLER_CHOICES:
        raise RuntimeError("Beauty seller must match shared goods")
    if GOODS_NEGOTIABLE_CHOICES != ("Есть торг", "Без торга"):
        raise RuntimeError("negotiable contract drifted")
    if len(CONTACT_METHOD_CHOICES) != 6:
        raise RuntimeError("contact_methods must stay six-option")
    if beauty_v2_kind_count() != 99:
        raise RuntimeError(
            f"Beauty Package A expects 99 kinds, got {beauty_v2_kind_count()}"
        )
    matrix = beauty_v2_condition_matrix()
    if matrix != {"YES": 18, "NO": 81}:
        raise RuntimeError(f"Beauty Condition matrix lock broken: {matrix}")
    yes = beauty_v2_condition_yes_kinds()
    if not yes <= set(beauty_v2_all_kinds()):
        raise RuntimeError("Condition YES kinds missing from catalog")
    for kind in (
        "Тональные средства",
        "Духи",
        "Шампуни",
        "Кремы для лица",
        "Зубные пасты",
        "Гель-лаки",
        "Краски для тату",
        "Средства для барбершопа",
    ):
        if beauty_v2_condition_decision(kind) != "NO":
            raise RuntimeError(f"Condition NO lock broken for {kind}")
    for kind in ("Фены", "Машинки для тату", "Парики и шиньоны", "Эпиляторы"):
        if beauty_v2_condition_decision(kind) != "YES":
            raise RuntimeError(f"Condition YES lock broken for {kind}")
    for forbidden in (
        "beauty_brand",
        "beauty_model",
        "volume",
        "package_state",
        "price_basis",
        "spf",
        "shade",
    ):
        if forbidden not in BEAUTY_CREATE_FORBIDDEN:
            raise RuntimeError(f"{forbidden} must stay forbidden")


def build_beauty_v2_core_fields() -> dict[str, list]:
    """Create cores for all 16 active Beauty L2 (Package A SoT)."""
    beauty_v2_assert_package_a_contracts()
    cond_approved = beauty_v2_condition_yes_kinds()
    out: dict[str, list] = {}

    for section_key, kinds in BEAUTY_V2_SECTION_KINDS.items():
        slug, _label = BEAUTY_V2_SECTION_META[section_key]
        fields: list = [
            _dep_field(
                BEAUTY_KIND_KEY,
                BEAUTY_KIND_LABEL,
                CategoryFieldType.enum,
                True,
                10,
                _choices(*kinds),
                hint="Какой товар?",
            ),
            _dep_field(
                BEAUTY_SELLER_KEY,
                BEAUTY_SELLER_LABEL,
                CategoryFieldType.enum,
                True,
                20,
                _choices(*BEAUTY_SELLER_OPTIONS),
            ),
        ]

        cond_kinds = [k for k in kinds if k in cond_approved]
        if cond_kinds:
            cond_opts: dict[str, Any] = _choices(*BEAUTY_CONDITION_OPTIONS)
            if set(cond_kinds) != set(kinds):
                cond_opts["depends_on"] = {
                    "field": BEAUTY_KIND_KEY,
                    "values": list(cond_kinds),
                }
            fields.append(
                _dep_field(
                    BEAUTY_CONDITION_KEY,
                    BEAUTY_CONDITION_LABEL,
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
            if key in BEAUTY_CREATE_FORBIDDEN:
                raise RuntimeError(f"forbidden Create field {slug}.{key}")
            if key not in _ALWAYS_CREATE:
                raise RuntimeError(f"unapproved Create field {slug}.{key}")
            opts = row[5]
            if opts and opts.get("choices") is not None and len(opts["choices"]) == 0:
                raise RuntimeError(f"empty picker {slug}.{key}")

        out[slug] = fields
    return out


def beauty_v2_all_kind_audit() -> list[dict[str, Any]]:
    """All-99 kind audit rows (Package A)."""
    cores = build_beauty_v2_core_fields()
    rows: list[dict[str, Any]] = []
    for section_key, kinds in BEAUTY_V2_SECTION_KINDS.items():
        slug, label = BEAUTY_V2_SECTION_META[section_key]
        fields = cores[slug]
        keys = [r[0] for r in fields]
        kind_row = next(r for r in fields if r[0] == BEAUTY_KIND_KEY)
        kind_opts = [c["value"] for c in kind_row[5]["choices"]]
        seller_row = next(r for r in fields if r[0] == BEAUTY_SELLER_KEY)
        seller_opts = [c["value"] for c in seller_row[5]["choices"]]
        cond_row = next((r for r in fields if r[0] == BEAUTY_CONDITION_KEY), None)
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
                BEAUTY_KIND_KEY,
                BEAUTY_SELLER_KEY,
                "price",
                "negotiable",
                "contact_methods",
            }
        ]
        for kind in kinds:
            cond = beauty_v2_condition_decision(kind)
            rows.append(
                {
                    "kind": kind,
                    "section_key": section_key,
                    "l2_slug": slug,
                    "l2_label": label,
                    "ownership": beauty_v2_kind_class(kind),
                    "kind_valid": kind in kind_opts,
                    "condition": cond,
                    "condition_in_schema": (kind in cond_values) == (cond == "YES"),
                    "seller": seller_opts,
                    "price": "price" in keys,
                    "package_state": "ABSENT",
                    "brand": "NO",
                    "model": "NO",
                    "volume": "NO",
                    "special_count": 1 if cond == "YES" else 0,
                    "forbidden": sorted(set(keys) & BEAUTY_CREATE_FORBIDDEN),
                    "components": {
                        BEAUTY_KIND_KEY: "enum",
                        BEAUTY_SELLER_KEY: "enum",
                        "price": "price",
                        "negotiable": "enum",
                        "contact_methods": "enum",
                        **(
                            {BEAUTY_CONDITION_KEY: "enum"}
                            if cond == "YES"
                            else {}
                        ),
                    },
                    "platform_owner": "BEAUTY",
                    "consumable_policy": "NO_CONDITION_NO_PACKAGE_STATE"
                    if cond == "NO"
                    else "DURABLE_CONDITION_YES",
                }
            )
    return rows


def beauty_v2_complexity_histogram() -> dict[str, int]:
    hist = {"0": 0, "1": 0, "2": 0, "3+": 0}
    for row in beauty_v2_all_kind_audit():
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


def _search_filter(
    key: str,
    label: str,
    ftype: CategoryFilterType,
    sort: int,
    config: dict[str, Any] | None,
) -> tuple:
    return (key, label, ftype, sort, config)


def build_beauty_v2_search_filters() -> dict[str, list]:
    """Package B Search SoT per canonical Beauty L2.

    Allowlist: beauty_kind + seller_type + condition (Package A semantic matrix).
    Price / negotiable / contacts / brand / volume / package_state never Search.
    Geo is shared Search UX, not CategoryFilter rows.
    """
    cores = build_beauty_v2_core_fields()
    out: dict[str, list] = {}
    for slug, fields in cores.items():
        filters: list = []
        for key, label, _ftype, _required, sort, options, _hint in fields:
            if key not in BEAUTY_V2_SEARCH_EAV_KEYS:
                continue
            if key in BEAUTY_V2_SEARCH_EXCLUDE:
                continue
            if key not in BEAUTY_V2_SEARCH_ALLOWLIST:
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
    if set(out) != BEAUTY_V2_CANONICAL_SLUGS:
        raise RuntimeError(
            "Beauty Search filter map != canonical L2 slugs: "
            f"extra={sorted(set(out) - BEAUTY_V2_CANONICAL_SLUGS)} "
            f"missing={sorted(BEAUTY_V2_CANONICAL_SLUGS - set(out))}"
        )
    return out


def beauty_v2_search_kind_audit_row(
    section_key: str, slug: str, kind: str
) -> dict[str, Any]:
    cond = beauty_v2_condition_decision(kind)
    visible = [BEAUTY_KIND_KEY, BEAUTY_SELLER_KEY]
    if cond == "YES":
        visible.append(BEAUTY_CONDITION_KEY)
    return {
        "l2": slug,
        "section": section_key,
        "kind": kind,
        "ownership": beauty_v2_kind_class(kind),
        "search_beauty_kind": "YES",
        "search_seller": "YES",
        "search_condition": cond,
        "search_package_state": "NO",
        "search_brand": "NO",
        "search_model": "NO",
        "search_volume": "NO",
        "search_shade": "NO",
        "search_spf": "NO",
        "search_skin_type": "NO",
        "search_hair_type": "NO",
        "search_size": "NO",
        "search_authenticity": "NO",
        "search_price_basis": "NO",
        "search_price": "NO",
        "search_negotiable": "NO",
        "search_contacts": "NO",
        "search_geo": "YES",
        "retired_resurrected": slug in BEAUTY_V2_RETIRED_SLUGS,
        "platform_owner": "BEAUTY",
        "visible_search_keys": visible,
        "ui_components": {
            BEAUTY_KIND_KEY: "multi_select",
            BEAUTY_SELLER_KEY: "multi_select",
            **({BEAUTY_CONDITION_KEY: "multi_select"} if cond == "YES" else {}),
            "geo": "region_city",
        },
    }


def beauty_v2_all_search_kind_audit() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for section_key, kinds in BEAUTY_V2_SECTION_KINDS.items():
        slug, _label = BEAUTY_V2_SECTION_META[section_key]
        for kind in kinds:
            rows.append(beauty_v2_search_kind_audit_row(section_key, slug, kind))
    return rows


def beauty_v2_assert_package_b_prep() -> None:
    """Backward-compatible alias — Package B contracts."""
    beauty_v2_assert_package_b_contracts()


def beauty_v2_assert_package_b_contracts() -> None:
    beauty_v2_assert_package_a_contracts()
    if BEAUTY_V2_SEARCH_POLICY != "SIMPLE":
        raise RuntimeError("Beauty Search policy must stay SIMPLE")
    if set(BEAUTY_V2_SEARCH_FUTURE) != {
        BEAUTY_KIND_KEY,
        BEAUTY_CONDITION_KEY,
        BEAUTY_SELLER_KEY,
        "geo",
    }:
        raise RuntimeError("Beauty Search future allowlist drifted")
    if BEAUTY_KIND_KEY not in BEAUTY_V2_SEARCH_EAV_KEYS:
        raise RuntimeError("beauty_kind must stay Search EAV")
    if BEAUTY_SELLER_KEY not in BEAUTY_V2_SEARCH_EAV_KEYS:
        raise RuntimeError("seller_type must stay Search EAV")
    if "geo" not in BEAUTY_V2_SEARCH_ALLOWLIST:
        raise RuntimeError("geo must remain on Search allowlist")
    if "price" in BEAUTY_V2_SEARCH_EAV_KEYS:
        raise RuntimeError("price must not be Search EAV")
    for banned in (
        "beauty_brand",
        "beauty_model",
        "volume",
        "package_state",
        "spf",
        "shade",
        "price_basis",
        "size",
        "authenticity",
    ):
        if banned in BEAUTY_V2_SEARCH_ALLOWLIST:
            raise RuntimeError(f"{banned} must not be Search")
        if banned in BEAUTY_V2_SEARCH_FUTURE:
            raise RuntimeError(f"{banned} must not be Search future")
    filters = build_beauty_v2_search_filters()
    if set(filters) != BEAUTY_V2_CANONICAL_SLUGS:
        raise RuntimeError("Package B Search map ≠ canonical L2")
    if set(filters) & BEAUTY_V2_RETIRED_SLUGS:
        raise RuntimeError("Retired Beauty slugs must not appear in Search")
    for slug, rows in filters.items():
        keys = {r[0] for r in rows}
        if keys & BEAUTY_CREATE_FORBIDDEN:
            raise RuntimeError(f"Forbidden Search keys: {slug}")
        if keys & {
            "price",
            "negotiable",
            "contact_methods",
            "package_state",
            "beauty_brand",
            "volume",
        }:
            raise RuntimeError(f"Create-only leaked into Search: {slug}")
        if BEAUTY_KIND_KEY not in keys or BEAUTY_SELLER_KEY not in keys:
            raise RuntimeError(f"Search missing kind/seller: {slug}")
        if not rows:
            raise RuntimeError(f"Empty Search filters: {slug}")
        cores = {r[0] for r in build_beauty_v2_core_fields()[slug]}
        if BEAUTY_CONDITION_KEY in cores:
            assert BEAUTY_CONDITION_KEY in keys, slug
        else:
            assert BEAUTY_CONDITION_KEY not in keys, slug
        for _key, _label, _ftype, _sort, cfg in rows:
            if cfg and cfg.get("choices") is not None and len(cfg["choices"]) == 0:
                raise RuntimeError(f"Empty Search picker: {slug}.{_key}")
    audit = beauty_v2_all_search_kind_audit()
    if len(audit) != 99:
        raise RuntimeError(f"Search audit expects 99, got {len(audit)}")
    yes = sum(1 for r in audit if r["search_condition"] == "YES")
    no = sum(1 for r in audit if r["search_condition"] == "NO")
    if yes != 18 or no != 81:
        raise RuntimeError(f"Search Condition matrix drifted: YES={yes} NO={no}")
    if any(r["search_package_state"] != "NO" for r in audit):
        raise RuntimeError("package_state leaked into Search audit")
    if any(r["search_brand"] != "NO" for r in audit):
        raise RuntimeError("Brand leaked into Search audit")
    if "Косметички" in {r["kind"] for r in audit}:
        raise RuntimeError("Косметички leaked into Search")
    if "Украшения для пирсинга" in {r["kind"] for r in audit}:
        raise RuntimeError("Piercing jewelry leaked into Search")
