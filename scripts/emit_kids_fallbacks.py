# -*- coding: utf-8 -*-
"""Write Dart fallbacks for Kids World sections."""
from pathlib import Path

from app.seeds.kids_sections_catalog import KIDS_SECTIONS


def dart_str(value: str) -> str:
    return "'" + value.replace("\\", "\\\\").replace("'", "\\'") + "'"


def dart_list(items: list[str]) -> str:
    return "[" + ", ".join(dart_str(item) for item in items) + "]"


lines = [
    "/// Offline copies of Kids World sections.",
    "abstract final class KidsSectionFallbacks {",
    "  static const sections = <String, (String, String, List<String>, List<(String, List<String>, List<String>?)>)>{",
]
for key, catalog in KIDS_SECTIONS.items():
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
    r"c:\Users\user\Desktop\AIVAI_PROJECT\aivai_mobile\lib\features\listings\data\kids_section_fallbacks.dart"
)
target.write_text("\n".join(lines), encoding="utf-8")
print("wrote", len(KIDS_SECTIONS), "chars", target.stat().st_size)
