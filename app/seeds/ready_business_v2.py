# -*- coding: utf-8 -*-
"""Ready Business & Franchises V2 — taxonomy + Package A Create SoT.

Package B Search filters are NOT seeded here.
Finance / operations claims stay in Description.
"""
from __future__ import annotations

from typing import Any, Literal

from app.models.category import CategoryEntityType
from app.models.category_enums import CategoryFieldType, CategoryFilterType
from app.seeds.shared_goods_create_contract import (
    CONTACT_METHOD_CHOICES,
    GOODS_NEGOTIABLE_CHOICES,
)

READY_BUSINESS_ROOT_SLUG = "ready-business"
READY_BUSINESS_ROOT_LABEL = "Готовый бизнес и франшизы"
READY_BUSINESS_ROOT_UI_ALIAS = "Готовый бизнес"
READY_BUSINESS_V2_ENTITY_TYPE = CategoryEntityType.business

READY_BUSINESS_CONDITION_POLICY = "ABSENT"

READY_BUSINESS_POSTER_KEY = "poster_type"
READY_BUSINESS_POSTER_LABEL = "Кто разместил"
READY_BUSINESS_POSTER_OPTIONS = ("Владелец", "Представитель", "Другой")

READY_BUSINESS_PREMISES_KEY = "premises"
READY_BUSINESS_PREMISES_LABEL = "Помещение"
READY_BUSINESS_PREMISES_OPTIONS = (
    "В собственности",
    "В аренде",
    "Без помещения",
)
READY_BUSINESS_PREMISES_REQUIRED = False

READY_BUSINESS_KIND_KEY = "ready_business_kind"
READY_BUSINESS_KIND_LABEL = "Вид бизнеса"

READY_BUSINESS_V2_SEARCH_ALLOWLIST = frozenset(
    {
        READY_BUSINESS_KIND_KEY,
        READY_BUSINESS_POSTER_KEY,
        "geo",
        READY_BUSINESS_PREMISES_KEY,  # only where semantically useful (Package B)
    }
)
READY_BUSINESS_V2_SEARCH_EAV_KEYS = frozenset(
    {
        READY_BUSINESS_KIND_KEY,
        READY_BUSINESS_POSTER_KEY,
        READY_BUSINESS_PREMISES_KEY,
    }
)
READY_BUSINESS_V2_SEARCH_EXCLUDE = frozenset(
    {
        "price",
        "negotiable",
        "contact_methods",
        "condition",
        "seller_type",
        "business_type",
        "currency",
        "revenue",
        "profit",
        "net_profit",
        "payback",
        "investment",
        "royalty",
        "lump_sum",
        "staff_count",
        "business_age",
        "rent",
        "rent_amount",
        "area",
        "debts",
        "loans",
        "license",
        "documents",
        "franchise_support",
        "territory",
    }
)
READY_BUSINESS_V2_SEARCH_POLICY = "SIMPLE"

_ALWAYS_CREATE = frozenset(
    {
        READY_BUSINESS_KIND_KEY,
        READY_BUSINESS_POSTER_KEY,
        "price",
        READY_BUSINESS_PREMISES_KEY,
        "negotiable",
        "contact_methods",
    }
)

READY_BUSINESS_NEGOTIABLE_POLICY = "CANONICAL_YES"
READY_BUSINESS_NEGOTIABLE_OPTIONS = ("Есть торг", "Без торга")

READY_BUSINESS_PRICE_SEMANTICS = {
    "ready_business": "ASKING_SALE_PRICE",
    "franchise": "ENTRY_START_PRICE",
}

READY_BUSINESS_CREATE_FORBIDDEN = frozenset(
    {
        "condition",
        "business_type",
        "operating_period",
        "included_assets",
        "revenue",
        "staff_count",
        "profit",
        "payback",
        "business_age",
        "rent_amount",
        "area",
        "equipment_included",
        "inventory_included",
        "reason_for_sale",
        "license",
        "documents",
        "debts",
        "royalty",
        "investment",
        "franchise_support",
        "territory",
        "seller_type",  # goods / fragmented seller — use poster_type
    }
)

READY_BUSINESS_SEARCH_FORBIDDEN = frozenset(
    {
        "profit",
        "revenue",
        "payback",
        "royalty",
        "investment",
        "price_basis",
        "staff_count",
        "area",
        "rent_amount",
        "documents",
        "condition",
    }
)

