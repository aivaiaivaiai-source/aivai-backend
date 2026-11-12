# -*- coding: utf-8 -*-
"""Business Equipment V2 — taxonomy + Package A Create SoT.

Backend/API is Create authority. Flutter is renderer / offline fallback.
Does NOT seed Package B Search filters.
"""
from __future__ import annotations

from typing import Any, Literal

from app.models.category_enums import (
    CategoryEntityType,
    CategoryFieldType,
    CategoryFilterType,
)
from app.seeds.business_sections_catalog import BUSINESS_SECTIONS
from app.seeds.shared_goods_create_contract import (
    CONTACT_METHOD_CHOICES,
    GOODS_NEGOTIABLE_CHOICES,
    GOODS_SELLER_CHOICES,
)

BUSINESS_EQUIPMENT_ROOT_SLUG = "business-equipment"
BUSINESS_EQUIPMENT_ROOT_LABEL = "Бизнес-оборудование"
BUSINESS_EQUIPMENT_V2_ENTITY_TYPE = CategoryEntityType.equipment

BUSINESS_KIND_KEY = "business_kind"
BUSINESS_KIND_LABEL = "Товар"
BUSINESS_SELLER_KEY = "seller_type"
BUSINESS_SELLER_LABEL = "Продавец"
BUSINESS_CONDITION_KEY = "condition"
BUSINESS_CONDITION_LABEL = "Состояние"

# Package A seller — canonical goods (no Компания).
BUSINESS_EQUIPMENT_SELLER_TARGET: tuple[str, ...] = GOODS_SELLER_CHOICES
BUSINESS_EQUIPMENT_CONDITION_CHOICES: tuple[str, ...] = ("Новое", "Б/у")

# Structured Create forbid-list (Package A → Description only).
BUSINESS_EQUIPMENT_CREATE_FORBIDDEN: frozenset[str] = frozenset(
    {
        "brand",
        "model",
        "power",
        "power_kw",
        "watt",
        "voltage",
        "capacity",
        "throughput",
        "productivity",
        "width",
        "height",
        "depth",
        "length",
        "diameter",
        "weight",
        "material",
        "year",
        "country",
        "manufacturer",
        "warranty",
        "quantity",
        "technical_condition",
        "price_basis",
        "unit_price",
    }
)

_ALWAYS_CREATE: frozenset[str] = frozenset(
    {
        BUSINESS_KIND_KEY,
        BUSINESS_SELLER_KEY,
        BUSINESS_CONDITION_KEY,
        "price",
        "negotiable",
        "contact_methods",
    }
)

# Package B Search — explicit allowlist (Create ≠ Search).
# Geo is shared Search UX (region/city), not CategoryFilter rows.
BUSINESS_EQUIPMENT_V2_SEARCH_ALLOWLIST: frozenset[str] = frozenset(
    {
        BUSINESS_KIND_KEY,
        BUSINESS_CONDITION_KEY,
        BUSINESS_SELLER_KEY,
        "geo",
    }
)

BUSINESS_EQUIPMENT_V2_SEARCH_EAV_KEYS: frozenset[str] = frozenset(
    {
        BUSINESS_KIND_KEY,
        BUSINESS_CONDITION_KEY,
        BUSINESS_SELLER_KEY,
    }
)

BUSINESS_EQUIPMENT_V2_SEARCH_EXCLUDE: frozenset[str] = frozenset(
    set(BUSINESS_EQUIPMENT_CREATE_FORBIDDEN)
    | {
        "price",
        "negotiable",
        "contact_methods",
        "price_basis",
        "currency",
        "brand",
        "model",
        "electronics_brand",
        "electronics_model",
    }
)

BUSINESS_EQUIPMENT_V2_SEARCH_POLICY_PREP: frozenset[str] = (
    BUSINESS_EQUIPMENT_V2_SEARCH_ALLOWLIST
)

BUSINESS_EQUIPMENT_V2_SECTION_SLUGS: dict[str, str] = {
    key: str(sec["category_slug"]) for key, sec in BUSINESS_SECTIONS.items()
}

