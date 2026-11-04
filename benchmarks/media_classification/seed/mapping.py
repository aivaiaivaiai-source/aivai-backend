"""Deterministic source_label → semantic / AiVai mapping (no AI)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LabelMapping:
    source_label: str
    semantic_slug: str
    semantic_name: str
    semantic_path: tuple[str, ...]
    aivai_category_slug: str | None  # None => NO_CURRENT_AIVAI_MATCH
    mapping_confidence: str  # exact | approximate | ambiguous
    review_required: bool = False


# Benchmark-only slugs (ids in seed catalog 9xxxxx) — never production.
SEMANTIC_APPAREL = "benchmark-apparel"
SEMANTIC_FOOTWEAR = "benchmark-footwear"
SEMANTIC_OTHER = "benchmark-other-consumer"
SEMANTIC_TRANSPORT_OTHER = "benchmark-transport-other"

NO_CURRENT_AIVAI_MATCH = "NO_CURRENT_AIVAI_MATCH"

# Clothing-dataset-small class folders → mapping
CLOTHING_SMALL_MAP: dict[str, LabelMapping] = {
    "t-shirt": LabelMapping(
        "t-shirt", SEMANTIC_APPAREL, "Apparel", ("Benchmark", "Apparel"), None, "exact"
    ),
    "shirt": LabelMapping(
        "shirt", SEMANTIC_APPAREL, "Apparel", ("Benchmark", "Apparel"), None, "exact"
    ),
    "blouse": LabelMapping(
        "blouse", SEMANTIC_APPAREL, "Apparel", ("Benchmark", "Apparel"), None, "exact"
    ),
    "pants": LabelMapping(
        "pants", SEMANTIC_APPAREL, "Apparel", ("Benchmark", "Apparel"), None, "exact"
    ),
    "shorts": LabelMapping(
        "shorts", SEMANTIC_APPAREL, "Apparel", ("Benchmark", "Apparel"), None, "exact"
    ),
    "skirt": LabelMapping(
        "skirt", SEMANTIC_APPAREL, "Apparel", ("Benchmark", "Apparel"), None, "exact"
    ),
    "dress": LabelMapping(
        "dress", SEMANTIC_APPAREL, "Apparel", ("Benchmark", "Apparel"), None, "exact"
    ),
    "longsleeve": LabelMapping(
        "longsleeve", SEMANTIC_APPAREL, "Apparel", ("Benchmark", "Apparel"), None, "exact"
    ),
    "outwear": LabelMapping(
        "outwear", SEMANTIC_APPAREL, "Apparel", ("Benchmark", "Apparel"), None, "approximate"
    ),
    "hat": LabelMapping(
        "hat", SEMANTIC_OTHER, "Other consumer", ("Benchmark", "Other"), None, "approximate"
    ),
    "shoes": LabelMapping(
        "shoes", SEMANTIC_FOOTWEAR, "Footwear", ("Benchmark", "Footwear"), None, "exact"
    ),
    "sandals": LabelMapping(
        "sandals", SEMANTIC_FOOTWEAR, "Footwear", ("Benchmark", "Footwear"), None, "exact"
    ),
    "sneakers": LabelMapping(
        "sneakers", SEMANTIC_FOOTWEAR, "Footwear", ("Benchmark", "Footwear"), None, "exact"
    ),
    "socks": LabelMapping(
        "socks", SEMANTIC_OTHER, "Other consumer", ("Benchmark", "Other"), None, "approximate"
    ),
    "underwear": LabelMapping(
        "underwear",
        SEMANTIC_APPAREL,
        "Apparel",
        ("Benchmark", "Apparel"),
        None,
        "ambiguous",
        True,
    ),
    "body": LabelMapping(
        "body",
        SEMANTIC_APPAREL,
        "Apparel",
        ("Benchmark", "Apparel"),
        None,
        "ambiguous",
        True,
    ),
    "not-sure": LabelMapping(
        "not-sure",
        SEMANTIC_OTHER,
        "Other consumer",
        ("Benchmark", "Other"),
        None,
        "ambiguous",
        True,
    ),
    "other": LabelMapping(
        "other",
        SEMANTIC_OTHER,
        "Other consumer",
        ("Benchmark", "Other"),
        None,
        "ambiguous",
        True,
    ),
    "skip": LabelMapping(
        "skip",
        SEMANTIC_OTHER,
        "Other consumer",
        ("Benchmark", "Other"),
        None,
        "ambiguous",
        True,
    ),
}

# Vehicles HF labels — for future use if APPROVED after review
VEHICLES_MAP: dict[str, LabelMapping] = {
    "Cars": LabelMapping(
        "Cars",
        "transport-car-sale",
        "Продажа авто",
        ("Транспорт", "Продажа авто"),
        "transport-car-sale",
        "approximate",
        True,  # car vs parts/rental ambiguity → review
    ),
    "Motorcycles": LabelMapping(
        "Motorcycles",
        SEMANTIC_TRANSPORT_OTHER,
        "Other transport",
        ("Benchmark", "Transport other"),
        None,
        "exact",
    ),
    "Bikes": LabelMapping(
        "Bikes",
        SEMANTIC_TRANSPORT_OTHER,
        "Other transport",
        ("Benchmark", "Transport other"),
        None,
        "exact",
    ),
    "Planes": LabelMapping(
        "Planes",
        SEMANTIC_TRANSPORT_OTHER,
        "Other transport",
        ("Benchmark", "Transport other"),
        None,
        "exact",
    ),
    "Trains": LabelMapping(
        "Trains",
        SEMANTIC_TRANSPORT_OTHER,
        "Other transport",
        ("Benchmark", "Transport other"),
        None,
        "exact",
    ),
    "Ships": LabelMapping(
        "Ships",
        SEMANTIC_TRANSPORT_OTHER,
        "Other transport",
        ("Benchmark", "Transport other"),
        None,
        "exact",
    ),
    "Auto Rickshaws": LabelMapping(
        "Auto Rickshaws",
        SEMANTIC_TRANSPORT_OTHER,
        "Other transport",
        ("Benchmark", "Transport other"),
        None,
        "exact",
    ),
}


def map_clothing_label(folder_name: str) -> LabelMapping | None:
    key = folder_name.strip().lower().replace("_", "-").replace(" ", "-")
    # normalize common variants
    aliases = {
        "tshirt": "t-shirt",
        "t-shirts": "t-shirt",
        "long-sleeve": "longsleeve",
        "long_sleeve": "longsleeve",
        "outerwear": "outwear",
        "shoe": "shoes",
    }
    key = aliases.get(key, key)
    return CLOTHING_SMALL_MAP.get(key)


def aivai_match_status(mapping: LabelMapping) -> str:
    if mapping.aivai_category_slug:
        return mapping.aivai_category_slug
    return NO_CURRENT_AIVAI_MATCH
