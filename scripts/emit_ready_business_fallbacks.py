# -*- coding: utf-8 -*-
"""Emit Flutter ReadyBusinessSectionFallbacks from Backend V2 catalog."""
from __future__ import annotations

from pathlib import Path

from app.seeds.ready_business_sections_catalog import READY_BUSINESS_SECTIONS

ROOT = Path(__file__).resolve().parents[2] / "aivai_mobile"
OUT = (
    ROOT
    / "lib"
    / "features"
    / "listings"
    / "data"
    / "ready_business_section_fallbacks.dart"
)


def _opt(o: dict) -> str:
    return f"('{o['label']}', null, null)"


def _group(g: dict) -> str:
    opts = ", ".join(_opt(o) for o in g["options"])
    return f"('{g['label']}', null, null, [{opts}])"


def main() -> None:
    lines = [
        "/// Offline copies of ready business sections.",
        "abstract final class ReadyBusinessSectionFallbacks {",
        "  static const sections = <String, (String, String, List<String>, List<(String, String?, List<String>?, List<(String, String?, List<String>?)>)>)>{",
    ]
    for key, cat in READY_BUSINESS_SECTIONS.items():
        kinds = ", ".join(f"'{r['label']}'" for r in cat["roles"])
        filters = ", ".join(_group(g) for g in cat["filters"])
        label = cat["label"]
        q = cat["question"]
        lines.append(
            f"    '{label}': ('{key}', '{q}', [{kinds}], [{filters}]),"
        )
    lines += [
        "  };",
        "",
        "  static String? keyForLabel(String label) => sections[label]?.$1;",
        "",
        "  static String questionFor(String label) =>",
        "      sections[label]?.$2 ?? 'Какой бизнес?';",
        "",
        "  static List<String> kindsFor(String label) => sections[label]?.$3 ?? const [];",
        "",
        "  static List<(String, String?, List<String>?, List<(String, String?, List<String>?)>)>",
        "      filtersFor(String label) =>",
        "          sections[label]?.$4 ?? const [];",
        "}",
        "",
    ]
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
