#!/usr/bin/env python3
"""Merge mashina.kg passenger makes/models into the Flutter car catalog.

Reads the attribute dumps saved by a prior fetch, or downloads them.
Then rewrites car_brands_data.dart and car_brands_models.dart.

    python scripts/merge_mashina_passenger_catalog.py
    python scripts/generate_vehicle_data_from_mobile.py
"""
from __future__ import annotations

import json
import re
import sys
import urllib.request
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.services.category_text import normalize_alias_compact  # noqa: E402

MOBILE_DATA = ROOT.parent / "aivai_mobile" / "lib" / "features" / "home" / "data"
BRANDS_DART = MOBILE_DATA / "car_brands_data.dart"
MODELS_DART = MOBILE_DATA / "car_brands_models.dart"

MAKES_URL = "https://api.mashina.kg/api/mbank-proxy/v1/ads/16/options?category_id=1"
MODELS_URL = "https://api.mashina.kg/api/mbank-proxy/v1/ads/17/options?category_id=1"

# Same marque, different spelling on mashina.kg.
_ALIAS_TO_OURS = {
    "lixiang": "Li Auto",
    "lixiangauto": "Li Auto",
    "immotorszhiji": "IM",
    "immotors": "IM",
    "zhiji": "IM",
}


def _fetch(url: str) -> list[dict]:
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://mashina.kg/catalog/passenger",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    if not isinstance(data, list):
        raise SystemExit(f"unexpected payload from {url}")
    return data


def _dart_str(value: str) -> str:
    return "'" + value.replace("\\", "\\\\").replace("'", "\\'") + "'"


def _parse_string_list(text: str, const_name: str) -> list[str]:
    block = re.search(
        rf"static const List<String> {const_name} = \[(.*?)\];",
        text,
        re.S,
    )
    if not block:
        raise SystemExit(f"missing {const_name}")
    return [
        m.replace("\\'", "'")
        for m in re.findall(r"'((?:\\'|[^'])*)'", block.group(1))
    ]


def _parse_models_map(text: str) -> dict[str, list[str]]:
    block = re.search(
        r"static const Map<String, List<String>> carModelsByBrand = \{(.*?)\n  \};",
        text,
        re.S,
    )
    if not block:
        raise SystemExit("missing carModelsByBrand")
    result: dict[str, list[str]] = {}
    for brand_match in re.finditer(
        r"'((?:\\'|[^'])*)': \[(.*?)\]",
        block.group(1),
        re.S,
    ):
        brand = brand_match.group(1).replace("\\'", "'")
        models = [
            m.replace("\\'", "'")
            for m in re.findall(r"'((?:\\'|[^'])*)'", brand_match.group(2))
        ]
        result[brand] = models
    return result


def _brand_keys(name: str) -> set[str]:
    keys = {normalize_alias_compact(name)}
    for inner in re.findall(r"\(([^)]+)\)", name):
        keys.add(normalize_alias_compact(inner))
    outer = re.sub(r"\([^)]*\)", "", name)
    keys.add(normalize_alias_compact(outer))
    keys.discard("")
    return keys


def _match_brand(name: str, by_key: dict[str, str]) -> str | None:
    for key in _brand_keys(name):
        aliased = _ALIAS_TO_OURS.get(key)
        if aliased:
            return aliased
        if key in by_key:
            return by_key[key]
    return None