BUSINESS_EQUIPMENT_V2_LEGACY_RETIRED_SLUGS: frozenset[str] = frozenset(
    {
        "business-equipment-cafe",
        "business-equipment-retail",
        "business-equipment-industrial",
    }
)

# Canonical modern 20 L2 from BUSINESS_SECTIONS (sort mirrors skeleton).
BUSINESS_EQUIPMENT_V2_CANONICAL_LEAVES: tuple[tuple[str, str, int], ...] = tuple(
    (sec["label"], sec["category_slug"], (i + 1) * 10)
    for i, sec in enumerate(BUSINESS_SECTIONS.values())
)
BUSINESS_EQUIPMENT_V2_CANONICAL_SLUGS: frozenset[str] = frozenset(
    slug for _label, slug, _sort in BUSINESS_EQUIPMENT_V2_CANONICAL_LEAVES
)
BUSINESS_EQUIPMENT_V2_RETIRED_SLUGS: frozenset[str] = (
    BUSINESS_EQUIPMENT_V2_LEGACY_RETIRED_SLUGS
)
BUSINESS_EQUIPMENT_V2_EXPECTED_L2_COUNT = len(BUSINESS_EQUIPMENT_V2_CANONICAL_LEAVES)

TRADE_CANONICAL_SLUG = "business-equipment-torgovoe-oborudovanie"
TRADE_CANONICAL_LABEL = "Торговое оборудование"
PLOTTER_KIND = "Плоттеры"
STO_COMPRESSOR_KIND = "Компрессоры для СТО"
REPAIR_GENERIC_COMPRESSOR_KIND = "Компрессоры"

# Food tara goods must never become BE ownership destinations.
FOOD_TARA_GOODS_NOT_BUSINESS_EQUIPMENT: frozenset[str] = frozenset(
    {
        "Стеклянные банки",
        "Крышки",
        "Пластиковые бутылки",
        "Мешки",
        "Ящики",
        "Контейнеры",
        "Пакеты",
        "Плёнка упаковочная",
    }
)
BUSINESS_PACKING_IS_EQUIPMENT_NOT_TARA = (
    "business-equipment-upakovka-i-markirovka owns packing *machines*, "
    "not jars/bags/lids/containers (Food Tara GAP remains open)."
)

# ---------------------------------------------------------------------------
# Platform coherence — explicit ownership locks (audit + Archi decisions)
# ---------------------------------------------------------------------------

Ownership = Literal[
    "BUSINESS_EQUIPMENT",
    "ELECTRONICS",
    "REPAIR",
    "FOOD_AGRI",
    "MATERIALS",
    "TRANSPORT",
    "SERVICES",
    "HOME_GARDEN",
    "MEDICAL",
    "BEAUTY",
    "ANIMALS",
]

BUSINESS_EQUIPMENT_ELECTRONICS_BOUNDARY: dict[str, Ownership] = {
    "Принтеры": "ELECTRONICS",
    "Сканеры": "ELECTRONICS",
    "МФУ": "ELECTRONICS",
    "Мониторы": "ELECTRONICS",
    "ИБП": "ELECTRONICS",
    "Холодильники": "ELECTRONICS",
    "Встраиваемые холодильники": "ELECTRONICS",
    "Бытовые швейные машины": "ELECTRONICS",
    "Напольные весы": "ELECTRONICS",
    "Чековые принтеры": "BUSINESS_EQUIPMENT",
    "Принтеры этикеток": "BUSINESS_EQUIPMENT",
    "Сканеры штрихкода": "BUSINESS_EQUIPMENT",
    "Онлайн-кассы": "BUSINESS_EQUIPMENT",
    "Плоттеры": "BUSINESS_EQUIPMENT",
    "Холодильные витрины": "BUSINESS_EQUIPMENT",
}