READY_BUSINESS_AI_FINANCIAL_CLAIM_RULE = (
    "AI must not invent factual claims: revenue, profit, payback, staff count, "
    "business age, debts, licenses, contracts, royalty, investment requirements."
)

# Legacy dual-tree L2 — soft-retire, rows kept.
READY_BUSINESS_V2_LEGACY_L2_SLUGS = frozenset(
    {
        "ready-business-cafe",
        "ready-business-retail",
        "ready-business-online",
        "ready-business-franchise",
    }
)

# Modern L2 retired for product identity (no automatic destination).
READY_BUSINESS_V2_RETIRED_MODERN = {
    "ready-business-dolya-v-biznese-i-investitsii": (
        "RETIRED_NO_CANONICAL_DESTINATION",
        "Shares/investment seeking is not ordinary ready-business identity.",
    ),
    "ready-business-kriptobiznes-i-tsifrovye-aktivy": (
        "NO_CANONICAL_DESTINATION",
        "Crypto is not a Ready Business kind.",
    ),
    "ready-business-biznes-pod-klyuch": (
        "RETIRED_MIXED_IDENTITY_NO_CANONICAL_DESTINATION",
        "Turnkey kinds mix READY_BUSINESS / SERVICE / EQUIPMENT / RE without "
        "listing evidence; removed from active catalog until product revisit.",
    ),
}

READY_BUSINESS_V2_RETIRED_SLUGS = frozenset(
    set(READY_BUSINESS_V2_LEGACY_L2_SLUGS) | set(READY_BUSINESS_V2_RETIRED_MODERN)
)

# Retired kinds inside otherwise-kept L2s (identity cleanup).
READY_BUSINESS_V2_RETIRED_KINDS = {
    "Линии": (
        "WRONG_ROOT",
        "BUSINESS_EQUIPMENT",
        "Production line/equipment alone is Business Equipment, not a going concern.",
    ),
    "Офисы": (
        "WRONG_ROOT",
        "COMMERCIAL_REAL_ESTATE",
        "Bare 'Офисы' is premises identity; Commercial RE owns office premises.",
    ),
    "Готовые ОсОО": (
        "RETIRED_NO_CANONICAL_DESTINATION",
        "NO_CANONICAL_DESTINATION",
        "Sale of legal entities is not ordinary Ready Business identity.",
    ),
    "Цех под ключ": (
        "RETIRED_MIXED_IDENTITY",
        "NO_CANONICAL_DESTINATION",
        "Turnkey workshop wording mixes equipment/setup/service vs going concern.",
    ),
    "Офис под ключ": (
        "RETIRED_MIXED_IDENTITY",
        "NO_CANONICAL_DESTINATION",
        "Turnkey office mixes premises/setup/service vs going concern.",
    ),
    "Точка под ключ": (
        "RETIRED_MIXED_IDENTITY",
        "NO_CANONICAL_DESTINATION",
        "Insufficient evidence of transferable operating business vs setup service.",
    ),
    "Сеть под ключ": (
        "RETIRED_MIXED_IDENTITY",
        "NO_CANONICAL_DESTINATION",
        "Insufficient evidence of transferable operating business vs setup service.",
    ),
    "Другой бизнес под ключ": (
        "RETIRED_MIXED_IDENTITY",
        "NO_CANONICAL_DESTINATION",
        "Catch-all turnkey is not a clean Ready Business kind.",
    ),
}

KindClass = Literal["READY_BUSINESS", "FRANCHISE"]
PremisesDecision = Literal["YES", "NO"]

# Canonical active modern L2: (label, slug, sort_order)
READY_BUSINESS_V2_CANONICAL_LEAVES: tuple[tuple[str, str, int], ...] = (
    ("Магазины и торговые точки", "ready-business-magaziny-i-torgovye-tochki", 10),
    ("Кафе, рестораны и общепит", "ready-business-kafe-restorany-i-obschepit", 20),
    ("Гостиницы и гостевые дома", "ready-business-gostinitsy-i-gostevye-doma", 30),
    ("Салоны красоты и барбершопы", "ready-business-salony-krasoty-i-barbershopy", 40),
    ("Швейные цеха и ателье", "ready-business-shveynye-tseha-i-atele", 50),
    ("Производство и цеха", "ready-business-proizvodstvo-i-tseha", 60),
    ("Автомойки/автоуслуги и СТО", "ready-business-avtomoyki-avtouslugi-i-sto", 70),
    ("Медицинские центры и аптеки", "ready-business-meditsinskie-tsentry-i-apteki", 80),
    ("Образовательные центры", "ready-business-obrazovatelnye-tsentry", 90),
    ("Онлайн магазины", "ready-business-onlayn-magaziny", 100),
    ("Франшизы", "ready-business-franshizy", 110),
    ("Сельскохозяйственный бизнес", "ready-business-selskohozyaystvennyy-biznes", 120),
    ("Развлекательный бизнес", "ready-business-razvlekatelnyy-biznes", 130),
    ("Туристический бизнес", "ready-business-turisticheskiy-biznes", 140),
    # Slug kept for stability; label drops investment wording.
    ("Финансовый бизнес", "ready-business-finansovyy-investits-nyy-biznes", 150),
    ("Прочий готовый бизнес", "ready-business-prochiy-gotovyy-biznes", 160),
)

