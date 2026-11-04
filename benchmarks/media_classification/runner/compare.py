"""Compare multiple existing benchmark report directories (facts side-by-side)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _load_metrics(run_dir: Path) -> dict[str, Any]:
    path = run_dir / "metrics.json"
    if not path.is_file():
        raise FileNotFoundError(f"missing metrics.json in {run_dir}")
    return json.loads(path.read_text(encoding="utf-8"))


def _load_config(run_dir: Path) -> dict[str, Any]:
    path = run_dir / "config.json"
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def compare_runs(run_dirs: list[Path]) -> str:
    if len(run_dirs) < 2:
        raise ValueError("compare requires at least 2 run directories")

    rows: list[dict[str, Any]] = []
    for d in run_dirs:
        cfg = _load_config(d)
        m = _load_metrics(d)
        rows.append(
            {
                "run": d.name,
                "adapter": cfg.get("adapter"),
                "adapter_version": cfg.get("adapter_version"),
                "catalog_hash": (cfg.get("catalog_hash") or "")[:12],
                "dataset_hash": (cfg.get("dataset_hash") or "")[:12],
                "leaf_top1": m.get("leaf_top1"),
                "leaf_top3": m.get("leaf_top3"),
                "macro_f1": m.get("macro_f1"),
                "l1_accuracy": m.get("l1_accuracy"),
                "false_high_confidence": m.get("false_high_confidence_count"),
                "false_high_confidence_rate": m.get("false_high_confidence_rate"),
                "errors": m.get("errors"),
                "evaluated": m.get("evaluated"),
                "total": m.get("total"),
                "latency_p50_ms": (m.get("latency") or {}).get("p50_ms"),
                "latency_p95_ms": (m.get("latency") or {}).get("p95_ms"),
                "cost_per_listing": (m.get("cost") or {}).get("cost_per_listing"),
                "rss_mb": (m.get("resources") or {}).get("rss_mb"),
            }
        )

    lines = [
        "# Benchmark compare (facts only — no pseudo-winner score)",
        "",
        "| run | adapter | leaf_top1 | macro_f1 | false_hi | errors | eval/total | p50ms | p95ms | $/listing |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for r in rows:
        lines.append(
            "| {run} | {adapter}@{ver} | {leaf_top1} | {macro_f1} | {false_high_confidence} "
            "({false_high_confidence_rate}) | {errors} | {evaluated}/{total} | "
            "{latency_p50_ms} | {latency_p95_ms} | {cost_per_listing} |".format(
                run=r["run"][:20],
                adapter=r["adapter"],
                ver=(r["adapter_version"] or "")[:16],
                leaf_top1=r["leaf_top1"],
                macro_f1=r["macro_f1"],
                false_high_confidence=r["false_high_confidence"],
                false_high_confidence_rate=r["false_high_confidence_rate"],
                errors=r["errors"],
                evaluated=r["evaluated"],
                total=r["total"],
                latency_p50_ms=r["latency_p50_ms"],
                latency_p95_ms=r["latency_p95_ms"],
                cost_per_listing=r["cost_per_listing"],
            )
        )
    lines.append("")
    lines.append("Catalog/dataset hashes:")
    for r in rows:
        lines.append(
            f"- `{r['run']}`: catalog={r['catalog_hash']}… dataset={r['dataset_hash']}…"
        )
    lines.append("")
    return "\n".join(lines)