BUSINESS_EQUIPMENT_REPAIR_BOUNDARY: dict[str, Ownership] = {
    "Генераторы": "REPAIR",
    "Бетономешалки": "REPAIR",
    "Сварочные аппараты": "REPAIR",
    REPAIR_GENERIC_COMPRESSOR_KIND: "REPAIR",
    STO_COMPRESSOR_KIND: "BUSINESS_EQUIPMENT",
}

BUSINESS_EQUIPMENT_MEDICAL_BOUNDARY: dict[str, Ownership] = {
    "Стоматологические установки": "BUSINESS_EQUIPMENT",
    "Стерилизаторы": "BUSINESS_EQUIPMENT",
    "Медицинские кушетки": "BUSINESS_EQUIPMENT",
    "Аппараты УЗИ": "BUSINESS_EQUIPMENT",
    "Другое медицинское оборудование": "BUSINESS_EQUIPMENT",
    "Медицинские кровати": "MEDICAL",
    "Каталки": "MEDICAL",
    "Процедурные столики": "MEDICAL",
    "Медицинские ширмы": "MEDICAL",
    "Медицинские шкафы": "MEDICAL",
}

BUSINESS_EQUIPMENT_BEAUTY_BOUNDARY: dict[str, Ownership] = {
    "Парикмахерские кресла": "BUSINESS_EQUIPMENT",
    "Мойки для салонов": "BUSINESS_EQUIPMENT",
    "Маникюрные столы": "BUSINESS_EQUIPMENT",
    "Фены": "BEAUTY",
    "Лампы для маникюра": "BEAUTY",
    "Аппараты для маникюра": "BEAUTY",
}

# ---------------------------------------------------------------------------
# Condition matrix — independent expectations (not self-proven by production)
# ---------------------------------------------------------------------------

ConditionDecision = Literal["YES", "NO"]

# Positive allowlist of Condition-NO kinds (consumable / trivial accessories).
# All other modern catalog kinds default YES (durable equipment / parts).
_INDEPENDENT_CONDITION_NO: frozenset[str] = frozenset(
    {
        "Ценникодержатели",
        "Крючки для торгового оборудования",
        "Подставки для украшений",
        "Иглы промышленные",
    }
)


def business_equipment_v2_all_kinds() -> tuple[str, ...]:
    out: list[str] = []
    for sec in BUSINESS_SECTIONS.values():
        for role in sec["roles"]:
            out.append(role["label"])
    return tuple(out)


def business_equipment_v2_kind_count() -> int:
    return len(business_equipment_v2_all_kinds())


def business_equipment_v2_condition_decision(kind: str) -> ConditionDecision:
    if kind in _INDEPENDENT_CONDITION_NO:
        return "NO"
    return "YES"


def business_equipment_v2_condition_visible_for_kind(kind: str) -> bool:
    return business_equipment_v2_condition_decision(kind) == "YES"


def business_equipment_v2_condition_yes_kinds() -> frozenset[str]:
    return frozenset(
        k
        for k in business_equipment_v2_all_kinds()
        if business_equipment_v2_condition_decision(k) == "YES"
    )


def business_equipment_v2_condition_no_kinds() -> frozenset[str]:
    return frozenset(
        k
        for k in business_equipment_v2_all_kinds()
        if business_equipment_v2_condition_decision(k) == "NO"
    )


def business_equipment_v2_condition_matrix() -> dict[str, ConditionDecision]:
    return {
        k: business_equipment_v2_condition_decision(k)
        for k in business_equipment_v2_all_kinds()
    }


