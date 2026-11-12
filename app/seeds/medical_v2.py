# -*- coding: utf-8 -*-
"""Medical Goods V2 — taxonomy + Package A Create SoT + Package B Search.

Backend/API is Create/Search authority. Flutter is renderer / offline fallback.
БАДы retired with NO_CANONICAL_DESTINATION.
Licensed medicines remain OUT of catalog.
Package B Search filters: build_medical_v2_search_filters().
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

MED_KIND_KEY = "med_kind"
MED_KIND_LABEL = "Товар"
MED_SELLER_KEY = "seller_type"
MED_SELLER_LABEL = "Продавец"
MED_CONDITION_KEY = "condition"
MED_CONDITION_LABEL = "Состояние"

MEDICAL_ROOT_SLUG = "medical"
MEDICAL_ROOT_LABEL = "Медтовары"
MEDICAL_V2_ENTITY_TYPE = CategoryEntityType.object

# Soft-retired: legacy dual tree + БАДы (no auto-move destination).
MEDICAL_V2_LEGACY_RETIRED_SLUGS: frozenset[str] = frozenset(
    {
        "medical-devices",
        "medical-care",
    }
)
MEDICAL_V2_SUPPLEMENTS_SLUG = "medical-bady-i-tovary-dlya-zdorovya"
MEDICAL_V2_SUPPLEMENTS_STATUS = "RETIRED_NO_CANONICAL_DESTINATION"

# Canonical modern active L2 (15) — БАДы excluded.
MEDICAL_V2_CANONICAL_LEAVES: tuple[tuple[str, str, int], ...] = (
    ("Ортопедические товары", "medical-ortopedicheskie-tovary", 10),
    ("Реабилитационные товары", "medical-reabilitatsionnye-tovary", 20),
    ("Товары для ухода за больными", "medical-tovary-dlya-uhoda-za-bolnymi", 30),
    ("Медицинские приборы", "medical-meditsinskie-pribory", 40),
    ("Расходные мед материалы", "medical-rashodnye-med-materialy", 50),
    ("Средства индивид.ной защиты", "medical-sredstva-individ-noy-zaschity", 60),
    ("Медицинская одежда", "medical-meditsinskaya-odezhda", 70),
    ("Оптика и товары для зрения", "medical-optika-i-tovary-dlya-zreniya", 80),
    ("Товары для слуха", "medical-tovary-dlya-sluha", 90),
    ("Товары для диабетиков", "medical-tovary-dlya-diabetikov", 100),
    ("Ингаляторы/товары для дыхания", "medical-ingalyatory-tovary-dlya-dyhaniya", 110),
    ("Массаж и реабилитация", "medical-massazh-i-reabilitatsiya", 120),
    ("Медицинская мебель", "medical-meditsinskaya-mebel", 130),
    ("Аптечки и первая помощь", "medical-aptechki-i-pervaya-pomosch", 140),
    ("Прочие медтовары", "medical-prochie-medtovary", 160),
)
MEDICAL_V2_CANONICAL_SLUGS: frozenset[str] = frozenset(
    slug for _label, slug, _s in MEDICAL_V2_CANONICAL_LEAVES
)
MEDICAL_V2_RETIRED_SLUGS: frozenset[str] = (
    MEDICAL_V2_LEGACY_RETIRED_SLUGS | {MEDICAL_V2_SUPPLEMENTS_SLUG}
)
MEDICAL_V2_EXPECTED_L2_COUNT = len(MEDICAL_V2_CANONICAL_LEAVES)
MEDICAL_DEVICES_CANONICAL_SLUG = "medical-meditsinskie-pribory"
MEDICAL_DEVICES_CANONICAL_LABEL = "Медицинские приборы"

MEDICAL_SELLER_TARGET = GOODS_SELLER_CHOICES
MEDICAL_CONDITION_OPTIONS = ("Новое", "Б/у")

# Section key → kinds (active product catalog only).
MEDICAL_V2_SECTION_KINDS: dict[str, tuple[str, ...]] = {
    "ortho": (
        "Бандажи",
        "Корсеты",
        "Корректоры осанки",
        "Ортезы",
        "Вальгусные шины",
        "Ортопедические стельки",
        "Наколенники",
        "Ортопедические подушки",
        "Другие ортопедические товары",
    ),
    "rehab": (
        "Инвалидные коляски",
        "Медицинские ходунки",
        "Костыли",
        "Трости",
        "Роллаторы",
        "Другие реабилитационные товары",
    ),
    "care": (
        "Противопролежневые матрасы",
        "Подгузники для взрослых",
        "Впитывающие пелёнки",
        "Мочеприёмники",
        "Санитарные кресла",
        "Другие товары для ухода",
    ),
    "devices": (
        "Тонометры",
        "Градусники",
        "Пульсоксиметры",
        "Кварцевые лампы",
        "Бактерицидные рециркуляторы",
        "Алкотестеры",
        "Другие медицинские приборы",
    ),
    "consumables": (
        "Бинты и повязки",
        "Пластыри",
        "Шприцы",
        "Инфузионные системы",
        "Медицинские перчатки",
        "Другие расходные материалы",
    ),
    "ppe": (
        "Медицинские маски",
        "Медицинские шапочки",
        "Бахилы",
        "Защитные экраны",
        "Другие средства защиты",
    ),
    "clothing": (
        "Медицинские халаты",
        "Медицинские костюмы",
        "Медицинские колпаки",
        "Медицинская обувь",
        "Другая медицинская одежда",
    ),
    "optics": (
        "Очки для зрения",
        "Оправы",
        "Контактные линзы",
        "Растворы для линз",
        "Футляры для очков",
        "Другие товары для зрения",
    ),
    "hearing": (
        "Слуховые аппараты",
        "Батарейки для слуховых аппаратов",
        "Другие товары для слуха",
    ),
    "diabetes": (
        "Глюкометры",
        "Тест-полоски",
        "Ланцеты",
        "Другие товары для диабетиков",
    ),
    "breathing": (
        "Небулайзеры",
        "Кислородные концентраторы",
        "Кислородные подушки",
        "Другие товары для дыхания",
    ),
    "massage": (
        "Массажёры",
        "Массажные кресла",
        "Массажные столы",
        "Турмалиновые коврики",
        "Другие товары для массажа",
    ),
    "furniture": (
        "Медицинские кровати",
        "Каталки",
        "Процедурные столики",
        "Медицинские ширмы",
        "Медицинские шкафы",
        "Другая медицинская мебель",
    ),
    "firstaid": (
        "Автомобильные аптечки",
        "Домашние аптечки",
        "Кровоостанавливающие жгуты",
        "Шины для иммобилизации",
        "Другие товары первой помощи",
    ),
    "other": (
        "Грелки",
        "Пузыри для льда",
        "Другие медтовары",
    ),
}

MEDICAL_V2_SECTION_SLUGS: dict[str, str] = {
    "ortho": "medical-ortopedicheskie-tovary",
    "rehab": "medical-reabilitatsionnye-tovary",
    "care": "medical-tovary-dlya-uhoda-za-bolnymi",
    "devices": "medical-meditsinskie-pribory",
    "consumables": "medical-rashodnye-med-materialy",
    "ppe": "medical-sredstva-individ-noy-zaschity",
    "clothing": "medical-meditsinskaya-odezhda",
    "optics": "medical-optika-i-tovary-dlya-zreniya",
    "hearing": "medical-tovary-dlya-sluha",
    "diabetes": "medical-tovary-dlya-diabetikov",
    "breathing": "medical-ingalyatory-tovary-dlya-dyhaniya",
    "massage": "medical-massazh-i-reabilitatsiya",
    "furniture": "medical-meditsinskaya-mebel",
    "firstaid": "medical-aptechki-i-pervaya-pomosch",
    "other": "medical-prochie-medtovary",
}

# Retired supplements kinds (historical catalog; not active).
MEDICAL_V2_RETIRED_SUPPLEMENT_KINDS: frozenset[str] = frozenset(
    {
        "Витаминные комплексы",
        "Омега-3",
        "Коллаген",
        "Минеральные комплексы",
        "Другие БАДы",
    }
)

LICENSED_MEDICINES_BANNED: frozenset[str] = frozenset(
    {
        "Инсулин",
        "Антибиотики",
        "Лекарства",
        "Таблетки",
        "Обезболивающие",
        "Средства для похудения",
        "Антисептики",
        "Вакцины",
        "Сиропы",
        "Гормональные препараты",
    }
)

# ---------------------------------------------------------------------------
# Independent Condition matrix (positive allowlist / default-off for NO)
# Production Package A mapping must not self-prove this set.
# ---------------------------------------------------------------------------

ConditionDecision = Literal["YES", "NO"]

_INDEPENDENT_CONDITION_NO: frozenset[str] = frozenset(
    {
        # Care consumables / personal hygiene
        "Подгузники для взрослых",
        "Впитывающие пелёнки",
        "Мочеприёмники",
        # Consumables / sharps
        "Бинты и повязки",
        "Пластыри",
        "Шприцы",
        "Инфузионные системы",
        "Медицинские перчатки",
        "Другие расходные материалы",
        # Disposable PPE
        "Медицинские маски",
        "Медицинские шапочки",
        "Бахилы",
        # Medical clothing (Archi)
        "Медицинские халаты",
        "Медицинские костюмы",
        "Медицинские колпаки",
        "Медицинская обувь",
        "Другая медицинская одежда",
        # Optics consumables
        "Контактные линзы",
        "Растворы для линз",
        # Hearing consumables
        "Батарейки для слуховых аппаратов",
        # Diabetes consumables
        "Тест-полоски",
        "Ланцеты",
        # First-aid kits / assembled kits (Archi: whole section NO)
        "Автомобильные аптечки",
        "Домашние аптечки",
        "Кровоостанавливающие жгуты",
        "Шины для иммобилизации",
        "Другие товары первой помощи",
    }
)

# Ownership lock notes (cross-root).
MEDICAL_KEEPS_MASSAGE_CHAIRS = True  # locked Medical ownership this milestone
BE_CLINIC_KINDS_NOT_IN_MEDICAL: frozenset[str] = frozenset(
    {
        "Стоматологические установки",
        "Стерилизаторы",
        "Медицинские кушетки",
        "Аппараты УЗИ",
        "Другое медицинское оборудование",
    }
)
KIDS_KINDS_NOT_IN_MEDICAL: frozenset[str] = frozenset(
    {"Подгузники", "Ходунки", "Матрасы"}
)

MEDICAL_CREATE_FORBIDDEN: frozenset[str] = frozenset(
    {
        "brand",
        "model",
        "dosage",
        "expiry",
        "expiry_date",
        "quantity",
        "pack_size",
        "volume",
        "manufacturer",
        "country",
        "power",
        "accuracy",
        "range",
        "capacity",
        "dimensions",
        "weight",
        "voltage",
        "price_basis",
        "item_type",
    }
)

_ALWAYS_CREATE: frozenset[str] = frozenset(
    {
        MED_KIND_KEY,
        MED_SELLER_KEY,
        MED_CONDITION_KEY,
        "price",
        "negotiable",
        "contact_methods",
    }
)

# Package B Search — explicit allowlist (Create ≠ Search).
# Geo is shared Search UX (region/city), not CategoryFilter rows.
MEDICAL_V2_SEARCH_ALLOWLIST: frozenset[str] = frozenset(
    {
        MED_KIND_KEY,
        MED_CONDITION_KEY,
        MED_SELLER_KEY,
        "geo",
    }
)

MEDICAL_V2_SEARCH_EAV_KEYS: frozenset[str] = frozenset(
    {
        MED_KIND_KEY,
        MED_CONDITION_KEY,
        MED_SELLER_KEY,
    }
)

MEDICAL_V2_SEARCH_EXCLUDE: frozenset[str] = frozenset(
    set(MEDICAL_CREATE_FORBIDDEN)
    | {
        "price",
        "negotiable",
        "contact_methods",
        "price_basis",
        "currency",
        "brand",
        "model",
        "dosage",
        "expiry",
        "expiry_date",
        "quantity",
        "pack_size",
        "volume",
        "manufacturer",
        "country",
        "power",
        "voltage",
        "accuracy",
        "range",
        "capacity",
        "dimensions",
        "weight",
    }
)

MEDICAL_V2_SEARCH_POLICY_PREP: frozenset[str] = MEDICAL_V2_SEARCH_ALLOWLIST

# Forensic Package A legacy incomplete listing (KEEP; no backfill).
MEDICAL_LEGACY_INCOMPLETE_LISTING_ID = 3154


def medical_v2_all_kinds() -> list[str]:
    out: list[str] = []
    for kinds in MEDICAL_V2_SECTION_KINDS.values():
        out.extend(kinds)
    return out


def medical_v2_kind_count() -> int:
    return len(medical_v2_all_kinds())


def medical_v2_condition_decision(kind: str) -> ConditionDecision:
    if kind in _INDEPENDENT_CONDITION_NO:
        return "NO"
    return "YES"


def medical_v2_condition_yes_kinds() -> frozenset[str]:
    return frozenset(
        k for k in medical_v2_all_kinds() if medical_v2_condition_decision(k) == "YES"
    )


def medical_v2_condition_no_kinds() -> frozenset[str]:
    return frozenset(
        k for k in medical_v2_all_kinds() if medical_v2_condition_decision(k) == "NO"
    )


def medical_v2_assert_cleanup_contracts() -> None:
    if MEDICAL_V2_EXPECTED_L2_COUNT != 15:
        raise RuntimeError(
            f"Medical V2 expects 15 active L2, got {MEDICAL_V2_EXPECTED_L2_COUNT}"
        )
    if set(MEDICAL_V2_SECTION_SLUGS.values()) != MEDICAL_V2_CANONICAL_SLUGS:
        raise RuntimeError("Medical section slugs ≠ canonical L2 set")
    if MEDICAL_V2_SUPPLEMENTS_SLUG in MEDICAL_V2_CANONICAL_SLUGS:
        raise RuntimeError("БАДы must not be active canonical L2")
    if MEDICAL_V2_LEGACY_RETIRED_SLUGS & MEDICAL_V2_CANONICAL_SLUGS:
        raise RuntimeError("Legacy retired slugs overlap canonical")
    kinds = medical_v2_all_kinds()
    if len(kinds) != len(set(kinds)):
        raise RuntimeError("Medical kind catalog has duplicates")
    if MEDICAL_V2_RETIRED_SUPPLEMENT_KINDS & set(kinds):
        raise RuntimeError("Retired БАДы kinds leaked into active catalog")
    if LICENSED_MEDICINES_BANNED & set(kinds):
        raise RuntimeError("Licensed medicines leaked into Medical kinds")
    if BE_CLINIC_KINDS_NOT_IN_MEDICAL & set(kinds):
        raise RuntimeError("BE clinic kinds duplicated into Medical")
    if KIDS_KINDS_NOT_IN_MEDICAL & set(kinds):
        raise RuntimeError("Kids-owned kinds leaked into Medical")
    devices = [
        slug
        for label, slug, _s in MEDICAL_V2_CANONICAL_LEAVES
        if label == MEDICAL_DEVICES_CANONICAL_LABEL
    ]
    if devices != [MEDICAL_DEVICES_CANONICAL_SLUG]:
        raise RuntimeError(f"Medical Devices must be unique: {devices}")
    yes = medical_v2_condition_yes_kinds()
    no = medical_v2_condition_no_kinds()
    if yes | no != set(kinds):
        raise RuntimeError("Condition matrix incomplete")
    if yes & no:
        raise RuntimeError("Condition YES/NO overlap")
    if no != _INDEPENDENT_CONDITION_NO:
        raise RuntimeError(
            "Condition NO drifted from independent allowlist: "
            f"extra={sorted(no - _INDEPENDENT_CONDITION_NO)} "
            f"missing={sorted(_INDEPENDENT_CONDITION_NO - no)}"
        )
    if set(MEDICAL_SELLER_TARGET) != {"Частное лицо", "Магазин", "Другой"}:
        raise RuntimeError("Medical seller must be canonical goods trio")
    if "Аптека" in MEDICAL_SELLER_TARGET or "Компания" in MEDICAL_SELLER_TARGET:
        raise RuntimeError("Аптека/Компания forbidden in Medical seller target")
    # Clothing + firstaid must be entirely NO
    for kind in MEDICAL_V2_SECTION_KINDS["clothing"]:
        if medical_v2_condition_decision(kind) != "NO":
            raise RuntimeError(f"Medical clothing must be Condition NO: {kind}")
    for kind in MEDICAL_V2_SECTION_KINDS["firstaid"]:
        if medical_v2_condition_decision(kind) != "NO":
            raise RuntimeError(f"First-aid kits must be Condition NO: {kind}")
    for kind in ("Шприцы", "Медицинские перчатки", "Бинты и повязки"):
        if medical_v2_condition_decision(kind) != "NO":
            raise RuntimeError(f"Consumable/sharps must be Condition NO: {kind}")
    for kind in ("Очки для зрения", "Оправы", "Тонометры", "Глюкометры", "Массажные кресла"):
        if medical_v2_condition_decision(kind) != "YES":
            raise RuntimeError(f"Durable kind must be Condition YES: {kind}")
    if not MEDICAL_KEEPS_MASSAGE_CHAIRS:
        raise RuntimeError("Massage chairs ownership lock broken")


def _item(label: str) -> dict[str, Any]:
    return {"value": label, "label": label}


def build_medical_v2_section_catalog(section_key: str) -> dict[str, Any] | None:
    """Active Medical section catalog for API / Flutter mirror (pre-Package A)."""
    if section_key not in MEDICAL_V2_SECTION_KINDS:
        return None
    medical_v2_assert_cleanup_contracts()
    kinds = MEDICAL_V2_SECTION_KINDS[section_key]
    slug = MEDICAL_V2_SECTION_SLUGS[section_key]
    label = next(lbl for lbl, s, _ in MEDICAL_V2_CANONICAL_LEAVES if s == slug)
    filters: list[dict[str, Any]] = [
        {
            "label": "Продавец",
            "options": [_item(x) for x in MEDICAL_SELLER_TARGET],
        }
    ]
    yes_in_section = [k for k in kinds if medical_v2_condition_decision(k) == "YES"]
    if yes_in_section:
        filters.append(
            {
                "label": "Состояние",
                "applies_to": list(yes_in_section),
                "options": [_item(x) for x in MEDICAL_CONDITION_OPTIONS],
            }
        )
    return {
        "category_slug": slug,
        "label": label,
        "question": "Какой товар?",
        "roles": [_item(k) for k in kinds],
        "filters": filters,
    }


def build_all_medical_v2_section_catalogs() -> dict[str, dict[str, Any]]:
    medical_v2_assert_cleanup_contracts()
    out: dict[str, dict[str, Any]] = {}
    for key in MEDICAL_V2_SECTION_KINDS:
        cat = build_medical_v2_section_catalog(key)
        assert cat is not None
        out[key] = cat
    return out


def medical_v2_condition_visible_for_kind(kind: str) -> bool:
    return medical_v2_condition_decision(kind) == "YES"


def medical_v2_condition_matrix() -> dict[str, ConditionDecision]:
    return {k: medical_v2_condition_decision(k) for k in medical_v2_all_kinds()}


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


def medical_v2_assert_package_a_contracts() -> None:
    medical_v2_assert_cleanup_contracts()
    if medical_v2_kind_count() != 80:
        raise RuntimeError(
            f"Medical Package A expects 80 kinds, got {medical_v2_kind_count()}"
        )
    if MEDICAL_SELLER_TARGET != GOODS_SELLER_CHOICES:
        raise RuntimeError("Medical seller must match goods shared seller")
    yes = medical_v2_condition_yes_kinds()
    no = medical_v2_condition_no_kinds()
    if len(yes) != 53 or len(no) != 27:
        raise RuntimeError(
            f"Condition matrix drift: yes={len(yes)} no={len(no)} (expected 53/27)"
        )
    if no != _INDEPENDENT_CONDITION_NO:
        raise RuntimeError("Condition NO drifted from independent allowlist")
    if MEDICAL_V2_SUPPLEMENTS_STATUS != "RETIRED_NO_CANONICAL_DESTINATION":
        raise RuntimeError("БАДы destination status lock broken")


def build_medical_v2_core_fields() -> dict[str, list]:
    """Create cores for all 15 active Medical L2 (Package A SoT)."""
    medical_v2_assert_package_a_contracts()
    cond_approved = medical_v2_condition_yes_kinds()
    out: dict[str, list] = {}

    for section_key, slug in MEDICAL_V2_SECTION_SLUGS.items():
        kinds = list(MEDICAL_V2_SECTION_KINDS[section_key])
        fields: list = [
            _dep_field(
                MED_KIND_KEY,
                MED_KIND_LABEL,
                CategoryFieldType.enum,
                True,
                10,
                _choices(*kinds),
                hint="Какой товар?",
            ),
            _dep_field(
                MED_SELLER_KEY,
                MED_SELLER_LABEL,
                CategoryFieldType.enum,
                True,
                20,
                _choices(*MEDICAL_SELLER_TARGET),
            ),
        ]

        cond_kinds = [k for k in kinds if k in cond_approved]
        if cond_kinds:
            cond_opts: dict[str, Any] = _choices(*MEDICAL_CONDITION_OPTIONS)
            if set(cond_kinds) != set(kinds):
                cond_opts["depends_on"] = {
                    "field": MED_KIND_KEY,
                    "values": list(cond_kinds),
                }
            fields.append(
                _dep_field(
                    MED_CONDITION_KEY,
                    MED_CONDITION_LABEL,
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
            if key in MEDICAL_CREATE_FORBIDDEN:
                raise RuntimeError(f"forbidden Create field {slug}.{key}")
            if key not in _ALWAYS_CREATE:
                raise RuntimeError(f"unapproved Create field {slug}.{key}")
            opts = row[5]
            if opts and opts.get("choices") is not None and len(opts["choices"]) == 0:
                raise RuntimeError(f"empty picker {slug}.{key}")

        out[slug] = fields
    return out


def medical_v2_all_kind_audit() -> list[dict[str, Any]]:
    """All-80 kind audit rows (Package A). Pair with independent expectations."""
    cores = build_medical_v2_core_fields()
    rows: list[dict[str, Any]] = []
    for section_key, slug in MEDICAL_V2_SECTION_SLUGS.items():
        kinds = MEDICAL_V2_SECTION_KINDS[section_key]
        fields = cores[slug]
        keys = [r[0] for r in fields]
        kind_row = next(r for r in fields if r[0] == MED_KIND_KEY)
        kind_opts = [c["value"] for c in kind_row[5]["choices"]]
        seller_row = next(r for r in fields if r[0] == MED_SELLER_KEY)
        seller_opts = [c["value"] for c in seller_row[5]["choices"]]
        cond_row = next((r for r in fields if r[0] == MED_CONDITION_KEY), None)
        cond_values: set[str] = set()
        if cond_row is not None:
            dep = (cond_row[5] or {}).get("depends_on") or {}
            if dep.get("values"):
                cond_values = set(dep["values"])
            else:
                cond_values = set(kind_opts)

        specials = [
            k
            for k in keys
            if k
            not in {
                MED_KIND_KEY,
                MED_SELLER_KEY,
                "price",
                "negotiable",
                "contact_methods",
            }
        ]

        for kind in kinds:
            cond_yes = medical_v2_condition_visible_for_kind(kind)
            kind_specials = list(specials)
            if not cond_yes:
                kind_specials = [k for k in kind_specials if k != MED_CONDITION_KEY]
            ownership = "MEDICAL"
            if kind in BE_CLINIC_KINDS_NOT_IN_MEDICAL:
                ownership = "BUSINESS_EQUIPMENT"
            elif kind in KIDS_KINDS_NOT_IN_MEDICAL:
                ownership = "KIDS"
            rows.append(
                {
                    "kind": kind,
                    "section": section_key,
                    "slug": slug,
                    "med_kind_valid": kind in kind_opts,
                    "condition": "YES" if cond_yes else "NO",
                    "condition_in_schema": cond_yes == (kind in cond_values),
                    "seller": seller_opts,
                    "price": "price" in keys,
                    "special_count": len(kind_specials),
                    "forbidden": sorted(set(keys) & MEDICAL_CREATE_FORBIDDEN),
                    "components": {
                        MED_KIND_KEY: "enum",
                        "price": "price",
                        MED_SELLER_KEY: "enum",
                        "contact_methods": "enum",
                    },
                    "ownership": ownership,
                }
            )
    return rows


def medical_v2_complexity_histogram() -> dict[str, int]:
    """special_count histogram excluding kind/shared base (condition only)."""
    hist = {"0": 0, "1": 0, "2": 0, "3+": 0}
    for row in medical_v2_all_kind_audit():
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


def medical_v2_section_kinds(slug: str) -> list[str]:
    for section_key, section_slug in MEDICAL_V2_SECTION_SLUGS.items():
        if section_slug != slug:
            continue
        return list(MEDICAL_V2_SECTION_KINDS[section_key])
    raise KeyError(f"Unknown Medical L2 slug: {slug}")


def _search_filter(
    key: str,
    label: str,
    ftype: CategoryFilterType,
    sort: int,
    config: dict[str, Any] | None,
) -> tuple:
    return (key, label, ftype, sort, config)


def build_medical_v2_search_filters() -> dict[str, list]:
    """Package B Search SoT per canonical Medical L2.

    Explicit allowlist only. Condition inherits Package A depends_on
    from Create cores (Create↔Search parity). Price / negotiable / contacts /
    brand / dosage / tech never Search. Geo is shared Search UX, not
    CategoryFilter rows. Medicines / БАДы never appear.
    """
    cores = build_medical_v2_core_fields()
    out: dict[str, list] = {}
    for slug, fields in cores.items():
        filters: list = []
        for key, label, _ftype, _required, sort, options, _hint in fields:
            if key not in MEDICAL_V2_SEARCH_EAV_KEYS:
                continue
            if key in MEDICAL_V2_SEARCH_EXCLUDE:
                continue
            if key not in MEDICAL_V2_SEARCH_ALLOWLIST:
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
    if set(out) != MEDICAL_V2_CANONICAL_SLUGS:
        raise RuntimeError(
            "Medical Search filter map != canonical L2 slugs: "
            f"extra={sorted(set(out) - MEDICAL_V2_CANONICAL_SLUGS)} "
            f"missing={sorted(MEDICAL_V2_CANONICAL_SLUGS - set(out))}"
        )
    return out


def medical_v2_search_kind_audit_row(
    section_key: str, slug: str, kind: str
) -> dict[str, Any]:
    """All-kind Search audit row (independent of Create visible_components)."""
    cond_yes = medical_v2_condition_visible_for_kind(kind)
    ownership = "MEDICAL"
    if kind in BE_CLINIC_KINDS_NOT_IN_MEDICAL:
        ownership = "BUSINESS_EQUIPMENT"
    elif kind in KIDS_KINDS_NOT_IN_MEDICAL:
        ownership = "KIDS"
    elif kind in MEDICAL_V2_RETIRED_SUPPLEMENT_KINDS:
        ownership = "RETIRED_SUPPLEMENT"
    elif kind in LICENSED_MEDICINES_BANNED:
        ownership = "MEDICINES_BANNED"
    visible = [MED_KIND_KEY, MED_SELLER_KEY]
    if cond_yes:
        visible.append(MED_CONDITION_KEY)
    return {
        "l2": slug,
        "section": section_key,
        "kind": kind,
        "search_med_kind": "YES",
        "search_seller": "YES",
        "search_condition": "YES" if cond_yes else "NO",
        "search_brand": "NO",
        "search_model": "NO",
        "search_dosage": "NO",
        "search_expiry": "NO",
        "search_quantity": "NO",
        "search_power": "NO",
        "search_voltage": "NO",
        "search_price": "NO",
        "search_negotiable": "NO",
        "search_contacts": "NO",
        "search_geo": "YES",
        "retired_resurrected": slug in MEDICAL_V2_RETIRED_SLUGS,
        "ownership": ownership,
        "visible_search_keys": visible,
        "ui_components": {
            MED_KIND_KEY: "multi_select",
            MED_SELLER_KEY: "multi_select",
            **({MED_CONDITION_KEY: "multi_select"} if cond_yes else {}),
            "geo": "region_city",
        },
    }


def medical_v2_all_search_kind_audit() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for section_key, slug in MEDICAL_V2_SECTION_SLUGS.items():
        for kind in MEDICAL_V2_SECTION_KINDS[section_key]:
            rows.append(
                medical_v2_search_kind_audit_row(section_key, slug, kind)
            )
    return rows


def medical_v2_search_policy_prep() -> dict[str, Any]:
    return {
        "allow": sorted(MEDICAL_V2_SEARCH_ALLOWLIST),
        "eav": sorted(MEDICAL_V2_SEARCH_EAV_KEYS),
        "exclude": sorted(MEDICAL_V2_SEARCH_EXCLUDE),
    }


def medical_v2_assert_package_b_contracts() -> None:
    medical_v2_assert_package_a_contracts()
    filters = build_medical_v2_search_filters()
    if set(filters) != MEDICAL_V2_CANONICAL_SLUGS:
        raise RuntimeError("Package B Search map ≠ canonical L2")
    if MEDICAL_V2_SUPPLEMENTS_SLUG in filters:
        raise RuntimeError("БАДы must not appear in Search filter map")
    if MEDICAL_V2_LEGACY_RETIRED_SLUGS & set(filters):
        raise RuntimeError("Legacy dual tree must not appear in Search")
    for slug, rows in filters.items():
        keys = {r[0] for r in rows}
        if keys - MEDICAL_V2_SEARCH_EAV_KEYS:
            raise RuntimeError(f"Search keys outside EAV allowlist: {slug}")
        if MED_KIND_KEY not in keys or MED_SELLER_KEY not in keys:
            raise RuntimeError(f"Search missing kind/seller: {slug}")
        if keys & MEDICAL_CREATE_FORBIDDEN:
            raise RuntimeError(f"Forbidden Search keys: {slug}")
        if keys & {"price", "negotiable", "contact_methods", "brand", "dosage"}:
            raise RuntimeError(f"Create-only/forbidden leaked into Search: {slug}")
    audit = medical_v2_all_search_kind_audit()
    if len(audit) != 80:
        raise RuntimeError(f"Search audit expects 80 kinds, got {len(audit)}")
    yes = sum(1 for r in audit if r["search_condition"] == "YES")
    no = sum(1 for r in audit if r["search_condition"] == "NO")
    if yes != 53 or no != 27:
        raise RuntimeError(f"Search Condition drift: yes={yes} no={no}")
