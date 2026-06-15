#!/usr/bin/env python3
"""Generate app/seeds/mobile_vehicle_catalog.py from aivai_mobile car brand Dart files."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MOBILE_DATA = ROOT.parent / "aivai_mobile" / "lib" / "features" / "home" / "data"
OUTPUT = ROOT / "app" / "seeds" / "mobile_vehicle_catalog.py"
VEHICLE_DATA = ROOT / "app" / "seeds" / "vehicle_data.py"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.services.category_text import slugify  # noqa: E402


def parse_string_list(text: str, const_name: str) -> list[str]:
    block = re.search(rf"static const List<String> {const_name} = \[(.*?)\];", text, re.S)
    if not block:
        return []
    return re.findall(r"'((?:\\'|[^'])*)'", block.group(1))


def parse_models_map(text: str) -> dict[str, list[str]]:
    block = re.search(
        r"static const Map<String, List<String>> carModelsByBrand = \{(.*?)\};",
        text,
        re.S,
    )
    if not block:
        return {}
    result: dict[str, list[str]] = {}
    for brand_match in re.finditer(r"'((?:\\'|[^'])*)': \[(.*?)\]", block.group(1), re.S):
        brand = brand_match.group(1).replace("\\'", "'")
        models = [
            m.replace("\\'", "'")
            for m in re.findall(r"'((?:\\'|[^'])*)'", brand_match.group(2))
        ]
        result[brand] = models
    return result


def load_legacy_brand_slugs() -> dict[str, str]:
    text = VEHICLE_DATA.read_text(encoding="utf-8")
    block = re.search(r"^BRANDS:.*?= \[(.*?)\n\]", text, re.S | re.M)
    if not block:
        return {}
    legacy: dict[str, str] = {}
    for slug, name in re.findall(r'\("([^"]+)", "([^"]+)",', block.group(1)):
        legacy[slugify(name)] = slug
        legacy[name.lower()] = slug
    return legacy


def stable_brand_slug(name: str, legacy_slugs: dict[str, str]) -> str:
    return legacy_slugs.get(name.lower()) or legacy_slugs.get(slugify(name)) or slugify(name)


def unique_model_slug(name: str, seen: set[str]) -> str:
    base = slugify(name)
    slug = base
    suffix = 2
    while slug in seen:
        slug = f"{base}-{suffix}"
        suffix += 1
    seen.add(slug)
    return slug


def build_catalog() -> tuple[list[str], list[tuple[str, str]], dict[str, list[tuple[str, str]]]]:
    brands_text = (MOBILE_DATA / "car_brands_data.dart").read_text(encoding="utf-8")
    models_text = (MOBILE_DATA / "car_brands_models.dart").read_text(encoding="utf-8")
    legacy_slugs = load_legacy_brand_slugs()

    popular_names = parse_string_list(brands_text, "popularBrands")
    brand_names = parse_string_list(brands_text, "brands")
    models_by_brand = parse_models_map(models_text)

    brand_slug_by_name: dict[str, str] = {}
    for name in brand_names:
        brand_slug_by_name[name] = stable_brand_slug(name, legacy_slugs)

    popular_slugs: list[str] = []
    seen_popular: set[str] = set()
    for name in popular_names:
        slug = brand_slug_by_name.get(name)
        if slug and slug not in seen_popular:
            popular_slugs.append(slug)
            seen_popular.add(slug)

    brands: list[tuple[str, str]] = []
    seen_brand_slugs: set[str] = set()
    for name in sorted(brand_names, key=str.casefold):
        slug = brand_slug_by_name[name]
        if slug in seen_brand_slugs:
            continue
        seen_brand_slugs.add(slug)
        brands.append((slug, name))

    models: dict[str, list[tuple[str, str]]] = {}
    for brand_name in brand_names:
        brand_slug = brand_slug_by_name[brand_name]
        raw_models = models_by_brand.get(brand_name, [])
        seen_model_slugs: set[str] = set()
        entries: list[tuple[str, str]] = []
        for model_name in sorted(raw_models, key=str.casefold):
            model_slug = unique_model_slug(model_name, seen_model_slugs)
            entries.append((model_slug, model_name))
        if entries:
            models[brand_slug] = entries

    return popular_slugs, brands, models


def render_python(
    popular_slugs: list[str],
    brands: list[tuple[str, str]],
    models: dict[str, list[tuple[str, str]]],
) -> str:
    lines = [
        '"""Mobile car brand/model catalog — generated from aivai_mobile Dart data.',
        "",
        "Regenerate:",
        "    python scripts/generate_vehicle_data_from_mobile.py",
        '"""',
        "from __future__ import annotations",
        "",
        f"MOBILE_POPULAR_BRAND_SLUGS: list[str] = {popular_slugs!r}",
        "",
        f"MOBILE_VEHICLE_BRANDS: list[tuple[str, str]] = [",
    ]
    for slug, name in brands:
        lines.append(f'    ("{slug}", "{name}"),')
    lines.append("]")
    lines.append("")
    lines.append("MOBILE_VEHICLE_MODELS: dict[str, list[tuple[str, str]]] = {")
    for brand_slug in sorted(models.keys()):
        lines.append(f'    "{brand_slug}": [')
        for model_slug, model_name in models[brand_slug]:
            safe_name = model_name.replace("\\", "\\\\").replace('"', '\\"')
            lines.append(f'        ("{model_slug}", "{safe_name}"),')
        lines.append("    ],")
    lines.append("}")
    lines.append("")
    model_count = sum(len(v) for v in models.values())
    lines.append("MOBILE_VEHICLE_CATALOG_COUNTS = {")
    lines.append(f'    "brands": {len(brands)},')
    lines.append(f'    "models": {model_count},')
    lines.append(f'    "popular_brands": {len(popular_slugs)},')
    lines.append("}")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    popular_slugs, brands, models = build_catalog()
    OUTPUT.write_text(render_python(popular_slugs, brands, models), encoding="utf-8")
    model_count = sum(len(v) for v in models.values())
    print(f"Wrote {OUTPUT}")
    print(f"  brands={len(brands)} models={model_count} popular={len(popular_slugs)}")


if __name__ == "__main__":
    main()