def business_equipment_v2_assert_cleanup_contracts() -> None:
    if BUSINESS_EQUIPMENT_V2_EXPECTED_L2_COUNT != 20:
        raise RuntimeError(
            f"Business Equipment V2 expects 20 L2, got {BUSINESS_EQUIPMENT_V2_EXPECTED_L2_COUNT}"
        )
    if business_equipment_v2_kind_count() != 176:
        raise RuntimeError(
            f"Business Equipment V2 expects 176 kinds, got {business_equipment_v2_kind_count()}"
        )
    if len(set(business_equipment_v2_all_kinds())) != 176:
        raise RuntimeError("Business Equipment V2 kind catalog has duplicates")
    trade = [
        slug
        for _label, slug, _s in BUSINESS_EQUIPMENT_V2_CANONICAL_LEAVES
        if _label == TRADE_CANONICAL_LABEL
    ]
    if trade != [TRADE_CANONICAL_SLUG]:
        raise RuntimeError(f"Trade direction must be unique: {trade}")
    if TRADE_CANONICAL_SLUG in BUSINESS_EQUIPMENT_V2_RETIRED_SLUGS:
        raise RuntimeError("Canonical Trade slug must not be retired")
    if BUSINESS_EQUIPMENT_V2_LEGACY_RETIRED_SLUGS & BUSINESS_EQUIPMENT_V2_CANONICAL_SLUGS:
        raise RuntimeError("Legacy retired slugs overlap canonical modern L2")
    if PLOTTER_KIND not in business_equipment_v2_all_kinds():
        raise RuntimeError("Plotters kind missing from modern catalog")
    print_sec = BUSINESS_SECTIONS["print"]
    if PLOTTER_KIND not in {r["label"] for r in print_sec["roles"]}:
        raise RuntimeError("Plotters must live under Полиграфическое оборудование")
    if STO_COMPRESSOR_KIND not in business_equipment_v2_all_kinds():
        raise RuntimeError("STO compressor kind missing")
    if REPAIR_GENERIC_COMPRESSOR_KIND in business_equipment_v2_all_kinds():
        raise RuntimeError("Generic Компрессоры must not live in Business Equipment")
    tara_hits = FOOD_TARA_GOODS_NOT_BUSINESS_EQUIPMENT & set(
        business_equipment_v2_all_kinds()
    )
    if tara_hits:
        raise RuntimeError(f"Tara goods leaked into BE kinds: {sorted(tara_hits)}")
    yes = business_equipment_v2_condition_yes_kinds()
    no = business_equipment_v2_condition_no_kinds()
    if yes | no != set(business_equipment_v2_all_kinds()):
        raise RuntimeError("Condition matrix incomplete")
    if yes & no:
        raise RuntimeError("Condition matrix YES/NO overlap")
    if no != _INDEPENDENT_CONDITION_NO:
        raise RuntimeError("Condition NO set drifted from independent allowlist")
    if set(BUSINESS_EQUIPMENT_SELLER_TARGET) != {
        "Частное лицо",
        "Магазин",
        "Другой",
    }:
        raise RuntimeError("Seller target must be canonical goods trio")
    if "Компания" in BUSINESS_EQUIPMENT_SELLER_TARGET:
        raise RuntimeError("Компания forbidden in seller target")


def business_equipment_v2_assert_platform_coherence() -> None:
    business_equipment_v2_assert_cleanup_contracts()
    if BUSINESS_EQUIPMENT_ELECTRONICS_BOUNDARY["Плоттеры"] != "BUSINESS_EQUIPMENT":
        raise RuntimeError("Plotters must be Business Equipment")
    if BUSINESS_EQUIPMENT_REPAIR_BOUNDARY[STO_COMPRESSOR_KIND] != "BUSINESS_EQUIPMENT":
        raise RuntimeError("STO compressors must be Business Equipment")
    if (
        BUSINESS_EQUIPMENT_REPAIR_BOUNDARY[REPAIR_GENERIC_COMPRESSOR_KIND]
        != "REPAIR"
    ):
        raise RuntimeError("Generic compressors must be Repair")
    for kind, owner in BUSINESS_EQUIPMENT_MEDICAL_BOUNDARY.items():
        if owner == "BUSINESS_EQUIPMENT" and kind not in set(
            business_equipment_v2_all_kinds()
        ):
            raise RuntimeError(f"Medical BE kind missing from catalog: {kind}")
    # Packaging L2 must remain machines-only (Tara GAP stays open).
    packing_kinds = {r["label"] for r in BUSINESS_SECTIONS["packing"]["roles"]}
    if packing_kinds & FOOD_TARA_GOODS_NOT_BUSINESS_EQUIPMENT:
        raise RuntimeError("Packing L2 contains tara goods")


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


