# -*- coding: utf-8 -*-
"""Animals V2 — taxonomy ownership + Package A Create + Package B Search SoT.

Backend/API is Create + Search authority. Flutter is renderer / offline fallback.
Search filters = explicit short allowlist (Create ≠ Search).
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
)

ANIMALS_ROOT_SLUG = "animals"
ANIMALS_ROOT_LABEL = "Животные"
ANIMALS_V2_ENTITY_TYPE = CategoryEntityType.animal

ANIMALS_KIND_KEY = "animals_kind"
ANIMALS_KIND_LABEL = "Товар"
ANIMALS_SELLER_KEY = "seller_type"
ANIMALS_SELLER_LABEL = "Кто продаёт"
ANIMALS_GENDER_KEY = "gender"
ANIMALS_GENDER_LABEL = "Пол"
ANIMALS_CONDITION_KEY = "condition"
ANIMALS_CONDITION_LABEL = "Состояние"

ANIMALS_SELLER_CHOICES: tuple[str, ...] = (
    "Частное лицо",
    "Хозяйство",
    "Питомник",
    "Магазин",
    "Другой",
)
ANIMALS_GENDER_CHOICES: tuple[str, ...] = ("Самец", "Самка")
ANIMALS_CONDITION_CHOICES: tuple[str, ...] = ("Новое", "Б/у")

ANIMALS_V2_LEGACY_RETIRED_SLUGS: frozenset[str] = frozenset(
    {
        "animals-pets",
        "animals-livestock",
        "animals-birds",
    }
)

ANIMALS_VET_SERVICES_SLUG = "animals-veterinarnye-uslugi"
ANIMALS_FEED_SLUG = "animals-seno-korma-i-kormovye-dobavki"
ANIMALS_VET_GOODS_SLUG = "animals-vetapteka-i-veterinarnye-tovary"

# Active goods/animal L2 after vet-services ownership move (Option B).
ANIMALS_V2_CANONICAL_LEAVES: tuple[tuple[str, str, int], ...] = (
    ("Овцы, бараны и козы", "animals-ovtsy-barany-i-kozy", 10),
    ("Коровы, быки и телята", "animals-korovy-byki-i-telyata", 20),
    ("Лошади", "animals-loshadi", 30),
    ("Птицеводство", "animals-ptitsevodstvo", 40),
    ("Собаки", "animals-sobaki", 50),
    ("Кошки", "animals-koshki", 60),
    ("Кролики", "animals-kroliki", 70),
    ("Пчеловодство", "animals-pchelovodstvo", 80),
    ("Рыбы и аквариумистика", "animals-ryby-i-akvariumistika", 90),
    ("Грызуны", "animals-gryzuny", 100),
    ("Рептилии/экзотические животные", "animals-reptilii-ekzoticheskie-zhivotnye", 110),
    ("Сено, Корма и кормовые добавки", ANIMALS_FEED_SLUG, 120),
    ("Товары/аксессуары для животных", "animals-tovary-aksessuary-dlya-zhivotnyh", 130),
    ("Ветаптека и ветеринарные товары", ANIMALS_VET_GOODS_SLUG, 140),
    ("Прочие животные", "animals-prochie-zhivotnye", 160),
)

ANIMALS_V2_CANONICAL_SLUGS: frozenset[str] = frozenset(
    slug for _label, slug, _sort in ANIMALS_V2_CANONICAL_LEAVES
)

ANIMALS_V2_RETIRED_SLUGS: frozenset[str] = frozenset(
    set(ANIMALS_V2_LEGACY_RETIRED_SLUGS) | {ANIMALS_VET_SERVICES_SLUG}
)

ANIMALS_V2_EXPECTED_L2_COUNT = len(ANIMALS_V2_CANONICAL_LEAVES)  # 15

ANIMALS_V2_SECTION_SLUGS: dict[str, str] = {
    "sheep": "animals-ovtsy-barany-i-kozy",
    "cattle": "animals-korovy-byki-i-telyata",
    "horses": "animals-loshadi",
    "poultry": "animals-ptitsevodstvo",
    "dogs": "animals-sobaki",
    "cats": "animals-koshki",
    "rabbits": "animals-kroliki",
    "bees": "animals-pchelovodstvo",
    "fish": "animals-ryby-i-akvariumistika",
    "rodents": "animals-gryzuny",
    "reptiles": "animals-reptilii-ekzoticheskie-zhivotnye",
    "feed": ANIMALS_FEED_SLUG,
    "accessories": "animals-tovary-aksessuary-dlya-zhivotnyh",
    "vetgoods": ANIMALS_VET_GOODS_SLUG,
    "other": "animals-prochie-zhivotnye",
}

# --- Services Option B: exact destinations under services-prochie-uslugi ---
SERVICES_OTHER_SLUG = "services-prochie-uslugi"
SERVICES_ANIMAL_CARE_KIND = "Уход за животными"

# Former Animals vet-service kinds → Services kind (exact after Option B expand).
ANIMALS_VET_SERVICE_KIND_MAPPING: dict[str, tuple[str, str, str]] = {
    "Осмотр": ("EXACT_DESTINATION", SERVICES_OTHER_SLUG, "Осмотр"),
    "Вакцинация": ("EXACT_DESTINATION", SERVICES_OTHER_SLUG, "Вакцинация"),
    "Стерилизация и кастрация": (
        "EXACT_DESTINATION",
        SERVICES_OTHER_SLUG,
        "Стерилизация и кастрация",
    ),
    "Хирургия": ("EXACT_DESTINATION", SERVICES_OTHER_SLUG, "Хирургия"),
    "Стационар": ("EXACT_DESTINATION", SERVICES_OTHER_SLUG, "Стационар"),
    "Груминг": ("EXACT_DESTINATION", SERVICES_OTHER_SLUG, "Груминг"),
    "Другие ветеринарные услуги": (
        "EXACT_DESTINATION",
        SERVICES_OTHER_SLUG,
        "Другие ветеринарные услуги",
    ),
}

# Services «other» animal-care/clinical kinds after Option B (not Animals).
SERVICES_VET_EXPANDED_KINDS: tuple[str, ...] = (
    "Осмотр",
    "Вакцинация",
    "Стерилизация и кастрация",
    "Хирургия",
    "Стационар",
    "Другие ветеринарные услуги",
    "Груминг",
    "Уход за животными",
)

ANIMALS_VET_SERVICES_RETIRE_BLOCKED = False

# Independent Sex allowlist (positive, default off).
# No sex where kind already encodes sex (Бараны/Быки/Кобылы/Петухи…).
# No sex for вязка, feed, goods, equipment, fish, poultry, bees.
ANIMALS_V2_SEX_APPROVED_KINDS: frozenset[str] = frozenset(
    {
        "Собаки",
        "Щенки",
        "Другие собаки",
        "Кошки",
        "Котята",
        "Другие кошки",
        "Кролики",
        "Декоративные кролики",
        "Другие кролики",
        "Хомяки",
        "Морские свинки",
        "Крысы",
        "Мыши",
        "Шиншиллы",
        "Дегу",
        "Другие грызуны",
        "Черепахи",
        "Змеи",
        "Ящерицы",
        "Пауки",
        "Другие экзотические животные",
        "Свиньи",
        "Ослы",
        "Верблюды",
        "Другие животные",
    }
)

# Independent Condition allowlist — durable goods only.
ANIMALS_V2_CONDITION_APPROVED_KINDS: frozenset[str] = frozenset(
    {
        "Ошейники",
        "Поводки",
        "Переноски",
        "Клетки",
        "Миски",
        "Лежанки",
        "Игрушки для животных",
        "Другие аксессуары для животных",
        "Ульи",
        "Рамки",
        "Аквариумы",
        "Оборудование для аквариума",
    }
)

ANIMALS_V2_AGE_TARGET = "DESCRIPTION"
ANIMALS_V2_BREED_TARGET = "DESCRIPTION"
ANIMALS_V2_WEIGHT_TARGET = "DESCRIPTION"
ANIMALS_V2_COLOR_TARGET = "DESCRIPTION"
ANIMALS_V2_DOCUMENTS_TARGET = "DESCRIPTION"
ANIMALS_V2_VACCINATION_STATUS_TARGET = "DESCRIPTION"
ANIMALS_V2_PRICE_BASIS_POLICY = "ABSENT"

ANIMALS_V2_BANNED_BREED_KIND_LABELS: frozenset[str] = frozenset(
    {
        "Алабаи",
        "Хаски",
        "Мейн-куны",
        "Британские",
        "Калифорнийские",
        "Новозеландские",
        "Голштин",
        "Гиссарские",
    }
)

ANIMALS_V2_BANNED_KIND_LABELS: frozenset[str] = frozenset(
    {
        "Мёд",
        "Соты",
        "Перга",
        "Прополис",
        "Пыльца",
        "Яйца",
        "Молоко",
        "Пшеница",
        "Ячмень",
        "Антибиотики",
        "Вакцины",
        "Лекарства",
        "Таблетки",
        "Сёдла",
    }
)

ANIMALS_CREATE_FORBIDDEN: frozenset[str] = frozenset(
    {
        "age",
        "breed",
        "порода",
        "weight",
        "color",
        "pedigree",
        "passport",
        "documents",
        "vaccination_status",
        "price_basis",
        "quantity",
        "purpose",
        "назначение",
    }
)

_ALWAYS_CREATE: frozenset[str] = frozenset(
    {
        ANIMALS_KIND_KEY,
        ANIMALS_SELLER_KEY,
        ANIMALS_GENDER_KEY,
        ANIMALS_CONDITION_KEY,
        "price",
        "negotiable",
        "contact_methods",
    }
)

# Package B Search — explicit allowlist (Create ≠ Search).
# Geo is shared Search UX (region/city), not CategoryFilter rows.
ANIMALS_V2_SEARCH_ALLOWLIST: frozenset[str] = frozenset(
    {
        ANIMALS_KIND_KEY,
        ANIMALS_GENDER_KEY,
        ANIMALS_CONDITION_KEY,
        ANIMALS_SELLER_KEY,
        "geo",
    }
)

ANIMALS_V2_SEARCH_EAV_KEYS: frozenset[str] = frozenset(
    {
        ANIMALS_KIND_KEY,
        ANIMALS_GENDER_KEY,
        ANIMALS_CONDITION_KEY,
        ANIMALS_SELLER_KEY,
    }
)

ANIMALS_V2_SEARCH_EXCLUDE: frozenset[str] = frozenset(
    set(ANIMALS_CREATE_FORBIDDEN)
    | {
        "price",
        "negotiable",
        "contact_methods",
        "price_basis",
        "quantity",
        "unit",
        "feed_unit",
        "weight",
        "color",
        "breed",
        "age",
        "documents",
        "vaccination_status",
        "порода",
    }
)

# Backward-compatible alias used by Package A tests.
ANIMALS_V2_SEARCH_POLICY_PREP: frozenset[str] = ANIMALS_V2_SEARCH_ALLOWLIST


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


def _animals_sections() -> dict[str, dict[str, Any]]:
    from app.seeds.animals_sections_catalog import ANIMALS_SECTIONS

    return ANIMALS_SECTIONS


def animals_v2_kind_count() -> int:
    return sum(len(cat["roles"]) for cat in _animals_sections().values())


def animals_v2_all_kinds() -> list[str]:
    out: list[str] = []
    for cat in _animals_sections().values():
        for role in cat["roles"]:
            out.append(str(role["label"]))
    return out


def animals_v2_assert_cleanup_contracts() -> None:
    """Taxonomy + ownership invariants (Package A)."""
    animals_v2_assert_package_a_contracts()


def animals_v2_assert_package_a_contracts() -> None:
    sections = _animals_sections()
    if len(sections) != ANIMALS_V2_EXPECTED_L2_COUNT:
        raise RuntimeError(
            f"Animals expected {ANIMALS_V2_EXPECTED_L2_COUNT} sections, got {len(sections)}"
        )
    if "vetservices" in sections:
        raise RuntimeError("Animals catalog must not keep vetservices section")
    catalog_slugs = {cat["category_slug"] for cat in sections.values()}
    if catalog_slugs != ANIMALS_V2_CANONICAL_SLUGS:
        raise RuntimeError("Animals catalog slugs ≠ canonical L2 set")
    if ANIMALS_VET_SERVICES_SLUG in ANIMALS_V2_CANONICAL_SLUGS:
        raise RuntimeError("Animals vet-services L2 must not be canonical")
    if ANIMALS_VET_SERVICES_SLUG not in ANIMALS_V2_RETIRED_SLUGS:
        raise RuntimeError("Animals vet-services must be retired")
    if ANIMALS_V2_LEGACY_RETIRED_SLUGS & ANIMALS_V2_CANONICAL_SLUGS:
        raise RuntimeError("Legacy triad intersects canonical")
    if ANIMALS_FEED_SLUG not in ANIMALS_V2_CANONICAL_SLUGS:
        raise RuntimeError("Feed ownership missing")
    if ANIMALS_VET_GOODS_SLUG not in ANIMALS_V2_CANONICAL_SLUGS:
        raise RuntimeError("Vet goods ownership missing")
    if ANIMALS_V2_AGE_TARGET != "DESCRIPTION":
        raise RuntimeError("Age must be Description")
    if ANIMALS_V2_PRICE_BASIS_POLICY != "ABSENT":
        raise RuntimeError("price_basis must be absent")
    kinds = set(animals_v2_all_kinds())
    if kinds & ANIMALS_V2_BANNED_BREED_KIND_LABELS:
        raise RuntimeError("Breed-as-kind labels still present")
    if kinds & ANIMALS_V2_BANNED_KIND_LABELS:
        raise RuntimeError("Banned cross-root kinds present")
    # Sex/condition allowlists must subset actual kinds.
    if not ANIMALS_V2_SEX_APPROVED_KINDS <= kinds:
        missing = ANIMALS_V2_SEX_APPROVED_KINDS - kinds
        raise RuntimeError(f"Sex allowlist kinds missing from catalog: {missing}")
    if not ANIMALS_V2_CONDITION_APPROVED_KINDS <= kinds:
        missing = ANIMALS_V2_CONDITION_APPROVED_KINDS - kinds
        raise RuntimeError(f"Condition allowlist kinds missing: {missing}")
    for kind, (decision, dest, services_kind) in ANIMALS_VET_SERVICE_KIND_MAPPING.items():
        if decision != "EXACT_DESTINATION":
            raise RuntimeError(f"Vet mapping must be EXACT after Option B: {kind}")
        if dest != SERVICES_OTHER_SLUG:
            raise RuntimeError(f"Unexpected Services destination for {kind}")
        if services_kind not in SERVICES_VET_EXPANDED_KINDS:
            raise RuntimeError(f"Services missing expanded kind {services_kind}")


def animals_vet_service_mapping_report() -> list[dict[str, Any]]:
    return [
        {
            "animals_kind": kind,
            "decision": decision,
            "services_slug": dest,
            "services_kind": services_kind,
            "note": f"Services «{services_kind}» under {dest}",
        }
        for kind, (decision, dest, services_kind) in ANIMALS_VET_SERVICE_KIND_MAPPING.items()
    ]


def build_animals_v2_core_fields() -> dict[str, list]:
    """Create cores for all active Animals L2 (Package A SoT)."""
    animals_v2_assert_package_a_contracts()
    sections = _animals_sections()
    out: dict[str, list] = {}
    sex_approved = ANIMALS_V2_SEX_APPROVED_KINDS
    cond_approved = ANIMALS_V2_CONDITION_APPROVED_KINDS

    for section_key, slug in ANIMALS_V2_SECTION_SLUGS.items():
        catalog = sections[section_key]
        kinds = [str(r["label"]) for r in catalog["roles"]]
        fields: list = [
            _dep_field(
                ANIMALS_KIND_KEY,
                ANIMALS_KIND_LABEL,
                CategoryFieldType.enum,
                True,
                10,
                _choices(*kinds),
                hint=str(catalog.get("question") or "Какой товар?"),
            ),
            _dep_field(
                ANIMALS_SELLER_KEY,
                ANIMALS_SELLER_LABEL,
                CategoryFieldType.enum,
                True,
                20,
                _choices(*ANIMALS_SELLER_CHOICES),
            ),
        ]

        sex_kinds = [k for k in kinds if k in sex_approved]
        if sex_kinds:
            sex_opts: dict[str, Any] = _choices(*ANIMALS_GENDER_CHOICES)
            if set(sex_kinds) != set(kinds):
                sex_opts["depends_on"] = {
                    "field": ANIMALS_KIND_KEY,
                    "values": list(sex_kinds),
                }
            fields.append(
                _dep_field(
                    ANIMALS_GENDER_KEY,
                    ANIMALS_GENDER_LABEL,
                    CategoryFieldType.enum,
                    False,
                    30,
                    sex_opts,
                )
            )

        cond_kinds = [k for k in kinds if k in cond_approved]
        if cond_kinds:
            cond_opts: dict[str, Any] = _choices(*ANIMALS_CONDITION_CHOICES)
            if set(cond_kinds) != set(kinds):
                cond_opts["depends_on"] = {
                    "field": ANIMALS_KIND_KEY,
                    "values": list(cond_kinds),
                }
            fields.append(
                _dep_field(
                    ANIMALS_CONDITION_KEY,
                    ANIMALS_CONDITION_LABEL,
                    CategoryFieldType.enum,
                    False,
                    40,
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
            if key in ANIMALS_CREATE_FORBIDDEN:
                raise RuntimeError(f"forbidden Create field {slug}.{key}")
            if key not in _ALWAYS_CREATE:
                raise RuntimeError(f"unapproved Create field {slug}.{key}")
            opts = row[5]
            if opts and opts.get("choices") is not None and len(opts["choices"]) == 0:
                raise RuntimeError(f"empty picker {slug}.{key}")

        out[slug] = fields
    return out


def animals_v2_sex_visible_for_kind(kind: str) -> bool:
    return kind in ANIMALS_V2_SEX_APPROVED_KINDS


def animals_v2_condition_visible_for_kind(kind: str) -> bool:
    return kind in ANIMALS_V2_CONDITION_APPROVED_KINDS


def animals_v2_classify_kind(kind: str, section_key: str) -> str:
    if kind in ANIMALS_V2_CONDITION_APPROVED_KINDS:
        return "durable_good"
    if section_key == "feed":
        return "feed"
    if section_key == "vetgoods":
        return "vet_consumable"
    if kind in {
        "Инкубационные яйца",
        "Ульи",
        "Рамки",
        "Аквариумы",
        "Оборудование для аквариума",
        "Другое для пчеловодства",
        "Другие рыбы и аквариумы",
    }:
        if kind in ANIMALS_V2_CONDITION_APPROVED_KINDS:
            return "durable_good"
        if kind in {"Инкубационные яйца"}:
            return "breeding_good"
        return "mixed_or_other_good"
    if kind.startswith("Вязка"):
        return "live_service_offer"
    return "live_animal"


def animals_v2_all_kind_audit() -> list[dict[str, Any]]:
    """Independent all-kind audit (Package A)."""
    cores = build_animals_v2_core_fields()
    sections = _animals_sections()
    rows: list[dict[str, Any]] = []
    for section_key, slug in ANIMALS_V2_SECTION_SLUGS.items():
        catalog = sections[section_key]
        fields = cores[slug]
        keys = [r[0] for r in fields]
        kind_row = next(r for r in fields if r[0] == ANIMALS_KIND_KEY)
        kind_opts = [c["value"] for c in kind_row[5]["choices"]]
        seller_row = next(r for r in fields if r[0] == ANIMALS_SELLER_KEY)
        seller_opts = [c["value"] for c in seller_row[5]["choices"]]
        gender_row = next((r for r in fields if r[0] == ANIMALS_GENDER_KEY), None)
        gender_values = (
            set((gender_row[5].get("depends_on") or {}).get("values") or kind_opts)
            if gender_row is not None
            else set()
        )
        if gender_row is not None and "depends_on" not in (gender_row[5] or {}):
            gender_values = set(kind_opts)
        cond_row = next((r for r in fields if r[0] == ANIMALS_CONDITION_KEY), None)
        cond_values = (
            set((cond_row[5].get("depends_on") or {}).get("values") or kind_opts)
            if cond_row is not None
            else set()
        )
        if cond_row is not None and "depends_on" not in (cond_row[5] or {}):
            cond_values = set(kind_opts)

        for role in catalog["roles"]:
            kind = str(role["label"])
            sex_yes = animals_v2_sex_visible_for_kind(kind)
            cond_yes = animals_v2_condition_visible_for_kind(kind)
            rows.append(
                {
                    "kind": kind,
                    "section": section_key,
                    "slug": slug,
                    "class": animals_v2_classify_kind(kind, section_key),
                    "animals_kind_valid": kind in kind_opts,
                    "sex": "YES" if sex_yes else "NO",
                    "sex_in_schema": sex_yes == (kind in gender_values),
                    "condition": "YES" if cond_yes else "NO",
                    "condition_in_schema": cond_yes == (kind in cond_values),
                    "seller": seller_opts,
                    "price": "price" in keys,
                    "price_basis": "price_basis" not in keys,
                    "forbidden": sorted(set(keys) & ANIMALS_CREATE_FORBIDDEN),
                    "components": {
                        ANIMALS_KIND_KEY: "enum",
                        ANIMALS_SELLER_KEY: "enum",
                        "price": "price",
                        "negotiable": "enum",
                        "contact_methods": "enum",
                        **(
                            {ANIMALS_GENDER_KEY: "enum"}
                            if gender_row is not None
                            else {}
                        ),
                        **(
                            {ANIMALS_CONDITION_KEY: "enum"}
                            if cond_row is not None
                            else {}
                        ),
                    },
                    "ownership": "animals",
                }
            )
    return rows


def animals_v2_complexity_histogram() -> dict[str, int]:
    """Specials over shared base: animals_kind + optional gender/condition."""
    hist = {"0": 0, "1": 0, "2": 0, "3": 0, "4": 0, "5+": 0}
    for row in animals_v2_all_kind_audit():
        specials = 1  # animals_kind
        if row["sex"] == "YES":
            specials += 1
        if row["condition"] == "YES":
            specials += 1
        if specials >= 5:
            hist["5+"] += 1
        else:
            hist[str(specials)] += 1
    return hist


def animals_v2_section_kinds(slug: str) -> list[str]:
    """Kinds for a canonical Animals L2 slug (catalog order)."""
    for section_key, section_slug in ANIMALS_V2_SECTION_SLUGS.items():
        if section_slug != slug:
            continue
        catalog = _animals_sections()[section_key]
        return [str(r["label"]) for r in catalog["roles"]]
    raise KeyError(f"Unknown Animals L2 slug: {slug}")


def _search_filter(
    key: str,
    label: str,
    ftype: CategoryFilterType,
    sort: int,
    config: dict[str, Any] | None,
) -> tuple:
    return (key, label, ftype, sort, config)


def build_animals_v2_search_filters() -> dict[str, list]:
    """Package B Search SoT per canonical Animals L2.

    Explicit allowlist only. Sex/Condition inherit Package A depends_on
    from Create cores (Create↔Search parity). Price / negotiable / contacts /
    Age / Breed / Weight / Color / Documents / Vaccination never Search.
    Geo is shared Search UX, not CategoryFilter rows.
    """
    cores = build_animals_v2_core_fields()
    out: dict[str, list] = {}
    for slug, fields in cores.items():
        filters: list = []
        for key, label, _ftype, _required, sort, options, _hint in fields:
            if key not in ANIMALS_V2_SEARCH_EAV_KEYS:
                continue
            if key in ANIMALS_V2_SEARCH_EXCLUDE:
                continue
            if key not in ANIMALS_V2_SEARCH_ALLOWLIST:
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
    if set(out) != ANIMALS_V2_CANONICAL_SLUGS:
        raise RuntimeError(
            "Animals Search filter map != canonical L2 slugs: "
            f"extra={sorted(set(out) - ANIMALS_V2_CANONICAL_SLUGS)} "
            f"missing={sorted(ANIMALS_V2_CANONICAL_SLUGS - set(out))}"
        )
    return out


def animals_v2_search_kind_audit_row(
    section_key: str, slug: str, kind: str
) -> dict[str, Any]:
    """All-kind Search audit row (independent of Create visible_components)."""
    sex_yes = animals_v2_sex_visible_for_kind(kind)
    cond_yes = animals_v2_condition_visible_for_kind(kind)
    visible = [ANIMALS_KIND_KEY, ANIMALS_SELLER_KEY]
    if sex_yes:
        visible.append(ANIMALS_GENDER_KEY)
    if cond_yes:
        visible.append(ANIMALS_CONDITION_KEY)
    return {
        "l2": slug,
        "section": section_key,
        "kind": kind,
        "class": animals_v2_classify_kind(kind, section_key),
        "search_animals_kind": "YES",
        "search_seller": "YES",
        "search_sex": "YES" if sex_yes else "NO",
        "search_condition": "YES" if cond_yes else "NO",
        "search_age": "NO",
        "search_breed": "NO",
        "search_weight": "NO",
        "search_color": "NO",
        "search_documents": "NO",
        "search_vaccination": "NO",
        "search_price": "NO",
        "search_price_basis": "NO",
        "search_negotiable": "NO",
        "search_contacts": "NO",
        "search_geo": "YES",
        "retired_resurrected": slug in ANIMALS_V2_RETIRED_SLUGS,
        "ownership": "animals",
        "visible_search_keys": visible,
    }


def animals_v2_all_search_kind_audit() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    sections = _animals_sections()
    for section_key, slug in ANIMALS_V2_SECTION_SLUGS.items():
        catalog = sections[section_key]
        for role in catalog["roles"]:
            rows.append(
                animals_v2_search_kind_audit_row(
                    section_key, slug, str(role["label"])
                )
            )
    return rows


def animals_v2_search_policy_prep() -> dict[str, Any]:
    """Explicit Search allowlist (Package B)."""
    return {
        "allow": sorted(ANIMALS_V2_SEARCH_ALLOWLIST),
        "eav": sorted(ANIMALS_V2_SEARCH_EAV_KEYS),
        "exclude": sorted(ANIMALS_V2_SEARCH_EXCLUDE),
        "sex_kinds": sorted(ANIMALS_V2_SEX_APPROVED_KINDS),
        "condition_kinds": sorted(ANIMALS_V2_CONDITION_APPROVED_KINDS),
    }