READY_BUSINESS_V2_CANONICAL_SLUGS = frozenset(
    slug for _, slug, _ in READY_BUSINESS_V2_CANONICAL_LEAVES
)
READY_BUSINESS_V2_EXPECTED_L2_COUNT = len(READY_BUSINESS_V2_CANONICAL_LEAVES)
READY_BUSINESS_FRANCHISE_SLUG = "ready-business-franshizy"

# section_key → (slug, label, kinds, premises_default)
_SECTION_SPECS: dict[str, tuple[str, str, tuple[str, ...], bool]] = {
    "shops": (
        "ready-business-magaziny-i-torgovye-tochki",
        "Магазины и торговые точки",
        (
            "Магазины",
            "Бутики",
            "Островки",
            "Киоски",
            "Павильоны",
            "Оптовые базы",
            "Другие торговые точки",
        ),
        True,
    ),
    "horeca": (
        "ready-business-kafe-restorany-i-obschepit",
        "Кафе, рестораны и общепит",
        (
            "Кафе",
            "Рестораны",
            "Фастфуд",
            "Фудтраки",
            "Столовые",
            "Другой общепит",
        ),
        True,
    ),
    "hotels": (
        "ready-business-gostinitsy-i-gostevye-doma",
        "Гостиницы и гостевые дома",
        (
            "Гостиницы",
            "Гостевые дома",
            "Хостелы",
            "Базы отдыха",
            "Другие объекты размещения",
        ),
        True,
    ),
    "salons": (
        "ready-business-salony-krasoty-i-barbershopy",
        "Салоны красоты и барбершопы",
        (
            "Салоны",
            "Барбершопы",
            "Студии",
            "Кабинеты",
            "СПА",
            "Другие салоны",
        ),
        True,
    ),
    "sewing": (
        "ready-business-shveynye-tseha-i-atele",
        "Швейные цеха и ателье",
        ("Цеха", "Ателье", "Мастерские", "Другие швейные бизнесы"),
        True,
    ),
    "production": (
        "ready-business-proizvodstvo-i-tseha",
        "Производство и цеха",
        # "Линии" retired → Business Equipment
        ("Заводы", "Другое производство"),
        True,
    ),
    "auto": (
        "ready-business-avtomoyki-avtouslugi-i-sto",
        "Автомойки/автоуслуги и СТО",
        # "Боксы" kept as operating auto-business point identity under this sector.
        ("Автомойки", "СТО", "Боксы", "Другой автобизнес"),
        True,
    ),
    "medical": (
        "ready-business-meditsinskie-tsentry-i-apteki",
        "Медицинские центры и аптеки",
        (
            "Клиники",
            "Центры",
            "Аптеки",
            "Лаборатории",
            "Другие медицинские бизнесы",
        ),
        True,
    ),
    "education": (
        "ready-business-obrazovatelnye-tsentry",
        "Образовательные центры",
        (
            "Центры обучения",
            "Школы",
            "Детские сады",
            "Курсы",
            "Другие образовательные бизнесы",
        ),
        True,
    ),
    "online": (
        "ready-business-onlayn-magaziny",
        "Онлайн магазины",
        (
            "Интернет-магазины",
            "Витрины",
            "Маркетплейсы",
            "Другие онлайн-магазины",
        ),
        False,
    ),
    "franchise": (
        "ready-business-franshizy",
        "Франшизы",
        (
            "Франшиза точки",
            "Региональная франшиза",
            "Мастер-франшиза",
            "Другие франшизы",
        ),
        False,
    ),
    "farm": (
        "ready-business-selskohozyaystvennyy-biznes",
        "Сельскохозяйственный бизнес",
        ("Хозяйства", "Тепличные хозяйства", "Другой сельхозбизнес"),
        True,
    ),
    "leisure": (
        "ready-business-razvlekatelnyy-biznes",
        "Развлекательный бизнес",
        (
            "Клубы",
            "Залы",
            "Аттракционы",
            "Площадки",
            "Другой развлекательный бизнес",
        ),
        True,
    ),
    "tourism": (
        "ready-business-turisticheskiy-biznes",
        "Туристический бизнес",
        (
            "Агентства",
            "Операторы",
            "Бюро",
            "Прокат",
            "Другой туристический бизнес",
        ),
        True,
    ),
    "finance": (
        "ready-business-finansovyy-investits-nyy-biznes",
        "Финансовый бизнес",
        # "Офисы" retired → Commercial RE
        ("Ломбарды", "Обменные пункты", "Другой финансовый бизнес"),
        True,
    ),
    "other": (
        "ready-business-prochiy-gotovyy-biznes",
        "Прочий готовый бизнес",
        # "Готовые ОсОО" retired — no canonical destination
        ("Вендинг", "Другой готовый бизнес"),
        True,
    ),
}