def business_equipment_v2_assert_package_a_contracts() -> None:
    business_equipment_v2_assert_cleanup_contracts()
    business_equipment_v2_assert_platform_coherence()
    if set(BUSINESS_EQUIPMENT_V2_SECTION_SLUGS.values()) != (
        BUSINESS_EQUIPMENT_V2_CANONICAL_SLUGS
    ):
        raise RuntimeError("SECTION_SLUGS ≠ canonical L2 set")
    if BUSINESS_EQUIPMENT_SELLER_TARGET != GOODS_SELLER_CHOICES:
        raise RuntimeError("BE seller must match goods shared seller")
    if "Компания" in BUSINESS_EQUIPMENT_SELLER_TARGET:
        raise RuntimeError("Компания forbidden in BE seller")
    yes = business_equipment_v2_condition_yes_kinds()
    no = business_equipment_v2_condition_no_kinds()
    if len(yes) + len(no) != 176:
        raise RuntimeError(
            f"Condition matrix size drift: yes={len(yes)} no={len(no)}"
        )
    if no != _INDEPENDENT_CONDITION_NO:
        raise RuntimeError("Condition NO drifted from independent allowlist")


def build_business_equipment_v2_core_fields() -> dict[str, list]:
    """Create cores for all 20 active Business Equipment L2 (Package A SoT)."""
    business_equipment_v2_assert_package_a_contracts()
    cond_approved = business_equipment_v2_condition_yes_kinds()
    out: dict[str, list] = {}

    for section_key, slug in BUSINESS_EQUIPMENT_V2_SECTION_SLUGS.items():
        catalog = BUSINESS_SECTIONS[section_key]
        kinds = [str(r["label"]) for r in catalog["roles"]]
        fields: list = [
            _dep_field(
                BUSINESS_KIND_KEY,
                BUSINESS_KIND_LABEL,
                CategoryFieldType.enum,
                True,
                10,
                _choices(*kinds),
                hint=str(catalog.get("question") or "Какой товар?"),
            ),
            _dep_field(
                BUSINESS_SELLER_KEY,
                BUSINESS_SELLER_LABEL,
                CategoryFieldType.enum,
                True,
                20,
                _choices(*BUSINESS_EQUIPMENT_SELLER_TARGET),
            ),
        ]

        cond_kinds = [k for k in kinds if k in cond_approved]
        if cond_kinds:
            cond_opts: dict[str, Any] = _choices(
                *BUSINESS_EQUIPMENT_CONDITION_CHOICES
            )
            if set(cond_kinds) != set(kinds):
                cond_opts["depends_on"] = {
                    "field": BUSINESS_KIND_KEY,
                    "values": list(cond_kinds),
                }
            fields.append(
                _dep_field(
                    BUSINESS_CONDITION_KEY,
                    BUSINESS_CONDITION_LABEL,
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
            if key in BUSINESS_EQUIPMENT_CREATE_FORBIDDEN:
                raise RuntimeError(f"forbidden Create field {slug}.{key}")
            if key not in _ALWAYS_CREATE:
                raise RuntimeError(f"unapproved Create field {slug}.{key}")
            opts = row[5]
            if opts and opts.get("choices") is not None and len(opts["choices"]) == 0:
                raise RuntimeError(f"empty picker {slug}.{key}")

        out[slug] = fields
    return out


def business_equipment_v2_all_kind_audit() -> list[dict[str, Any]]:
    """All-176 kind audit rows (Package A). Pair with independent expectations."""
    cores = build_business_equipment_v2_core_fields()
    rows: list[dict[str, Any]] = []
    for section_key, slug in BUSINESS_EQUIPMENT_V2_SECTION_SLUGS.items():
        catalog = BUSINESS_SECTIONS[section_key]
        fields = cores[slug]
        keys = [r[0] for r in fields]
        kind_row = next(r for r in fields if r[0] == BUSINESS_KIND_KEY)
        kind_opts = [c["value"] for c in kind_row[5]["choices"]]
        seller_row = next(r for r in fields if r[0] == BUSINESS_SELLER_KEY)
        seller_opts = [c["value"] for c in seller_row[5]["choices"]]
        cond_row = next(
            (r for r in fields if r[0] == BUSINESS_CONDITION_KEY), None
        )
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
                BUSINESS_KIND_KEY,
                BUSINESS_SELLER_KEY,
                "price",
                "negotiable",
                "contact_methods",
            }
        ]

        for role in catalog["roles"]:
            kind = str(role["label"])
            cond_yes = business_equipment_v2_condition_visible_for_kind(kind)
            kind_specials = list(specials)
            if not cond_yes:
                kind_specials = [
                    k for k in kind_specials if k != BUSINESS_CONDITION_KEY
                ]
            ownership = "BUSINESS_EQUIPMENT"
            if kind in BUSINESS_EQUIPMENT_ELECTRONICS_BOUNDARY:
                ownership = BUSINESS_EQUIPMENT_ELECTRONICS_BOUNDARY[kind]
            elif kind in BUSINESS_EQUIPMENT_REPAIR_BOUNDARY:
                ownership = BUSINESS_EQUIPMENT_REPAIR_BOUNDARY[kind]
            elif kind in BUSINESS_EQUIPMENT_MEDICAL_BOUNDARY:
                ownership = BUSINESS_EQUIPMENT_MEDICAL_BOUNDARY[kind]
            elif kind in BUSINESS_EQUIPMENT_BEAUTY_BOUNDARY:
                ownership = BUSINESS_EQUIPMENT_BEAUTY_BOUNDARY[kind]
            rows.append(
                {
                    "kind": kind,
                    "section": section_key,
                    "slug": slug,
                    "business_kind_valid": kind in kind_opts,
                    "condition": "YES" if cond_yes else "NO",
                    "condition_in_schema": cond_yes == (kind in cond_values),
                    "seller": seller_opts,
                    "price": "price" in keys,
                    "special_count": len(kind_specials),
                    "forbidden": sorted(
                        set(keys) & BUSINESS_EQUIPMENT_CREATE_FORBIDDEN
                    ),
                    "components": {
                        BUSINESS_KIND_KEY: "enum",
                        "price": "price",
                        BUSINESS_SELLER_KEY: "enum",
                        "contact_methods": "enum",
                    },
                    "ownership": ownership,
                }
            )
    return rows


