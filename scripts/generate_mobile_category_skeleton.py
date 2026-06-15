#!/usr/bin/env python3
"""Generate app/seeds/mobile_category_skeleton.py from aivai_mobile Dart data files."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MOBILE_DATA = ROOT.parent / "aivai_mobile" / "lib" / "features" / "home" / "data"
OUTPUT = ROOT / "app" / "seeds" / "mobile_category_skeleton.py"

# Mobile root label -> existing backend root slug (legacy roots preserved).
ROOT_LABEL_TO_SLUG: dict[str, str] = {
    "Транспорт": "transport",
    "Недвижимость": "real-estate",
    "Работа": "jobs",
    "Услуги": "services",
    "Ремонт и Строительство": "repair-construction",
    "Техника и электроника": "electronics",
    "Красота и личный уход": "beauty",
    "Одежда, обувь и аксессуары": "fashion",
    "Продукты и сельхозтовары": "food-agri",
    "Детский мир": "kids",
    "Оборудование для бизнеса": "business-equipment",
    "Медтовары": "medical",
    "Готовый бизнес": "ready-business",
    "Дом и сад": "home-garden",
    "Канцтовары и книги": "stationery-books",
    "Животные": "animals",
    "Спорт, отдых и хобби": "sports-hobby",
    "Сырьё для производство": "materials",
}

# Stable L2 slugs for transport (v2 skeleton; legacy slugs unchanged).
TRANSPORT_L2_SLUGS: dict[str, str] = {
    "Продажа авто": "transport-car-sale",
    "Автозапчасти": "transport-auto-parts",
    "Аксессуары и тюнинг": "transport-accessories-tuning",
    "Шины и диски": "transport-tires-wheels",
    "Автоуслуги": "transport-auto-services",
    "Мототехника": "transport-moto-tech",
    "Электротранспорт": "transport-electric",
    "Коммерческий транспорт": "transport-commercial",
    "Велосипеды": "transport-bicycles",
    "Спецтехника": "transport-special-equipment",
    "Грузовой транспорт": "transport-cargo",
    "Водный транспорт": "transport-watercraft",
    "Прицепы и полуприцепы": "transport-trailers",
    "Сельхозтехника": "transport-farm-machinery",
    "Аренда транспорта": "transport-rental",
    "Скупка/обмен транспорта": "transport-buyback-exchange",
}

# Transport L3 dart file -> parent L2 slug
TRANSPORT_L3_FILES: dict[str, str] = {
    "auto_parts_subcategories_data.dart": "transport-auto-parts",
    "accessories_subcategories_data.dart": "transport-accessories-tuning",
    "tires_wheels_subcategories_data.dart": "transport-tires-wheels",
    "auto_services_subcategories_data.dart": "transport-auto-services",
    "moto_technika_subcategories_data.dart": "transport-moto-tech",
    "electric_transport_subcategories_data.dart": "transport-electric",
    "commercial_transport_subcategories_data.dart": "transport-commercial",
    "bicycles_subcategories_data.dart": "transport-bicycles",
    "special_equipment_subcategories_data.dart": "transport-special-equipment",
    "cargo_transport_subcategories_data.dart": "transport-cargo",
    "water_transport_subcategories_data.dart": "transport-watercraft",
    "trailers_semi_trailers_subcategories_data.dart": "transport-trailers",
    "farm_machinery_subcategories_data.dart": "transport-farm-machinery",
    "transport_rental_subcategories_data.dart": "transport-rental",
    "transport_buyback_exchange_subcategories_data.dart": "transport-buyback-exchange",
}

# Non-transport L2 dart file -> backend root slug
ROOT_L2_FILES: dict[str, str] = {
    "real_estate_subcategories_data.dart": "real-estate",
    "work_subcategories_data.dart": "jobs",
    "services_subcategories_data.dart": "services",
    "repair_construction_subcategories_data.dart": "repair-construction",
    "electronics_subcategories_data.dart": "electronics",
    "beauty_personal_care_subcategories_data.dart": "beauty",
    "fashion_subcategories_data.dart": "fashion",
    "food_agriculture_subcategories_data.dart": "food-agri",
    "kids_world_subcategories_data.dart": "kids",
    "business_equipment_subcategories_data.dart": "business-equipment",
    "med_goods_subcategories_data.dart": "medical",
    "ready_business_subcategories_data.dart": "ready-business",
    "home_garden_subcategories_data.dart": "home-garden",
    "stationery_books_subcategories_data.dart": "stationery-books",
    "animals_subcategories_data.dart": "animals",
    "sport_leisure_hobby_subcategories_data.dart": "sports-hobby",
    "raw_materials_subcategories_data.dart": "materials",
}

ROOT_ENTITY_TYPE: dict[str, str] = {
    "real-estate": "object",
    "transport": "object",
    "jobs": "job",
    "services": "service",
    "repair-construction": "construction",
    "electronics": "object",
    "business-equipment": "equipment",
    "home-garden": "object",
    "kids": "object",
    "medical": "object",
    "food-agri": "food",
    "beauty": "object",
    "fashion": "object",
    "sports-hobby": "object",
    "stationery-books": "object",
    "animals": "animal",
    "materials": "raw_material",
    "ready-business": "business",
}

_TRANSLIT = {
    "а": "a",
    "б": "b",
    "в": "v",
    "г": "g",
    "д": "d",
    "е": "e",
    "ё": "e",
    "ж": "zh",
    "з": "z",
    "и": "i",
    "й": "y",
    "к": "k",
    "л": "l",
    "м": "m",
    "н": "n",
    "о": "o",
    "п": "p",
    "р": "r",
    "с": "s",
    "т": "t",
    "у": "u",
    "ф": "f",
    "х": "h",
    "ц": "ts",
    "ч": "ch",
    "ш": "sh",
    "щ": "sch",
    "ъ": "",
    "ы": "y",
    "ь": "",
    "э": "e",
    "ю": "yu",
    "я": "ya",
}


def slugify_part(text: str) -> str:
    out: list[str] = []
    for ch in text.lower():
        if ch in _TRANSLIT:
            out.append(_TRANSLIT[ch])
        elif ch.isascii() and ch.isalnum():
            out.append(ch)
        elif ch in " -_/\\.":
            out.append("-")
    slug = re.sub(r"-+", "-", "".join(out)).strip("-")
    return slug[:50] or "section"


def parse_labels_from_dart(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    labels: list[str] = []
    for match in re.finditer(r"TransportSubcategoryItem\(label:\s*'([^']+)'", text):
        labels.append(match.group(1))
    if labels:
        return labels
    block = re.search(r"static const List<String> _labels = \[(.*?)\];", text, re.S)
    if not block:
        return labels
    for match in re.finditer(r"'([^']+)'", block.group(1)):
        labels.append(match.group(1))
    return labels


def parse_root_labels(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    return re.findall(r"label:\s*'([^']+)'", text)


def unique_slug(parent_slug: str, label: str, seen: set[str]) -> str:
    base = f"{parent_slug}-{slugify_part(label)}"
    slug = base
    n = 2
    while slug in seen:
        slug = f"{base}-{n}"
        n += 1
    seen.add(slug)
    return slug


def build_skeleton() -> list[tuple[str, str, str, str, int]]:
    entries: list[tuple[str, str, str, str, int]] = []
    seen_slugs: set[str] = set()

    # Transport L2
    transport_labels = parse_labels_from_dart(MOBILE_DATA / "transport_subcategories_data.dart")
    for i, label in enumerate(transport_labels):
        slug = TRANSPORT_L2_SLUGS.get(label)
        if slug is None:
            slug = unique_slug("transport", label, seen_slugs)
        else:
            seen_slugs.add(slug)
        entity = ROOT_ENTITY_TYPE["transport"]
        entries.append(("transport", slug, label, entity, (i + 1) * 10))

    # Transport L3
    for filename, parent_slug in TRANSPORT_L3_FILES.items():
        path = MOBILE_DATA / filename
        if not path.exists():
            print(f"WARN missing {filename}", file=sys.stderr)
            continue
        labels = parse_labels_from_dart(path)
        for i, label in enumerate(labels):
            slug = unique_slug(parent_slug, label, seen_slugs)
            entries.append((parent_slug, slug, label, ROOT_ENTITY_TYPE["transport"], (i + 1) * 10))

    # Other roots L2
    for filename, root_slug in ROOT_L2_FILES.items():
        path = MOBILE_DATA / filename
        if not path.exists():
            print(f"WARN missing {filename}", file=sys.stderr)
            continue
        entity = ROOT_ENTITY_TYPE[root_slug]
        labels = parse_labels_from_dart(path)
        for i, label in enumerate(labels):
            slug = unique_slug(root_slug, label, seen_slugs)
            entries.append((root_slug, slug, label, entity, (i + 1) * 10))

    return entries


def render_python(entries: list[tuple[str, str, str, str, int]]) -> str:
    lines = [
        '"""Mobile category skeleton v2 — generated from aivai_mobile Dart data.',
        "",
        "Regenerate:",
        "    python -m scripts.generate_mobile_category_skeleton",
        '"""',
        "from __future__ import annotations",
        "",
        "from app.models.category_enums import CategoryEntityType",
        "",
        "# (parent_slug, slug, name, entity_type_name, sort_order)",
        "# parent_slug is backend root slug (L2) or mobile v2 L2 slug (L3).",
        "MOBILE_CATEGORY_SKELETON: list[tuple[str, str, str, str, int]] = [",
    ]
    entity_map = {
        "object": "CategoryEntityType.object",
        "job": "CategoryEntityType.job",
        "service": "CategoryEntityType.service",
        "construction": "CategoryEntityType.construction",
        "equipment": "CategoryEntityType.equipment",
        "food": "CategoryEntityType.food",
        "animal": "CategoryEntityType.animal",
        "raw_material": "CategoryEntityType.raw_material",
        "business": "CategoryEntityType.business",
    }
    for parent, slug, name, entity, sort_order in entries:
        et = entity_map[entity]
        safe_name = name.replace('"', '\\"')
        lines.append(f'    ("{parent}", "{slug}", "{safe_name}", {et}, {sort_order}),')
    lines.append("]")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    if not MOBILE_DATA.is_dir():
        raise SystemExit(f"Mobile data dir not found: {MOBILE_DATA}")
    entries = build_skeleton()
    OUTPUT.write_text(render_python(entries), encoding="utf-8")
    print(f"Wrote {len(entries)} entries -> {OUTPUT}")


if __name__ == "__main__":
    main()