def _item(label: str) -> dict[str, Any]:
    return {"value": label, "label": label}


def _opts(*labels: str) -> list[dict[str, Any]]:
    return [_item(label) for label in labels]


def _poster_group() -> dict[str, Any]:
    return {
        "label": READY_BUSINESS_POSTER_LABEL,
        "options": _opts(*READY_BUSINESS_POSTER_OPTIONS),
    }


def _premises_group() -> dict[str, Any]:
    return {
        "label": READY_BUSINESS_PREMISES_LABEL,
        "options": _opts(*READY_BUSINESS_PREMISES_OPTIONS),
    }


def build_ready_business_v2_sections() -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for key, (slug, label, kinds, premises) in _SECTION_SPECS.items():
        filters = [_poster_group()]
        if premises:
            filters.append(_premises_group())
        out[key] = {
            "category_slug": slug,
            "label": label,
            "question": "Какой бизнес?",
            "roles": _opts(*kinds),
            "filters": filters,
            "premises_default": premises,
        }
    return out


READY_BUSINESS_V2_SECTION_KINDS: dict[str, tuple[str, ...]] = {
    key: kinds for key, (_s, _l, kinds, _p) in _SECTION_SPECS.items()
}


def ready_business_v2_all_kinds() -> list[str]:
    out: list[str] = []
    for kinds in READY_BUSINESS_V2_SECTION_KINDS.values():
        out.extend(kinds)
    return out


def ready_business_v2_kind_count() -> int:
    return len(ready_business_v2_all_kinds())


def ready_business_v2_kind_class(kind: str) -> KindClass:
    franchise_kinds = set(READY_BUSINESS_V2_SECTION_KINDS["franchise"])
    if kind in franchise_kinds:
        return "FRANCHISE"
    if kind in READY_BUSINESS_V2_RETIRED_KINDS:
        raise ValueError(f"Retired kind has no active class: {kind}")
    return "READY_BUSINESS"


def ready_business_v2_premises_decision(kind: str) -> PremisesDecision:
    """Independent YES/NO matrix — not a self-proving allowlist copy."""
    # Explicit independent expectations keyed by kind identity.
    no_premises = {
        # Online storefronts — no physical premises field.
        "Интернет-магазины",
        "Витрины",
        "Маркетплейсы",
        "Другие онлайн-магазины",
        # Franchise formats — premises not assumed; Description if needed.
        "Франшиза точки",
        "Региональная франшиза",
        "Мастер-франшиза",
        "Другие франшизы",
    }
    if kind in no_premises:
        return "NO"
    if kind not in set(ready_business_v2_all_kinds()):
        raise ValueError(f"Unknown Ready Business kind for premises matrix: {kind}")
    return "YES"


def ready_business_v2_condition_decision(kind: str) -> str:
    assert kind in set(ready_business_v2_all_kinds())
    return "NO"


