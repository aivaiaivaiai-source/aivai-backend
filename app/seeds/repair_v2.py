# -*- coding: utf-8 -*-
"""Repair & Construction V2 — canonical goods taxonomy + Create/Search SoT.

Package A: 28 goods L2, Create core fields (repair_kind, seller, condition,
dependents, price «Цена», negotiable, contacts).

Package B: Search filters / facets — useful product filters only
(no price range, negotiable, contacts). Geo stays on shared Flutter Search.
"""
from __future__ import annotations

from typing import Any

from app.models.category_enums import (
    CategoryEntityType,
    CategoryFieldType,
    CategoryFilterType,
)
from app.seeds.repair_sections_catalog import REPAIR_SECTIONS

REPAIR_ROOT_SLUG = "repair-construction"
REPAIR_ROOT_LABEL = "Ремонт и строительство"

# Canonical L2: (slug, label, sort_order) — keep existing DB ids 933–960.
REPAIR_V2_CANONICAL_LEAVES: tuple[tuple[str, str, int], ...] = (
    ("repair-construction-stroitelnye-materialy", "ЖБИ, сетки и плёнки", 10),
    ("repair-construction-kirpichi-i-stroitelnye-bloki", "Кирпичи и строительные блоки", 20),
    ("repair-construction-tsement-smesi-sypuchie-materialy", "Цемент/смеси/сыпучие материалы", 30),
    ("repair-construction-pilomaterialy", "Пиломатериалы", 40),
    ("repair-construction-metalloprokat", "Металлопрокат", 50),
    ("repair-construction-krovlya-i-vodostoki", "Кровля и водостоки", 60),
    ("repair-construction-fasady-i-uteplenie", "Фасады и утепление", 70),
    ("repair-construction-okna-i-dveri", "Окна и двери", 80),
    ("repair-construction-napolnye-pokrytiya", "Напольные покрытия", 90),
    ("repair-construction-stenovye-materialy-pokrytiya", "Стеновые материалы", 100),
    ("repair-construction-potolki-i-potolochnye-sistemy", "Потолки и потолочные системы", 110),
    ("repair-construction-plitka-i-keramogranit", "Плитка и керамогранит", 120),
    ("repair-construction-lakokrasochnye-materialy", "Краски и лаки", 130),
    ("repair-construction-klei-i-stroitelnaya-himiya", "Клеи и строительная химия", 140),
    ("repair-construction-otdelochnye-materialy", "Плинтусы и декор", 150),
    ("repair-construction-santehnika-i-vodosnabzhenie", "Сантехника и водоснабжение", 160),
    ("repair-construction-elektrika-i-osveschenie", "Электрика и освещение", 170),
    ("repair-construction-otoplenie-ventilyatsiya-i-klimat", "Отопление, вентиляция и климат", 180),
    ("repair-construction-instrumenty", "Инструменты", 190),
    ("repair-construction-elektroinstrumenty", "Электроинструменты", 200),
    ("repair-construction-spetsodezhda-i-sredstva-zaschity", "Спецодежда и средства защиты", 210),
    ("repair-construction-stroitelnoe-oborudovanie", "Строительное оборудование", 220),
    ("repair-construction-lestnitsy-i-stroitelnye-lesa", "Лестницы и строительные леса", 230),
    ("repair-construction-zabory-vorota-i-ograzhdeniya", "Заборы, ворота и ограждения", 240),
    ("repair-construction-navesy-i-metallokonstruktsii", "Навесы и металлоконструкции", 250),
    ("repair-construction-kovanye-izdeliya", "Кованые изделия", 260),
    ("repair-construction-krepezh-i-rashodnye-materialy", "Крепёж и расходные материалы", 270),
    ("repair-construction-prochee-dlya-remonta-stroitelstva", "Прочее для ремонта/строительства", 280),
)

REPAIR_V2_CANONICAL_SLUGS: frozenset[str] = frozenset(
    slug for slug, _label, _sort in REPAIR_V2_CANONICAL_LEAVES
)

REPAIR_V2_RETIRED_SLUGS: frozenset[str] = frozenset(
    {
        "repair-building",
        "construction-work",
        "repair-tools",
    }
)

