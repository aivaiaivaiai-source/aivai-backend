# -*- coding: utf-8 -*-
"""Write Dart fallbacks for electronics sections."""
from pathlib import Path

from app.seeds.electronics_sections_catalog import ELECTRONICS_SECTIONS


def dart_str(value: str) -> str:
    return "'" + value.replace("\\", "\\\\").replace("'", "\\'") + "'"


def dart_list(items: list[str]) -> str:
    return "[" + ", ".join(dart_str(item) for item in items) + "]"


lines = [
    "/// Offline copies of electronics sections.",
    "abstract final class ElectronicsSectionFallbacks {",
    "  static const sections = <String, (String, String, List<String>, List<(String, String?, List<String>?, List<(String, String?, List<String>?)>)>)>{",
]
for key, catalog in ELECTRONICS_SECTIONS.items():
    kinds = [item["label"] for item in catalog["roles"]]
    filters = []
    for group in catalog["filters"]:
        options = []
        for opt in group["options"]:
            parent = "null" if not opt.get("parent") else dart_str(opt["parent"])
            for_kinds = opt.get("for_kinds")
            kinds_dart = "null" if not for_kinds else dart_list(list(for_kinds))
            options.append("(" + dart_str(opt["label"]) + ", " + parent + ", " + kinds_dart + ")")
        applies = group.get("applies_to")
        applies_dart = "null" if not applies else dart_list(list(applies))
        depends = "null" if not group.get("depends_on") else dart_str(group["depends_on"])
        filters.append(
            "("
            + dart_str(group["label"])
            + ", "
            + depends
            + ", "
            + applies_dart
            + ", ["
            + ", ".join(options)
            + "])"
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
        "  static List<(String, String?, List<String>?, List<(String, String?, List<String>?)>)>",
        "      filtersFor(String label) =>",
        "          sections[label]?.$4 ?? const [];",
        "}",
        "",
    ]
)
target = Path(
    r"c:\Users\user\Desktop\AIVAI_PROJECT\aivai_mobile\lib\features\listings\data\electronics_section_fallbacks.dart"
)
target.write_text("\n".join(lines), encoding="utf-8")
print("wrote", target.stat().st_size)