def ready_business_v2_package_a_field_target() -> dict[str, Any]:
    return {
        "kind": READY_BUSINESS_KIND_KEY,
        "kind_label": READY_BUSINESS_KIND_LABEL,
        "poster": READY_BUSINESS_POSTER_KEY,
        "poster_options": list(READY_BUSINESS_POSTER_OPTIONS),
        "price": "price",
        "premises": READY_BUSINESS_PREMISES_KEY,
        "premises_required": READY_BUSINESS_PREMISES_REQUIRED,
        "premises_scope": "POSITIVE_ALLOWLIST_DEFAULT_OFF_VIA_KIND_MATRIX",
        "negotiable": READY_BUSINESS_NEGOTIABLE_POLICY,
        "contact_methods": "CANONICAL_SIX",
        "condition": READY_BUSINESS_CONDITION_POLICY,
        "forbidden": sorted(READY_BUSINESS_CREATE_FORBIDDEN),
        "price_semantics": dict(READY_BUSINESS_PRICE_SEMANTICS),
        "ai_financial_claim_rule": READY_BUSINESS_AI_FINANCIAL_CLAIM_RULE,
        "required": (
            READY_BUSINESS_KIND_KEY,
            READY_BUSINESS_POSTER_KEY,
            "price",
            "contact_methods",
        ),
        "optional": (READY_BUSINESS_PREMISES_KEY, "negotiable"),
    }


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


def ready_business_v2_assert_package_a_contracts() -> None:
    ready_business_v2_assert_cleanup_contracts()
    if READY_BUSINESS_KIND_LABEL != "Вид бизнеса":
        raise RuntimeError("Ready Business kind label must be Вид бизнеса")
    if READY_BUSINESS_POSTER_OPTIONS != ("Владелец", "Представитель", "Другой"):
        raise RuntimeError("Ready Business poster options drifted")
    if READY_BUSINESS_CONDITION_POLICY != "ABSENT":
        raise RuntimeError("Ready Business Condition must stay ABSENT")
    if READY_BUSINESS_NEGOTIABLE_OPTIONS != GOODS_NEGOTIABLE_CHOICES:
        raise RuntimeError("Ready Business negotiable must match shared goods")
    if "seller_type" not in READY_BUSINESS_CREATE_FORBIDDEN:
        raise RuntimeError("seller_type must stay forbidden for Ready Business")
    if "condition" not in READY_BUSINESS_CREATE_FORBIDDEN:
        raise RuntimeError("condition must stay forbidden")
    if "revenue" not in READY_BUSINESS_CREATE_FORBIDDEN:
        raise RuntimeError("revenue must stay forbidden")
    if READY_BUSINESS_KIND_KEY != "ready_business_kind":
        raise RuntimeError("kind key lock broken")
    if ready_business_v2_kind_count() != 70:
        raise RuntimeError(
            f"Ready Business Package A expects 70 kinds, got {ready_business_v2_kind_count()}"
        )