def business_equipment_v2_complexity_histogram() -> dict[str, int]:
    """special_count histogram excluding kind/shared base (condition only)."""
    hist = {"0": 0, "1": 0, "2": 0, "3+": 0}
    for row in business_equipment_v2_all_kind_audit():
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


def business_equipment_v2_section_kinds(slug: str) -> list[str]:
    for section_key, section_slug in BUSINESS_EQUIPMENT_V2_SECTION_SLUGS.items():
        if section_slug != slug:
            continue
        catalog = BUSINESS_SECTIONS[section_key]
        return [str(r["label"]) for r in catalog["roles"]]
    raise KeyError(f"Unknown Business Equipment L2 slug: {slug}")


def _search_filter(
    key: str,
    label: str,
    ftype: CategoryFilterType,
    sort: int,
    config: dict[str, Any] | None,
) -> tuple:
    return (key, label, ftype, sort, config)


def build_business_equipment_v2_search_filters() -> dict[str, list]:
    """Package B Search SoT per canonical Business Equipment L2.

    Explicit allowlist only. Condition inherits Package A depends_on
    from Create cores (Create↔Search parity). Price / negotiable / contacts /
    brand / tech never Search. Geo is shared Search UX, not CategoryFilter rows.
    """
    cores = build_business_equipment_v2_core_fields()
    out: dict[str, list] = {}
    for slug, fields in cores.items():
        filters: list = []
        for key, label, _ftype, _required, sort, options, _hint in fields:
            if key not in BUSINESS_EQUIPMENT_V2_SEARCH_EAV_KEYS:
                continue
            if key in BUSINESS_EQUIPMENT_V2_SEARCH_EXCLUDE:
                continue
            if key not in BUSINESS_EQUIPMENT_V2_SEARCH_ALLOWLIST:
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
    if set(out) != BUSINESS_EQUIPMENT_V2_CANONICAL_SLUGS:
        raise RuntimeError(
            "Business Equipment Search filter map != canonical L2 slugs: "
            f"extra={sorted(set(out) - BUSINESS_EQUIPMENT_V2_CANONICAL_SLUGS)} "
            f"missing={sorted(BUSINESS_EQUIPMENT_V2_CANONICAL_SLUGS - set(out))}"
        )
    return out