# Internal section key → canonical DB slug (identity lock).
REPAIR_V2_SECTION_TO_SLUG: dict[str, str] = {
    "materials": "repair-construction-stroitelnye-materialy",
    "bricks": "repair-construction-kirpichi-i-stroitelnye-bloki",
    "mixes": "repair-construction-tsement-smesi-sypuchie-materialy",
    "lumber": "repair-construction-pilomaterialy",
    "metal": "repair-construction-metalloprokat",
    "roof": "repair-construction-krovlya-i-vodostoki",
    "facade": "repair-construction-fasady-i-uteplenie",
    "windows": "repair-construction-okna-i-dveri",
    "floors": "repair-construction-napolnye-pokrytiya",
    "walls": "repair-construction-stenovye-materialy-pokrytiya",
    "ceilings": "repair-construction-potolki-i-potolochnye-sistemy",
    "tile": "repair-construction-plitka-i-keramogranit",
    "paint": "repair-construction-lakokrasochnye-materialy",
    "chemistry": "repair-construction-klei-i-stroitelnaya-himiya",
    "finishing": "repair-construction-otdelochnye-materialy",
    "plumbing": "repair-construction-santehnika-i-vodosnabzhenie",
    "electrical": "repair-construction-elektrika-i-osveschenie",
    "climate": "repair-construction-otoplenie-ventilyatsiya-i-klimat",
    "hand-tools": "repair-construction-instrumenty",
    "power-tools": "repair-construction-elektroinstrumenty",
    "ppe": "repair-construction-spetsodezhda-i-sredstva-zaschity",
    "equipment": "repair-construction-stroitelnoe-oborudovanie",
    "scaffolding": "repair-construction-lestnitsy-i-stroitelnye-lesa",
    "fences": "repair-construction-zabory-vorota-i-ograzhdeniya",
    "structures": "repair-construction-navesy-i-metallokonstruktsii",
    "forged": "repair-construction-kovanye-izdeliya",
    "fasteners": "repair-construction-krepezh-i-rashodnye-materialy",
    "other": "repair-construction-prochee-dlya-remonta-stroitelstva",
}

# Goods-word aliases → canonical goods leaves.
REPAIR_V2_GOODS_ALIAS_REMAP: dict[str, str] = {
    "плитка": "repair-construction-plitka-i-keramogranit",
    "кровля": "repair-construction-krovlya-i-vodostoki",
    "забор": "repair-construction-zabory-vorota-i-ograzhdeniya",
    "перфоратор": "repair-construction-elektroinstrumenty",
    "болгарка": "repair-construction-elektroinstrumenty",
    "стройинструмент": "repair-construction-instrumenty",
    "люстра": "repair-construction-elektrika-i-osveschenie",
    "бра": "repair-construction-elektrika-i-osveschenie",
    "торшер": "repair-construction-elektrika-i-osveschenie",
    "лампа": "repair-construction-elektrika-i-osveschenie",
    "освещение": "repair-construction-elektrika-i-osveschenie",
    "электрика": "repair-construction-elektrika-i-osveschenie",
}

# Explicit work-intent aliases → Services construction leaf.
REPAIR_V2_WORK_ALIAS_REMAP: dict[str, str] = {
    "ремонт квартиры": "services-stroitelnye-i-remontnye-uslugi",
    "строительные работы": "services-stroitelnye-i-remontnye-uslugi",
    "отделка": "services-stroitelnye-i-remontnye-uslugi",
    "строительство": "services-stroitelnye-i-remontnye-uslugi",
    "фундамент": "services-stroitelnye-i-remontnye-uslugi",
    "штукатурка": "services-stroitelnye-i-remontnye-uslugi",
}

REPAIR_V2_ALIAS_REMAP: dict[str, str] = {
    **REPAIR_V2_GOODS_ALIAS_REMAP,
    **REPAIR_V2_WORK_ALIAS_REMAP,
}

REPAIR_V2_ENTITY_TYPE = CategoryEntityType.construction

_FILTER_LABEL_TO_KEY: dict[str, str] = {
    "Продавец": "seller_type",
    "Состояние": "condition",
    "Фасовка": "packaging",
    "Влажность": "moisture",
    "Толщина": "thickness",
    "Стеклопакет": "glazing",
    "Класс": "class_grade",
    "Упаковка": "package_state",
    "Объём": "volume",
    "Цоколь": "lamp_base",
    "Питание": "power_source",
    "Размер одежды": "clothing_size",
    "Размер обуви": "shoe_size",
    "Топливо": "fuel",
}

_CONTACT_METHODS = (
    "Только чат",
    "Только телефон",
    "Чат + телефон",
    "Чат + Wapp",
    "Телефон + Wapp",
    "Чат + Тел. + Wapp",
)

_NEGOTIABLE = ("Есть торг", "Без торга")


def _choices(*labels: str) -> dict[str, Any]:
    return {"choices": [{"value": label, "label": label} for label in labels]}


def _dep_choices(
    *labels: str,
    field: str,
    values: tuple[str, ...] | list[str],
) -> dict[str, Any]:
    opts = _choices(*labels)
    opts["depends_on"] = {"field": field, "values": list(values)}
    return opts


def _field(
    key: str,
    label: str,
    ftype: CategoryFieldType,
    required: bool,
    sort: int,
    options: dict[str, Any] | None = None,
    *,
    hint: str | None = None,
) -> tuple:
    return (key, label, ftype, required, sort, options, hint)


def _labels(items: list[dict[str, str]]) -> tuple[str, ...]:
    return tuple(str(i["label"]) for i in items)