def build_ready_business_v2_core_fields() -> dict[str, list]:
    """Create cores for all 16 active Ready Business L2 (Package A SoT)."""
    ready_business_v2_assert_package_a_contracts()
    out: dict[str, list] = {}

    for section_key, (slug, _label, kinds, premises_default) in _SECTION_SPECS.items():
        price_hint = (
            "Цена входа / старта франшизы (СОМ / KGS). Детали — в описании."
            if section_key == "franchise"
            else "Цена продажи бизнеса (СОМ / KGS)"
        )
        fields: list = [
            _dep_field(
                READY_BUSINESS_KIND_KEY,
                READY_BUSINESS_KIND_LABEL,
                CategoryFieldType.enum,
                True,
                10,
                _choices(*kinds),
                hint="Какой бизнес?",
            ),
            _dep_field(
                READY_BUSINESS_POSTER_KEY,
                READY_BUSINESS_POSTER_LABEL,
                CategoryFieldType.enum,
                True,
                20,
                _choices(*READY_BUSINESS_POSTER_OPTIONS),
            ),
        ]
        # Premises: section-uniform matrix — physical YES, online/franchise NO.
        if premises_default:
            for kind in kinds:
                if ready_business_v2_premises_decision(kind) != "YES":
                    raise RuntimeError(
                        f"premises matrix mismatch for physical section {slug}/{kind}"
                    )
            fields.append(
                _dep_field(
                    READY_BUSINESS_PREMISES_KEY,
                    READY_BUSINESS_PREMISES_LABEL,
                    CategoryFieldType.enum,
                    False,
                    30,
                    _choices(*READY_BUSINESS_PREMISES_OPTIONS),
                )
            )
        else:
            for kind in kinds:
                if ready_business_v2_premises_decision(kind) != "NO":
                    raise RuntimeError(
                        f"premises matrix mismatch for no-premises section {slug}/{kind}"
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
                    hint=price_hint,
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
            if key in READY_BUSINESS_CREATE_FORBIDDEN:
                raise RuntimeError(f"forbidden Create field {slug}.{key}")
            if key not in _ALWAYS_CREATE:
                raise RuntimeError(f"unapproved Create field {slug}.{key}")
            opts = row[5]
            if opts and opts.get("choices") is not None and len(opts["choices"]) == 0:
                raise RuntimeError(f"empty picker {slug}.{key}")

        out[slug] = fields
    return out


def ready_business_v2_all_kind_audit() -> list[dict[str, Any]]:
    """All-70 kind audit rows (Package A)."""
    cores = build_ready_business_v2_core_fields()
    rows: list[dict[str, Any]] = []
    for section_key, (slug, _label, kinds, premises_default) in _SECTION_SPECS.items():
        fields = cores[slug]
        keys = [r[0] for r in fields]
        kind_row = next(r for r in fields if r[0] == READY_BUSINESS_KIND_KEY)
        kind_opts = [c["value"] for c in kind_row[5]["choices"]]
        poster_row = next(r for r in fields if r[0] == READY_BUSINESS_POSTER_KEY)
        poster_opts = [c["value"] for c in poster_row[5]["choices"]]
        specials = [
            k
            for k in keys
            if k
            not in {
                READY_BUSINESS_KIND_KEY,
                READY_BUSINESS_POSTER_KEY,
                "price",
                "negotiable",
                "contact_methods",
            }
        ]
        for kind in kinds:
            premises = ready_business_v2_premises_decision(kind)
            rows.append(
                {
                    "kind": kind,
                    "section": section_key,
                    "slug": slug,
                    "class": ready_business_v2_kind_class(kind),
                    "kind_valid": kind in kind_opts,
                    "condition": "NO",
                    "condition_in_schema": "condition" not in keys,
                    "poster": poster_opts,
                    "price": "price" in keys,
                    "premises": premises,
                    "premises_in_schema": READY_BUSINESS_PREMISES_KEY in keys,
                    "premises_section_default": premises_default,
                    "special_count": len(specials),
                    "forbidden": sorted(set(keys) & READY_BUSINESS_CREATE_FORBIDDEN),
                    "components": {
                        READY_BUSINESS_KIND_KEY: "enum",
                        READY_BUSINESS_POSTER_KEY: "enum",
                        "price": "price",
                        "negotiable": "enum",
                        "contact_methods": "enum",
                        **(
                            {READY_BUSINESS_PREMISES_KEY: "enum"}
                            if READY_BUSINESS_PREMISES_KEY in keys
                            else {}
                        ),
                    },
                    "ownership": "READY_BUSINESS"
                    if ready_business_v2_kind_class(kind) == "READY_BUSINESS"
                    else "FRANCHISE",
                }
            )
    return rows


def ready_business_v2_complexity_histogram() -> dict[str, int]:
    """special_count histogram — premises only (=0 or 1)."""
    hist = {"0": 0, "1": 0, "2": 0, "3+": 0}
    for row in ready_business_v2_all_kind_audit():
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


def ready_business_v2_assert_cleanup_contracts() -> None:
    assert READY_BUSINESS_ROOT_SLUG == "ready-business"
    assert READY_BUSINESS_ROOT_LABEL == "Готовый бизнес и франшизы"
    assert READY_BUSINESS_V2_EXPECTED_L2_COUNT == 16
    assert len(READY_BUSINESS_V2_CANONICAL_LEAVES) == 16
    assert len(build_ready_business_v2_sections()) == 16
    assert ready_business_v2_kind_count() == 70
    assert READY_BUSINESS_CONDITION_POLICY == "ABSENT"
    assert READY_BUSINESS_POSTER_OPTIONS == ("Владелец", "Представитель", "Другой")
    assert "Франчайзер" not in READY_BUSINESS_POSTER_OPTIONS
    for banned in ("Частное лицо", "Магазин", "Собственник", "Компания", "Агентство"):
        assert banned not in READY_BUSINESS_POSTER_OPTIONS
    assert READY_BUSINESS_V2_LEGACY_L2_SLUGS.isdisjoint(READY_BUSINESS_V2_CANONICAL_SLUGS)
    for slug in READY_BUSINESS_V2_RETIRED_MODERN:
        assert slug not in READY_BUSINESS_V2_CANONICAL_SLUGS
    assert READY_BUSINESS_FRANCHISE_SLUG in READY_BUSINESS_V2_CANONICAL_SLUGS
    assert "ready-business-franchise" not in READY_BUSINESS_V2_CANONICAL_SLUGS
    for kind in ("Линии", "Офисы", "Готовые ОсОО"):
        assert kind in READY_BUSINESS_V2_RETIRED_KINDS
        assert kind not in set(ready_business_v2_all_kinds())
    sections = build_ready_business_v2_sections()
    active_slugs = {c["category_slug"] for c in sections.values()}
    assert active_slugs == READY_BUSINESS_V2_CANONICAL_SLUGS
    # Unique kinds across catalog.
    seen: dict[str, str] = {}
    for cat in sections.values():
        for role in cat["roles"]:
            label = role["label"]
            assert label not in seen, label
            seen[label] = cat["label"]
        filter_labels = [g["label"] for g in cat["filters"]]
        assert filter_labels[0] == READY_BUSINESS_POSTER_LABEL
        poster_opts = [o["label"] for o in cat["filters"][0]["options"]]
        assert poster_opts == list(READY_BUSINESS_POSTER_OPTIONS)
        assert "Состояние" not in filter_labels
        premises_default = cat["premises_default"]
        if premises_default:
            assert READY_BUSINESS_PREMISES_LABEL in filter_labels
        else:
            assert READY_BUSINESS_PREMISES_LABEL not in filter_labels
    for kind in ready_business_v2_all_kinds():
        assert ready_business_v2_kind_class(kind) in ("READY_BUSINESS", "FRANCHISE")
        assert ready_business_v2_premises_decision(kind) in ("YES", "NO")
        assert ready_business_v2_condition_decision(kind) == "NO"
    # Sample platform-coherence bans in active kinds.
    banned_active = {
        "Готовый бизнес",
        "Готовые ОсОО",
        "Линии",
        "Офисы",
        "Доля",
        "Пакет",
        "Партнёрство",
        "Майнинг-фермы",
        "Инсулин",
        "Холодильные витрины",
        "Вакансия",
        "Резюме",
    }
    assert banned_active.isdisjoint(seen)


def _search_filter(
    key: str,
    label: str,
    ftype: CategoryFilterType,
    sort: int,
    config: dict[str, Any] | None,
) -> tuple:
    return (key, label, ftype, sort, config)


def build_ready_business_v2_search_filters() -> dict[str, list]:
    """Package B Search SoT per canonical Ready Business L2.

    Allowlist: ready_business_kind + poster_type + premises (semantic matrix).
    Condition / price / negotiable / contacts / finance never Search.
    Geo is shared Search UX, not CategoryFilter rows.
    """
    cores = build_ready_business_v2_core_fields()
    out: dict[str, list] = {}
    for slug, fields in cores.items():
        filters: list = []
        for key, label, _ftype, _required, sort, options, _hint in fields:
            if key not in READY_BUSINESS_V2_SEARCH_EAV_KEYS:
                continue
            if key in READY_BUSINESS_V2_SEARCH_EXCLUDE:
                continue
            if key not in READY_BUSINESS_V2_SEARCH_ALLOWLIST:
                continue
            # Premises only when Package A Create schema includes it for this L2.
            if key == READY_BUSINESS_PREMISES_KEY:
                # Independent matrix already enforced in Create builder.
                pass
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
    if set(out) != READY_BUSINESS_V2_CANONICAL_SLUGS:
        raise RuntimeError(
            "Ready Business Search filter map != canonical L2 slugs: "
            f"extra={sorted(set(out) - READY_BUSINESS_V2_CANONICAL_SLUGS)} "
            f"missing={sorted(READY_BUSINESS_V2_CANONICAL_SLUGS - set(out))}"
        )
    return out


def ready_business_v2_search_kind_audit_row(
    section_key: str, slug: str, kind: str
) -> dict[str, Any]:
    premises = ready_business_v2_premises_decision(kind)
    ownership = (
        "FRANCHISE"
        if ready_business_v2_kind_class(kind) == "FRANCHISE"
        else "READY_BUSINESS"
    )
    visible = [READY_BUSINESS_KIND_KEY, READY_BUSINESS_POSTER_KEY]
    if premises == "YES":
        visible.append(READY_BUSINESS_PREMISES_KEY)
    return {
        "l2": slug,
        "section": section_key,
        "kind": kind,
        "search_ready_business_kind": "YES",
        "search_poster": "YES",
        "search_premises": premises,
        "search_condition": "NO",
        "search_price": "NO",
        "search_negotiable": "NO",
        "search_contacts": "NO",
        "search_revenue": "NO",
        "search_profit": "NO",
        "search_payback": "NO",
        "search_royalty": "NO",
        "search_investment": "NO",
        "search_geo": "YES",
        "retired_resurrected": slug in READY_BUSINESS_V2_RETIRED_SLUGS,
        "ownership": ownership,
        "visible_search_keys": visible,
        "ui_components": {
            READY_BUSINESS_KIND_KEY: "multi_select",
            READY_BUSINESS_POSTER_KEY: "multi_select",
            "geo": "region_city",
            **(
                {READY_BUSINESS_PREMISES_KEY: "multi_select"}
                if premises == "YES"
                else {}
            ),
        },
    }


def ready_business_v2_all_search_kind_audit() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for section_key, (slug, _label, kinds, _premises) in _SECTION_SPECS.items():
        for kind in kinds:
            rows.append(
                ready_business_v2_search_kind_audit_row(section_key, slug, kind)
            )
    return rows


def ready_business_v2_assert_package_b_contracts() -> None:
    ready_business_v2_assert_package_a_contracts()
    if READY_BUSINESS_V2_SEARCH_POLICY != "SIMPLE":
        raise RuntimeError("Ready Business Search policy must stay SIMPLE")
    if READY_BUSINESS_KIND_KEY not in READY_BUSINESS_V2_SEARCH_EAV_KEYS:
        raise RuntimeError("kind must stay Search EAV")
    if READY_BUSINESS_POSTER_KEY not in READY_BUSINESS_V2_SEARCH_EAV_KEYS:
        raise RuntimeError("poster must stay Search EAV")
    if "geo" not in READY_BUSINESS_V2_SEARCH_ALLOWLIST:
        raise RuntimeError("geo must remain on Search allowlist")
    if "condition" in READY_BUSINESS_V2_SEARCH_EAV_KEYS:
        raise RuntimeError("condition must not be Search EAV")
    if "seller_type" in READY_BUSINESS_V2_SEARCH_EAV_KEYS:
        raise RuntimeError("seller_type must not be Search EAV")
    filters = build_ready_business_v2_search_filters()
    if set(filters) != READY_BUSINESS_V2_CANONICAL_SLUGS:
        raise RuntimeError("Package B Search map ≠ canonical L2")
    if set(filters) & READY_BUSINESS_V2_RETIRED_SLUGS:
        raise RuntimeError("Retired Ready Business slugs must not appear in Search")
    for slug, rows in filters.items():
        keys = {r[0] for r in rows}
        if keys & READY_BUSINESS_CREATE_FORBIDDEN:
            raise RuntimeError(f"Forbidden Search keys: {slug}")
        if keys & {
            "price",
            "negotiable",
            "contact_methods",
            "condition",
            "seller_type",
            "revenue",
            "profit",
            "royalty",
            "investment",
        }:
            raise RuntimeError(f"Create-only / finance leaked into Search: {slug}")
        if READY_BUSINESS_KIND_KEY not in keys or READY_BUSINESS_POSTER_KEY not in keys:
            raise RuntimeError(f"Search missing kind/poster: {slug}")
        if not rows:
            raise RuntimeError(f"Empty Search filters: {slug}")
        # Premises presence must match Create/matrix for this L2.
        from_core = {
            r[0] for r in build_ready_business_v2_core_fields()[slug]
        }
        has_premises_create = READY_BUSINESS_PREMISES_KEY in from_core
        has_premises_search = READY_BUSINESS_PREMISES_KEY in keys
        if has_premises_create != has_premises_search:
            raise RuntimeError(
                f"Premises Search/Create mismatch for {slug}: "
                f"create={has_premises_create} search={has_premises_search}"
            )
    audit = ready_business_v2_all_search_kind_audit()
    if len(audit) != 70:
        raise RuntimeError(f"Search audit expects 70 kinds, got {len(audit)}")
    if any(r["search_condition"] != "NO" for r in audit):
        raise RuntimeError("Condition must be ABSENT from Ready Business Search")
    if any(r["search_revenue"] != "NO" for r in audit):
        raise RuntimeError("revenue must be ABSENT from Search")
    yes = sum(1 for r in audit if r["search_premises"] == "YES")
    no = sum(1 for r in audit if r["search_premises"] == "NO")
    if yes != 62 or no != 8:
        raise RuntimeError(f"Premises Search matrix drift: YES={yes} NO={no}")
