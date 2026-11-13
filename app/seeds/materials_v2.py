# -*- coding: utf-8 -*-
"""Materials / Raw Materials V2 — Package A Create SoT + Package B Search SoT.

Food Tara GAP remains STILL_OPEN (no invented kinds).
Condition removed entirely for Materials V2 (Create + Search).
price_basis is Create/Detail only — never Search.
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

MATERIALS_KIND_KEY = "materials_kind"
MATERIALS_KIND_LABEL = "Товар"
MATERIALS_SELLER_KEY = "seller_type"
MATERIALS_SELLER_LABEL = "Продавец"

MATERIALS_ROOT_SLUG = "materials"
MATERIALS_ROOT_LABEL = "Материалы, сырьё и товары для производства"
# Historical Flutter typo — compatibility alias only.
MATERIALS_ROOT_LABEL_LEGACY_ALIAS = "Сырьё для производство"
MATERIALS_V2_ENTITY_TYPE = CategoryEntityType.raw_material

MATERIALS_V2_LEGACY_TRIAD_SLUGS: frozenset[str] = frozenset(
    {
        "materials-textile",
        "materials-metal",
        "materials-chemical",
    }
)
MATERIALS_V2_IMPORT_SLUG = "materials-import-i-optovye-postavki-syrya"
MATERIALS_V2_IMPORT_STATUS = "RETIRED_SALES_MODE_NOT_PRODUCT_IDENTITY"

MATERIALS_V2_RETIRED_SLUGS: frozenset[str] = (
    MATERIALS_V2_LEGACY_TRIAD_SLUGS | {MATERIALS_V2_IMPORT_SLUG}
)

# Canonical modern active L2 (18) — Import/Wholesale excluded.
MATERIALS_V2_CANONICAL_LEAVES: tuple[tuple[str, str, int], ...] = (
    ("Ткани и текстильное сырьё", "materials-tkani-i-tekstilnoe-syre", 10),
    ("Швейная фурнитура", "materials-shveynaya-furnitura", 20),
    ("Кожа и кожзаменители", "materials-kozha-i-kozhzameniteli", 30),
    ("Нитки, пряжа и волокно", "materials-nitki-pryazha-i-volokno", 40),
    ("Металлы/металлическое сырьё", "materials-metally-metallicheskoe-syre", 50),
    ("Древесина и древесное сырьё", "materials-drevesina-i-drevesnoe-syre", 60),
    ("Пластик и полимерное сырьё", "materials-plastik-i-polimernoe-syre", 70),
    ("Резина и каучук", "materials-rezina-i-kauchuk", 80),
    ("Бумага и картон", "materials-bumaga-i-karton", 90),
    ("Стекло и стекольное сырьё", "materials-steklo-i-stekolnoe-syre", 100),
    ("Химическое сырьё", "materials-himicheskoe-syre", 110),
    ("Лакокрасочное сырьё", "materials-lakokrasochnoe-syre", 120),
    ("Упаковочные материалы", "materials-upakovochnye-materialy", 130),
    ("Пищевое сырьё и ингредиенты", "materials-pischevoe-syre-i-ingredienty", 140),
    (
        "Сырьё для косметики/парфюмерии",
        "materials-syre-dlya-kosmetiki-parfyumerii",
        150,
    ),
    ("Сырьё для бытовой химии", "materials-syre-dlya-bytovoy-himii", 160),
    ("Для ювелирного производства", "materials-dlya-yuvelirnogo-proizvodstva", 170),
    ("Прочее сырьё для производства", "materials-prochee-syre-dlya-proizvodstva", 190),
)
MATERIALS_V2_CANONICAL_SLUGS: frozenset[str] = frozenset(
    slug for _label, slug, _s in MATERIALS_V2_CANONICAL_LEAVES
)
MATERIALS_V2_EXPECTED_L2_COUNT = len(MATERIALS_V2_CANONICAL_LEAVES)

MATERIALS_SELLER_TARGET = GOODS_SELLER_CHOICES
MATERIALS_CONDITION_POLICY = "ABSENT"
MATERIALS_PACKAGING_SLUG = "materials-upakovochnye-materialy"
FOOD_TARA_GAP_STATUS = "STILL_OPEN"

MATERIALS_PRICE_BASIS_KEY = "price_basis"
MATERIALS_PRICE_BASIS_LABEL = "Цена за"
MATERIALS_PRICE_BASIS_REQUIRED = False
MATERIALS_PRICE_BASIS_OPTIONS: tuple[str, ...] = (
    "кг",
    "г",
    "тонна",
    "м",
    "м²",
    "м³",
    "л",
    "шт.",
    "рулон",
    "упаковка",
    "Другое",
)

MATERIALS_CREATE_FORBIDDEN: frozenset[str] = frozenset(
    {
        "condition",
        "brand",
        "model",
        "manufacturer",
        "country",
        "grade",
        "standard",
        "color",
        "dimensions",
        "weight",
        "quantity",
        "moq",
        "wholesale_price",
        "tech_specs",
        "material_type",
        "available_quantity",
        "stock",
    }
)

_ALWAYS_CREATE: frozenset[str] = frozenset(
    {
        MATERIALS_KIND_KEY,
        MATERIALS_SELLER_KEY,
        MATERIALS_PRICE_BASIS_KEY,
        "price",
        "negotiable",
        "contact_methods",
    }
)

# Package B Search SoT — geo is shared Search UX (not CategoryFilter rows).
MATERIALS_V2_SEARCH_ALLOWLIST: frozenset[str] = frozenset(
    {
        MATERIALS_KIND_KEY,
        MATERIALS_SELLER_KEY,
        "geo",
    }
)
MATERIALS_V2_SEARCH_EAV_KEYS: frozenset[str] = frozenset(
    {
        MATERIALS_KIND_KEY,
        MATERIALS_SELLER_KEY,
    }
)
MATERIALS_V2_SEARCH_EXCLUDE: frozenset[str] = frozenset(
    set(MATERIALS_CREATE_FORBIDDEN)
    | {
        "price",
        "negotiable",
        "contact_methods",
        MATERIALS_PRICE_BASIS_KEY,
        "condition",
        "currency",
    }
)
MATERIALS_V2_SEARCH_POLICY = "SIMPLE"

MATERIALS_V2_SECTION_SLUGS: dict[str, str] = {
    "fabric": "materials-tkani-i-tekstilnoe-syre",
    "notions": "materials-shveynaya-furnitura",
    "leather": "materials-kozha-i-kozhzameniteli",
    "yarn": "materials-nitki-pryazha-i-volokno",
    "metal": "materials-metally-metallicheskoe-syre",
    "wood": "materials-drevesina-i-drevesnoe-syre",
    "plastic": "materials-plastik-i-polimernoe-syre",
    "rubber": "materials-rezina-i-kauchuk",
    "paper": "materials-bumaga-i-karton",
    "glass": "materials-steklo-i-stekolnoe-syre",
    "chemical": "materials-himicheskoe-syre",
    "paint": "materials-lakokrasochnoe-syre",
    "pack": "materials-upakovochnye-materialy",
    "food": "materials-pischevoe-syre-i-ingredienty",
    "cosmetic": "materials-syre-dlya-kosmetiki-parfyumerii",
    "household": "materials-syre-dlya-bytovoy-himii",
    "jewelry": "materials-dlya-yuvelirnogo-proizvodstva",
    "other": "materials-prochee-syre-dlya-proizvodstva",
}

MATERIALS_SCRAP_KINDS: frozenset[str] = frozenset(
    {
        "Вторсырьё",
        "Отходы производства",
        "Макулатура",
        "Стеклобой",
        "Резиновая крошка",
    }
)

# Hazardous / regulated — taxonomy KEEP; enforcement out of scope.
HazardClass = Literal["KEEP_CURRENT", "POLICY_REVIEW", "PRODUCT_DECISION"]
MATERIALS_HAZARDOUS_MATRIX: dict[str, HazardClass] = {
    "Растворители": "POLICY_REVIEW",
    "Технические спирты": "POLICY_REVIEW",
    "Катализаторы": "POLICY_REVIEW",
    "Пластификаторы": "POLICY_REVIEW",
    "Смолы": "KEEP_CURRENT",
    "Растворители для красок": "POLICY_REVIEW",
    "ПАВ для косметики": "POLICY_REVIEW",
    "ПАВ для бытовой химии": "POLICY_REVIEW",
}

# Ambiguous metal wording — keep both; identity differs feedstock vs construction.
MATERIALS_METAL_LABEL_NOTE = (
    "Materials «Листовой прокат» = production metal stock; "
    "Repair «Листовой металл» = finished/construction metal goods. "
    "Labels retained without merge/rename in this cleanup."
)

MATERIALS_V2_SECTION_KINDS: dict[str, tuple[str, ...]] = {
    "fabric": (
        "Хлопковые ткани",
        "Шёлк",
        "Льняные ткани",
        "Шерстяные ткани",
        "Синтетические ткани",
        "Трикотажное полотно",
        "Подкладочные ткани",
        "Другие ткани",
    ),
    "notions": (
        "Молнии",
        "Пуговицы",
        "Кнопки",
        "Крючки и петли",
        "Тесьма",
        "Резинка",
        "Люверсы",
        "Другая швейная фурнитура",
    ),
    "leather": (
        "Натуральная кожа",
        "Кожзаменитель",
        "Замша",
        "Мех",
        "Спилок",
        "Другая кожа и кожзам",
    ),
    "yarn": (
        "Пряжа",
        "Нитки",
        "Шерсть",
        "Хлопковое волокно",
        "Шёлковое волокно",
        "Синтетическое волокно",
        "Другие нитки и волокно",
    ),
    "metal": (
        "Листовой прокат",
        "Сортовой прокат",
        "Катанка",
        "Цветные металлы",
        "Нержавеющая сталь",
        "Чугун",
        "Другое металлическое сырьё",
    ),
    "wood": (
        "Брёвна",
        "Пиловочник",
        "Шпон",
        "Щепа",
        "Опилки",
        "Горбыль",
        "Другое древесное сырьё",
    ),
    "plastic": (
        "Гранулы полиэтилена",
        "Гранулы полипропилена",
        "Гранулы ПВХ",
        "ПЭТ",
        "АБС-пластик",
        "Другое полимерное сырьё",
    ),
    "rubber": (
        "Натуральный каучук",
        "Синтетический каучук",
        "Резиновая крошка",
        "Резиновые смеси",
        "Силикон",
        "Другая резина и каучук",
    ),
    "paper": (
        "Бумага в рулонах",
        "Картон",
        "Целлюлоза",
        "Макулатура",
        "Крафт",
        "Другая бумага и картон",
    ),
    "glass": (
        "Листовое стекло",
        "Стеклобой",
        "Стеклотара",
        "Зеркальное полотно",
        "Другое стекольное сырьё",
    ),
    "chemical": (
        "Смолы",
        "Растворители",
        "Технические спирты",
        "Пластификаторы",
        "Катализаторы",
        "Другое химическое сырьё",
    ),
    "paint": (
        "Пигменты",
        "Связующие",
        "Олифа",
        "Растворители для красок",
        "Колеры оптом",
        "Другое лакокрасочное сырьё",
    ),
    "pack": (
        "Стретч-плёнка",
        "Плёнка упаковочная",
        "Гофрокартон",
        "Пакеты",
        "Скотч",
        "Этикетки",
        "Другие упаковочные материалы",
    ),
    "food": (
        "Сухое молоко",
        "Сыворотка",
        "Патока",
        "Солод",
        "Желатин",
        "Ароматизаторы",
        "Пищевые добавки",
        "Какао-бобы",
        "Другое пищевое сырьё",
    ),
    "cosmetic": (
        "Базовые масла",
        "Эфирные масла",
        "ПАВ для косметики",
        "Отдушки для косметики",
        "Воски",
        "Пигменты для косметики",
        "Другое косметическое сырьё",
    ),
    "household": (
        "Кальцинированная сода",
        "ПАВ для бытовой химии",
        "Отдушки для химии",
        "Загустители",
        "Наполнители",
        "Другое сырьё для бытовой химии",
    ),
    "jewelry": (
        "Золото",
        "Серебро",
        "Драгоценные камни",
        "Ювелирная фурнитура",
        "Ювелирная проволока",
        "Другое ювелирное сырьё",
    ),
    "other": (
        "Вторсырьё",
        "Отходы производства",
        "Образцы",
        "Другое сырьё",
    ),
}

# Finished construction goods must not appear as Materials kinds.
MATERIALS_REPAIR_FINISHED_BANNED: frozenset[str] = frozenset(
    {
        "Доска",
        "Брус",
        "Фанера",
        "Вагонка",
        "Цемент",
        "Кирпич",
        "Арматура",
        "Трубы стальные",
        "Интерьерные краски",
        "Фасадные краски",
        "Эмали",
        "Лаки",
        "Грунтовки",
        "Гипсокартон",
        "Пенопласт и пеноплекс",
        "Плёнки и мембраны",
    }
)
MATERIALS_FOOD_GRAIN_BANNED: frozenset[str] = frozenset(
    {
        "Пшеница",
        "Ячмень",
        "Кукуруза",
        "Овёс",
        "Мука",
        "Сахар",
        "Дрожжи",
        "Крахмал",
        "Какао",
        "Мёд",
        "Молоко",
    }
)
MATERIALS_FEED_BANNED: frozenset[str] = frozenset(
    {"Сено", "Комбикорм", "Кормовые добавки", "Другие корма"}
)


def materials_v2_all_kinds() -> tuple[str, ...]:
    out: list[str] = []
    for kinds in MATERIALS_V2_SECTION_KINDS.values():
        out.extend(kinds)
    return tuple(out)


def materials_v2_kind_count() -> int:
    return len(materials_v2_all_kinds())


def materials_v2_condition_decision(_kind: str) -> Literal["NO"]:
    return "NO"


def materials_v2_assert_cleanup_contracts() -> None:
    assert MATERIALS_ROOT_SLUG == "materials"
    assert MATERIALS_ROOT_LABEL == "Материалы, сырьё и товары для производства"
    assert MATERIALS_V2_EXPECTED_L2_COUNT == 18
    assert len(MATERIALS_V2_CANONICAL_LEAVES) == 18
    assert MATERIALS_V2_IMPORT_SLUG in MATERIALS_V2_RETIRED_SLUGS
    assert MATERIALS_V2_LEGACY_TRIAD_SLUGS.isdisjoint(MATERIALS_V2_CANONICAL_SLUGS)
    assert MATERIALS_V2_IMPORT_SLUG not in MATERIALS_V2_CANONICAL_SLUGS
    assert MATERIALS_SELLER_TARGET == ("Частное лицо", "Магазин", "Другой")
    assert MATERIALS_CONDITION_POLICY == "ABSENT"
    assert FOOD_TARA_GAP_STATUS == "STILL_OPEN"
    assert len(MATERIALS_PRICE_BASIS_OPTIONS) == 11
    assert MATERIALS_PRICE_BASIS_REQUIRED is False
    assert "condition" in MATERIALS_CREATE_FORBIDDEN
    assert "quantity" in MATERIALS_CREATE_FORBIDDEN
    assert "moq" in MATERIALS_CREATE_FORBIDDEN
    assert set(MATERIALS_V2_SECTION_SLUGS.values()) == MATERIALS_V2_CANONICAL_SLUGS
    assert set(MATERIALS_V2_SECTION_SLUGS) == set(MATERIALS_V2_SECTION_KINDS)
    kinds = set(materials_v2_all_kinds())
    assert len(kinds) == materials_v2_kind_count()
    assert MATERIALS_REPAIR_FINISHED_BANNED.isdisjoint(kinds)
    assert MATERIALS_FOOD_GRAIN_BANNED.isdisjoint(kinds)
    assert MATERIALS_FEED_BANNED.isdisjoint(kinds)
    assert "Партия под заказ" not in kinds
    assert "Контейнерная поставка" not in kinds
    for kind in kinds:
        assert materials_v2_condition_decision(kind) == "NO"


def materials_v2_package_a_field_target() -> dict[str, Any]:
    return {
        "required": (
            MATERIALS_KIND_KEY,
            MATERIALS_SELLER_KEY,
            "price",
            "contact_methods",
        ),
        "optional": (MATERIALS_PRICE_BASIS_KEY, "negotiable"),
        "absent": tuple(sorted(MATERIALS_CREATE_FORBIDDEN)),
        "seller": MATERIALS_SELLER_TARGET,
        "price_basis_options": MATERIALS_PRICE_BASIS_OPTIONS,
        "condition": MATERIALS_CONDITION_POLICY,
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


def materials_v2_assert_package_a_contracts() -> None:
    materials_v2_assert_cleanup_contracts()
    if materials_v2_kind_count() != 117:
        raise RuntimeError(
            f"Materials Package A expects 117 kinds, got {materials_v2_kind_count()}"
        )
    if MATERIALS_SELLER_TARGET != GOODS_SELLER_CHOICES:
        raise RuntimeError("Materials seller must match goods shared seller")
    if MATERIALS_CONDITION_POLICY != "ABSENT":
        raise RuntimeError("Materials Condition must stay ABSENT")
    if MATERIALS_PRICE_BASIS_OPTIONS != (
        "кг",
        "г",
        "тонна",
        "м",
        "м²",
        "м³",
        "л",
        "шт.",
        "рулон",
        "упаковка",
        "Другое",
    ):
        raise RuntimeError("Materials price_basis options drifted")
    if MATERIALS_PRICE_BASIS_REQUIRED is not False:
        raise RuntimeError("Materials price_basis must be optional")
    if MATERIALS_KIND_KEY != "materials_kind" or MATERIALS_KIND_LABEL != "Товар":
        raise RuntimeError("Materials kind key/label lock broken")
    if FOOD_TARA_GAP_STATUS != "STILL_OPEN":
        raise RuntimeError("Food Tara GAP must remain STILL_OPEN")
    if MATERIALS_PRICE_BASIS_KEY in MATERIALS_CREATE_FORBIDDEN:
        raise RuntimeError("price_basis must not be forbidden")
    if "condition" not in MATERIALS_CREATE_FORBIDDEN:
        raise RuntimeError("condition must stay forbidden")
    if MATERIALS_V2_SEARCH_ALLOWLIST != {
        MATERIALS_KIND_KEY,
        MATERIALS_SELLER_KEY,
        "geo",
    }:
        raise RuntimeError("Materials Search allowlist prep drifted")
    if MATERIALS_PRICE_BASIS_KEY not in MATERIALS_V2_SEARCH_EXCLUDE:
        raise RuntimeError("price_basis must be Search-excluded")
    if "condition" not in MATERIALS_V2_SEARCH_EXCLUDE:
        raise RuntimeError("condition must be Search-excluded")


def build_materials_v2_core_fields() -> dict[str, list]:
    """Create cores for all 18 active Materials L2 (Package A SoT)."""
    materials_v2_assert_package_a_contracts()
    out: dict[str, list] = {}

    for section_key, slug in MATERIALS_V2_SECTION_SLUGS.items():
        kinds = list(MATERIALS_V2_SECTION_KINDS[section_key])
        fields: list = [
            _dep_field(
                MATERIALS_KIND_KEY,
                MATERIALS_KIND_LABEL,
                CategoryFieldType.enum,
                True,
                10,
                _choices(*kinds),
                hint="Какое сырьё?",
            ),
            _dep_field(
                MATERIALS_SELLER_KEY,
                MATERIALS_SELLER_LABEL,
                CategoryFieldType.enum,
                True,
                20,
                _choices(*MATERIALS_SELLER_TARGET),
            ),
            _dep_field(
                MATERIALS_PRICE_BASIS_KEY,
                MATERIALS_PRICE_BASIS_LABEL,
                CategoryFieldType.enum,
                False,
                40,
                _choices(*MATERIALS_PRICE_BASIS_OPTIONS),
                hint="Цена за единицу (не количество на складе)",
            ),
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

        for row in fields:
            key = row[0]
            if key in MATERIALS_CREATE_FORBIDDEN:
                raise RuntimeError(f"forbidden Create field {slug}.{key}")
            if key not in _ALWAYS_CREATE:
                raise RuntimeError(f"unapproved Create field {slug}.{key}")
            opts = row[5]
            if opts and opts.get("choices") is not None and len(opts["choices"]) == 0:
                raise RuntimeError(f"empty picker {slug}.{key}")

        out[slug] = fields
    return out


def materials_v2_all_kind_audit() -> list[dict[str, Any]]:
    """All-117 kind audit rows (Package A)."""
    cores = build_materials_v2_core_fields()
    rows: list[dict[str, Any]] = []
    for section_key, slug in MATERIALS_V2_SECTION_SLUGS.items():
        kinds = MATERIALS_V2_SECTION_KINDS[section_key]
        fields = cores[slug]
        keys = [r[0] for r in fields]
        kind_row = next(r for r in fields if r[0] == MATERIALS_KIND_KEY)
        kind_opts = [c["value"] for c in kind_row[5]["choices"]]
        seller_row = next(r for r in fields if r[0] == MATERIALS_SELLER_KEY)
        seller_opts = [c["value"] for c in seller_row[5]["choices"]]
        basis_row = next(r for r in fields if r[0] == MATERIALS_PRICE_BASIS_KEY)
        basis_opts = [c["value"] for c in basis_row[5]["choices"]]
        specials = [
            k
            for k in keys
            if k
            not in {
                MATERIALS_KIND_KEY,
                MATERIALS_SELLER_KEY,
                "price",
                "negotiable",
                "contact_methods",
            }
        ]
        for kind in kinds:
            ownership = "MATERIALS"
            if kind in MATERIALS_REPAIR_FINISHED_BANNED:
                ownership = "REPAIR"
            elif kind in MATERIALS_FOOD_GRAIN_BANNED:
                ownership = "FOOD_AGRI"
            elif kind in MATERIALS_FEED_BANNED:
                ownership = "ANIMALS"
            rows.append(
                {
                    "kind": kind,
                    "section": section_key,
                    "slug": slug,
                    "materials_kind_valid": kind in kind_opts,
                    "condition": "NO",
                    "condition_in_schema": "condition" not in keys,
                    "seller": seller_opts,
                    "price": "price" in keys,
                    "price_basis": basis_opts,
                    "price_basis_optional": basis_row[3] is False,
                    "special_count": len(specials),
                    "forbidden": sorted(set(keys) & MATERIALS_CREATE_FORBIDDEN),
                    "components": {
                        MATERIALS_KIND_KEY: "enum",
                        MATERIALS_SELLER_KEY: "enum",
                        MATERIALS_PRICE_BASIS_KEY: "enum",
                        "price": "price",
                        "negotiable": "enum",
                        "contact_methods": "enum",
                    },
                    "ownership": ownership,
                }
            )
    return rows


def materials_v2_complexity_histogram() -> dict[str, int]:
    """special_count histogram — expected all kinds share price_basis only (=1)."""
    hist = {"0": 0, "1": 0, "2": 0, "3+": 0}
    for row in materials_v2_all_kind_audit():
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


def build_materials_v2_search_filters() -> dict[str, list]:
    """Package B Search SoT per canonical Materials L2.

    Explicit allowlist only: materials_kind + seller_type.
    Condition / price_basis / price / negotiable / contacts / tech never Search.
    Geo is shared Search UX, not CategoryFilter rows.
    """
    cores = build_materials_v2_core_fields()
    out: dict[str, list] = {}
    for slug, fields in cores.items():
        filters: list = []
        for key, label, _ftype, _required, sort, options, _hint in fields:
            if key not in MATERIALS_V2_SEARCH_EAV_KEYS:
                continue
            if key in MATERIALS_V2_SEARCH_EXCLUDE:
                continue
            if key not in MATERIALS_V2_SEARCH_ALLOWLIST:
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
    if set(out) != MATERIALS_V2_CANONICAL_SLUGS:
        raise RuntimeError(
            "Materials Search filter map != canonical L2 slugs: "
            f"extra={sorted(set(out) - MATERIALS_V2_CANONICAL_SLUGS)} "
            f"missing={sorted(MATERIALS_V2_CANONICAL_SLUGS - set(out))}"
        )
    return out


def materials_v2_search_kind_audit_row(
    section_key: str, slug: str, kind: str
) -> dict[str, Any]:
    """All-kind Search audit row (independent of Create components)."""
    ownership = "MATERIALS"
    if kind in MATERIALS_REPAIR_FINISHED_BANNED:
        ownership = "REPAIR"
    elif kind in MATERIALS_FOOD_GRAIN_BANNED:
        ownership = "FOOD_AGRI"
    elif kind in MATERIALS_FEED_BANNED:
        ownership = "ANIMALS"
    return {
        "l2": slug,
        "section": section_key,
        "kind": kind,
        "search_materials_kind": "YES",
        "search_seller": "YES",
        "search_condition": "NO",
        "search_price_basis": "NO",
        "search_price": "NO",
        "search_negotiable": "NO",
        "search_contacts": "NO",
        "search_quantity": "NO",
        "search_moq": "NO",
        "search_wholesale": "NO",
        "search_brand": "NO",
        "search_model": "NO",
        "search_grade": "NO",
        "search_tech": "NO",
        "search_geo": "YES",
        "retired_resurrected": slug in MATERIALS_V2_RETIRED_SLUGS,
        "ownership": ownership,
        "visible_search_keys": [MATERIALS_KIND_KEY, MATERIALS_SELLER_KEY],
        "ui_components": {
            MATERIALS_KIND_KEY: "multi_select",
            MATERIALS_SELLER_KEY: "multi_select",
            "geo": "region_city",
        },
    }


def materials_v2_all_search_kind_audit() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for section_key, slug in MATERIALS_V2_SECTION_SLUGS.items():
        for kind in MATERIALS_V2_SECTION_KINDS[section_key]:
            rows.append(
                materials_v2_search_kind_audit_row(section_key, slug, kind)
            )
    return rows


def materials_v2_assert_package_b_contracts() -> None:
    materials_v2_assert_package_a_contracts()
    if MATERIALS_V2_SEARCH_POLICY != "SIMPLE":
        raise RuntimeError("Materials Search policy must stay SIMPLE")
    if MATERIALS_V2_SEARCH_EAV_KEYS != {
        MATERIALS_KIND_KEY,
        MATERIALS_SELLER_KEY,
    }:
        raise RuntimeError("Materials Search EAV keys drifted")
    if "geo" not in MATERIALS_V2_SEARCH_ALLOWLIST:
        raise RuntimeError("geo must remain on Search allowlist")
    if MATERIALS_PRICE_BASIS_KEY in MATERIALS_V2_SEARCH_EAV_KEYS:
        raise RuntimeError("price_basis must not be Search EAV")
    if "condition" in MATERIALS_V2_SEARCH_EAV_KEYS:
        raise RuntimeError("condition must not be Search EAV")
    filters = build_materials_v2_search_filters()
    if set(filters) != MATERIALS_V2_CANONICAL_SLUGS:
        raise RuntimeError("Package B Search map ≠ canonical L2")
    if set(filters) & MATERIALS_V2_RETIRED_SLUGS:
        raise RuntimeError("Retired Materials slugs must not appear in Search")
    for slug, rows in filters.items():
        keys = {r[0] for r in rows}
        if keys != MATERIALS_V2_SEARCH_EAV_KEYS:
            raise RuntimeError(f"Search keys mismatch: {slug} → {sorted(keys)}")
        if keys & MATERIALS_CREATE_FORBIDDEN:
            raise RuntimeError(f"Forbidden Search keys: {slug}")
        if keys & {
            "price",
            "negotiable",
            "contact_methods",
            MATERIALS_PRICE_BASIS_KEY,
            "condition",
        }:
            raise RuntimeError(f"Create-only leaked into Search: {slug}")
        if not rows:
            raise RuntimeError(f"Empty Search filters: {slug}")
    audit = materials_v2_all_search_kind_audit()
    if len(audit) != 117:
        raise RuntimeError(f"Search audit expects 117 kinds, got {len(audit)}")
    if any(r["search_condition"] != "NO" for r in audit):
        raise RuntimeError("Condition must be ABSENT from Materials Search")
    if any(r["search_price_basis"] != "NO" for r in audit):
        raise RuntimeError("price_basis must be ABSENT from Materials Search")
    if any(r["ownership"] != "MATERIALS" for r in audit):
        raise RuntimeError("Search audit ownership drift")
    if FOOD_TARA_GAP_STATUS != "STILL_OPEN":
        raise RuntimeError("Food Tara GAP must remain STILL_OPEN in Package B")