def build_repair_v2_core_fields() -> dict[str, list]:
    """Create SoT core fields per canonical goods leaf."""
    out: dict[str, list] = {}
    for section_key, slug in REPAIR_V2_SECTION_TO_SLUG.items():
        catalog = REPAIR_SECTIONS[section_key]
        assert catalog["category_slug"] == slug, (
            section_key,
            catalog["category_slug"],
            slug,
        )
        kinds = _labels(catalog["roles"])
        fields: list = [
            _field(
                "repair_kind",
                "Товар",
                CategoryFieldType.enum,
                True,
                10,
                _choices(*kinds),
                hint=str(catalog.get("question") or "Какой товар?"),
            ),
        ]
        sort = 20
        for group in catalog.get("filters") or []:
            label = str(group["label"])
            key = _FILTER_LABEL_TO_KEY.get(label)
            if key is None:
                continue
            option_labels = _labels(group.get("options") or [])
            applies = group.get("applies_to")
            if applies:
                opts = _dep_choices(
                    *option_labels,
                    field="repair_kind",
                    values=list(applies),
                )
                required = False
            else:
                opts = _choices(*option_labels)
                # Seller always required; condition required when present for branch.
                required = key in {"seller_type", "condition"}
            fields.append(
                _field(
                    key,
                    label,
                    CategoryFieldType.enum,
                    required,
                    sort,
                    opts,
                )
            )
            sort += 10
        fields.extend(
            [
                _field(
                    "price",
                    "Цена",
                    CategoryFieldType.price,
                    True,
                    200,
                    hint="Цена товара",
                ),
                _field(
                    "negotiable",
                    "Торг",
                    CategoryFieldType.enum,
                    False,
                    210,
                    _choices(*_NEGOTIABLE),
                ),
                _field(
                    "contact_methods",
                    "Способы связи",
                    CategoryFieldType.enum,
                    True,
                    220,
                    _choices(*_CONTACT_METHODS),
                ),
            ]
        )
        out[slug] = fields
    assert set(out) == REPAIR_V2_CANONICAL_SLUGS
    return out


# ---------------------------------------------------------------------------
# Package B — Search filter usefulness
# SEARCH YES: repair_kind, seller_type, condition, packaging, moisture,
#   thickness, glazing, class_grade, package_state, volume, lamp_base,
#   power_source, clothing_size, shoe_size, fuel
# SEARCH NO (Create-only): price, negotiable, contact_methods
# ---------------------------------------------------------------------------

_SEARCH_YES_KEYS: frozenset[str] = frozenset(
    {
        "repair_kind",
        "seller_type",
        "condition",
        "packaging",
        "moisture",
        "thickness",
        "glazing",
        "class_grade",
        "package_state",
        "volume",
        "lamp_base",
        "power_source",
        "clothing_size",
        "shoe_size",
        "fuel",
    }
)

_SEARCH_KIND_LABEL = "Вид товара"


def _filter_opts(
    *labels: str,
    depends_on: dict[str, Any] | None = None,
) -> dict[str, Any]:
    cfg: dict[str, Any] = {
        "options": [{"value": label, "label": label} for label in labels]
    }
    if depends_on is not None:
        cfg["depends_on"] = depends_on
    return cfg


def _search_filter(
    key: str,
    label: str,
    ftype: CategoryFilterType,
    sort: int,
    options: dict[str, Any] | None,
) -> tuple:
    return (key, label, ftype, sort, options)


def build_repair_v2_search_filters() -> dict[str, list]:
    """Search SoT per canonical goods leaf — Backend filter metadata authority.

    Multi-select for kind / seller / condition / dependents so facets share
    the generic ``A||B`` attrs contract. Price / negotiable / contacts omitted.
    """
    out: dict[str, list] = {}
    for section_key, slug in REPAIR_V2_SECTION_TO_SLUG.items():
        catalog = REPAIR_SECTIONS[section_key]
        kinds = _labels(catalog["roles"])
        filters: list = [
            _search_filter(
                "repair_kind",
                _SEARCH_KIND_LABEL,
                CategoryFilterType.multi_select,
                10,
                _filter_opts(*kinds),
            ),
        ]
        sort = 20
        for group in catalog.get("filters") or []:
            label = str(group["label"])
            key = _FILTER_LABEL_TO_KEY.get(label)
            if key is None or key not in _SEARCH_YES_KEYS:
                continue
            option_labels = _labels(group.get("options") or [])
            applies = group.get("applies_to")
            depends = (
                {"field": "repair_kind", "values": list(applies)}
                if applies
                else None
            )
            filters.append(
                _search_filter(
                    key,
                    label,
                    CategoryFilterType.multi_select,
                    sort,
                    _filter_opts(*option_labels, depends_on=depends),
                )
            )
            sort += 10
        out[slug] = filters
    assert set(out) == REPAIR_V2_CANONICAL_SLUGS
    return out
