# -*- coding: utf-8 -*-
"""Продажа «Материалы, сырьё и товары для производства».

Вид — само сырьё для цеха, не готовый товар. Доска, брус, фанера, цемент,
арматура и готовые краски остаются в ремонте. Мука, сахар и зерно — в продуктах.
Бумага для офиса — в канцтоварах. Кольца и серьги — в одежде. Шампуни и мыло —
в красоте. Пряжа и нитки живут здесь, не в рукоделии.
Import/wholesale L2 retired (sales mode ≠ product identity).
Condition absent for all Materials kinds (Archi).
"""
from __future__ import annotations

from typing import Any

from app.seeds.materials_v2 import (
    MATERIALS_PRICE_BASIS_LABEL,
    MATERIALS_PRICE_BASIS_OPTIONS,
    MATERIALS_SELLER_TARGET,
    MATERIALS_V2_SECTION_KINDS,
)
from app.seeds.shared_goods_create_contract import GOODS_SELLER_CHOICES


def _item(label: str) -> dict[str, Any]:
    return {"value": label, "label": label}


def _opts(*labels: str) -> list[dict[str, Any]]:
    return [_item(label) for label in labels]


def _group(label: str, options: tuple[str, ...]) -> dict[str, Any]:
    return {"label": label, "options": _opts(*options)}


def _seller() -> dict[str, Any]:
    return _group("Продавец", GOODS_SELLER_CHOICES)


def _price_basis() -> dict[str, Any]:
    return _group(MATERIALS_PRICE_BASIS_LABEL, MATERIALS_PRICE_BASIS_OPTIONS)


def _filters() -> list[dict[str, Any]]:
    # Offline/testing mirror of Package A Create filters (not Search SoT).
    return [_seller(), _price_basis()]


def _section(
    slug: str,
    label: str,
    kinds: tuple[str, ...],
    *,
    question: str = "Какое сырьё?",
) -> dict[str, Any]:
    return {
        "category_slug": slug,
        "label": label,
        "question": question,
        "roles": _opts(*kinds),
        "filters": _filters(),
    }


_SLUG_BY_KEY: dict[str, tuple[str, str]] = {
    "fabric": ("materials-tkani-i-tekstilnoe-syre", "Ткани и текстильное сырьё"),
    "notions": ("materials-shveynaya-furnitura", "Швейная фурнитура"),
    "leather": ("materials-kozha-i-kozhzameniteli", "Кожа и кожзаменители"),
    "yarn": ("materials-nitki-pryazha-i-volokno", "Нитки, пряжа и волокно"),
    "metal": ("materials-metally-metallicheskoe-syre", "Металлы/металлическое сырьё"),
    "wood": ("materials-drevesina-i-drevesnoe-syre", "Древесина и древесное сырьё"),
    "plastic": ("materials-plastik-i-polimernoe-syre", "Пластик и полимерное сырьё"),
    "rubber": ("materials-rezina-i-kauchuk", "Резина и каучук"),
    "paper": ("materials-bumaga-i-karton", "Бумага и картон"),
    "glass": ("materials-steklo-i-stekolnoe-syre", "Стекло и стекольное сырьё"),
    "chemical": ("materials-himicheskoe-syre", "Химическое сырьё"),
    "paint": ("materials-lakokrasochnoe-syre", "Лакокрасочное сырьё"),
    "pack": ("materials-upakovochnye-materialy", "Упаковочные материалы"),
    "food": ("materials-pischevoe-syre-i-ingredienty", "Пищевое сырьё и ингредиенты"),
    "cosmetic": (
        "materials-syre-dlya-kosmetiki-parfyumerii",
        "Сырьё для косметики/парфюмерии",
    ),
    "household": ("materials-syre-dlya-bytovoy-himii", "Сырьё для бытовой химии"),
    "jewelry": (
        "materials-dlya-yuvelirnogo-proizvodstva",
        "Для ювелирного производства",
    ),
    "other": (
        "materials-prochee-syre-dlya-proizvodstva",
        "Прочее сырьё для производства",
    ),
}

MATERIALS_SECTIONS: dict[str, dict[str, Any]] = {
    key: _section(slug, label, MATERIALS_V2_SECTION_KINDS[key])
    for key, (slug, label) in _SLUG_BY_KEY.items()
}

assert set(MATERIALS_SECTIONS) == set(MATERIALS_V2_SECTION_KINDS)
assert MATERIALS_SELLER_TARGET == GOODS_SELLER_CHOICES


def build_materials_section_catalog(section_key: str) -> dict[str, Any] | None:
    return MATERIALS_SECTIONS.get(section_key)