def merge(makes: list[dict], mash_models: list[dict]) -> tuple[list[str], dict[str, list[str]], dict[str, int]]:
    brands_text = BRANDS_DART.read_text(encoding="utf-8")
    models_text = MODELS_DART.read_text(encoding="utf-8")
    brands = _parse_string_list(brands_text, "brands")
    models = _parse_models_map(models_text)

    by_key: dict[str, str] = {}
    for name in brands:
        for key in _brand_keys(name):
            by_key.setdefault(key, name)

    by_parent: dict[int, list[str]] = defaultdict(list)
    for row in mash_models:
        if row.get("is_active", True) and row.get("value"):
            by_parent[row["parent_option_id"]].append(row["value"])

    added_brands = 0
    added_models = 0
    for make in makes:
        if not make.get("is_active", True):
            continue
        mash_name = (make.get("value") or "").strip()
        if not mash_name:
            continue
        ours = _match_brand(mash_name, by_key)
        if ours is None:
            ours = mash_name
            brands.append(ours)
            for key in _brand_keys(ours):
                by_key.setdefault(key, ours)
            added_brands += 1
        have = {normalize_alias_compact(m) for m in models.get(ours, [])}
        bucket = list(models.get(ours, []))
        for model_name in by_parent.get(make["id"], []):
            model_name = model_name.strip()
            if not model_name:
                continue
            key = normalize_alias_compact(model_name)
            if not key or key in have:
                continue
            have.add(key)
            bucket.append(model_name)
            added_models += 1
        if bucket:
            models[ours] = sorted(set(bucket), key=str.casefold)

    brands = sorted(set(brands), key=str.casefold)
    return brands, models, {"brands_added": added_brands, "models_added": added_models}


def _write_brands(brands: list[str], popular: list[str]) -> None:
    lines = [
        "import '../figma/figma_car_sale_filter_spec.dart';",
        "",
        "/// Марки авто A→Z — раскрывающийся список `AIVAI_HOME 12`.",
        "/// Passenger makes include mashina.kg (category легковые).",
        "abstract final class CarBrandsData {",
        "  static const String brandCountLabel = '5656';",
        "",
        "  static const double brandListStartY = 139;",
        "",
        "  /// Популярные марки — показываются первыми в списке «Марка».",
        "  static const List<String> popularBrands = [",
    ]
    for name in popular:
        lines.append(f"    {_dart_str(name)},")
    lines += [
        "  ];",
        "",
        "  static const List<String> brands = [",
    ]
    for name in brands:
        lines.append(f"    {_dart_str(name)},")
    lines += [
        "  ];",
        "",
        "  /// Популярные марки, затем остальные A→Z (без дублей).",
        "  static List<String> get brandsForPicker {",
        "    final popularSet = popularBrands.toSet();",
        "    final rest = brands.where((brand) => !popularSet.contains(brand));",
        "    return [...popularBrands, ...rest];",
        "  }",
        "",
        "  static double rowYForIndex(int index) =>",
        "      brandListStartY + index * FigmaCarSaleFilterSpec.fieldStride;",
        "}",
        "",
    ]
    BRANDS_DART.write_text("\n".join(lines), encoding="utf-8")


def _write_models(brands: list[str], models: dict[str, list[str]]) -> None:
    lines = [
        "import 'car_brands_data.dart';",
        "",
        "/// Модели по маркам — зависимый список «Модель» в фильтре «Продажа авто».",
        "/// Union of the previous catalog and mashina.kg passenger models.",
        "abstract final class CarBrandsModels {",
        "  static const String modelCountLabel = CarBrandsData.brandCountLabel;",
        "  static const String selectBrandFirstHint = 'Сначала выберите марку';",
        "",
        "  static const Map<String, List<String>> carModelsByBrand = {",
    ]
    for brand in brands:
        bucket = models.get(brand) or []
        if not bucket:
            continue
        inner = ", ".join(_dart_str(m) for m in bucket)
        lines.append(f"    {_dart_str(brand)}: [{inner}],")
    lines += [
        "  };",
        "}",
        "",
    ]
    MODELS_DART.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    makes = _fetch(MAKES_URL)
    mash_models = _fetch(MODELS_URL)
    popular = _parse_string_list(BRANDS_DART.read_text(encoding="utf-8"), "popularBrands")
    brands, models, stats = merge(makes, mash_models)
    _write_brands(brands, popular)
    _write_models(brands, models)
    model_count = sum(len(v) for v in models.values())
    print(
        f"brands={len(brands)} models={model_count} "
        f"added_brands={stats['brands_added']} added_models={stats['models_added']}"
    )


if __name__ == "__main__":
    main()