def business_equipment_v2_search_kind_audit_row(
    section_key: str, slug: str, kind: str
) -> dict[str, Any]:
    """All-kind Search audit row (independent of Create visible_components)."""
    cond_yes = business_equipment_v2_condition_visible_for_kind(kind)
    ownership = "BUSINESS_EQUIPMENT"
    if kind in BUSINESS_EQUIPMENT_ELECTRONICS_BOUNDARY:
        ownership = BUSINESS_EQUIPMENT_ELECTRONICS_BOUNDARY[kind]
    elif kind in BUSINESS_EQUIPMENT_REPAIR_BOUNDARY:
        ownership = BUSINESS_EQUIPMENT_REPAIR_BOUNDARY[kind]
    elif kind in BUSINESS_EQUIPMENT_MEDICAL_BOUNDARY:
        ownership = BUSINESS_EQUIPMENT_MEDICAL_BOUNDARY[kind]
    elif kind in BUSINESS_EQUIPMENT_BEAUTY_BOUNDARY:
        ownership = BUSINESS_EQUIPMENT_BEAUTY_BOUNDARY[kind]
    visible = [BUSINESS_KIND_KEY, BUSINESS_SELLER_KEY]
    if cond_yes:
        visible.append(BUSINESS_CONDITION_KEY)
    return {
        "l2": slug,
        "section": section_key,
        "kind": kind,
        "search_business_kind": "YES",
        "search_seller": "YES",
        "search_condition": "YES" if cond_yes else "NO",
        "search_brand": "NO",
        "search_model": "NO",
        "search_power": "NO",
        "search_voltage": "NO",
        "search_price": "NO",
        "search_negotiable": "NO",
        "search_contacts": "NO",
        "search_geo": "YES",
        "retired_resurrected": slug in BUSINESS_EQUIPMENT_V2_RETIRED_SLUGS,
        "ownership": ownership,
        "visible_search_keys": visible,
        "ui_components": {
            BUSINESS_KIND_KEY: "multi_select",
            BUSINESS_SELLER_KEY: "multi_select",
            **(
                {BUSINESS_CONDITION_KEY: "multi_select"}
                if cond_yes
                else {}
            ),
            "geo": "region_city",
        },
    }


def business_equipment_v2_all_search_kind_audit() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for section_key, slug in BUSINESS_EQUIPMENT_V2_SECTION_SLUGS.items():
        catalog = BUSINESS_SECTIONS[section_key]
        for role in catalog["roles"]:
            rows.append(
                business_equipment_v2_search_kind_audit_row(
                    section_key, slug, str(role["label"])
                )
            )
    return rows


def business_equipment_v2_search_policy_prep() -> dict[str, Any]:
    return {
        "allow": sorted(BUSINESS_EQUIPMENT_V2_SEARCH_ALLOWLIST),
        "eav": sorted(BUSINESS_EQUIPMENT_V2_SEARCH_EAV_KEYS),
        "exclude": sorted(BUSINESS_EQUIPMENT_V2_SEARCH_EXCLUDE),
    }
