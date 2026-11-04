# -*- coding: utf-8 -*-
"""Write Dart fallbacks for repair and construction goods."""
from pathlib import Path

from app.seeds.repair_sections_catalog import REPAIR_SECTIONS


def dart_str(value: str) -> str:
    return "'" + value.replace("\\", "\\\\").replace("'", "\\'") + "'"


def dart_list(items: list[str]) -> str:
    return "[" + ", ".join(dart_str(item) for item in items) + "]"


lines = [
    "/// Offline copies of repair and construction goods.",
    "abstract final class RepairSectionFallbacks {",
    "  static const sections = <String, (String, String, List<String>, List<(String, List<String>, List<String>?)>)>{",
]
for key, catalog in REPAIR_SECTIONS.items():
    kinds = [item["label"] for item in catalog["roles"]]
    filters = []
    for group in catalog["filters"]:
        options = [opt["label"] for opt in group["options"]]
        applies = group.get("applies_to")
        applies_dart = "null" if not applies else dart_list(list(applies))
        filters.append(
            "("
            + dart_str(group["label"])
            + ", "
            + dart_list(options)
            + ", "
            + applies_dart
            + ")"
        )
    lines.append(
        "    "
        + dart_str(catalog["label"])
        + ": ("
        + dart_str(key)
        + ", "
        + dart_str(catalog["question"])
        + ", "
        + dart_list(kinds)
        + ", ["
        + ", ".join(filters)
        + "]),"
    )
lines.extend(
    [
        "  };",
        "",
        "  static String? keyForLabel(String label) => sections[label]?.$1;",
        "",
        "  static String questionFor(String label) =>",
        "      sections[label]?.$2 ?? 'Какой товар?';",
        "",
        "  static List<String> kindsFor(String label) => sections[label]?.$3 ?? const [];",
        "",
        "  static List<(String, List<String>, List<String>?)> filtersFor(String label) =>",
        "      sections[label]?.$4 ?? const [];",
        "}",
        "",
    ]
)
target = Path(
    r"c:\Users\user\Desktop\AIVAI_PROJECT\aivai_mobile\lib\features\listings\data\repair_section_fallbacks.dart"
)
target.write_text("\n".join(lines), encoding="utf-8")
print("wrote", len(REPAIR_SECTIONS), "chars", target.stat().st_size)
