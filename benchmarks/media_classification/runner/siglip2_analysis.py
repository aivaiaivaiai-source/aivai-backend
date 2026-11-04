"""Post-run analysis helpers for SigLIP2 private baseline (no GT mutation)."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

FOCUS_PAIRS = [
    ("CAR_SALE", "AUTO_PARTS"),
    ("AUTO_PARTS", "CAR_SALE"),
    ("CAR_SALE", "TRUCK_TRANSPORT"),
    ("TRUCK_TRANSPORT", "COMMERCIAL_TRANSPORT"),
    ("BUSES", "COMMERCIAL_TRANSPORT"),
    ("SPECIAL_MACHINERY", "TRUCK_TRANSPORT"),
    ("MOTORCYCLES", "CAR_SALE"),
    ("REAL_ESTATE", "CAR_SALE"),
    ("REAL_ESTATE", "AUTO_PARTS"),
    ("REAL_ESTATE", "TRUCK_TRANSPORT"),
    ("REAL_ESTATE", "SPECIAL_MACHINERY"),
    ("REAL_ESTATE", "COMMERCIAL_TRANSPORT"),
]


def enrich_siglip2_report(report_dir: Path) -> dict[str, Any]:
    report_dir = Path(report_dir)
    preds_path = report_dir / "predictions.jsonl"
    metrics_path = report_dir / "metrics.json"
    rows: list[dict[str, Any]] = []
    for line in preds_path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))

    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))

    wrong = []
    top3_only = []
    margins_wrong = []
    margins_all = []
    unclear_cases = []
    low_support_errors = []
    pair_counts: Counter[tuple[str, str]] = Counter()

    for row in rows:
        gt = row["ground_truth"]["category_slug"]
        cands = row.get("predicted_candidates") or []
        pred = cands[0]["category_slug"] if cands else None
        meta = row.get("raw_metadata") or {}
        margin = meta.get("margin")
        top1 = meta.get("top1_score")
        top2 = meta.get("top2_score")
        if margin is not None:
            margins_all.append((row["test_id"], float(margin), gt, pred, top1, top2))

        if gt == "UNCLEAR":
            unclear_cases.append(
                {
                    "test_id": row["test_id"],
                    "predicted": pred,
                    "top1_score": top1,
                    "margin": margin,
                }
            )

        if row.get("status") != "success" or not pred:
            continue

        exact = pred == gt
        top3 = gt in [c["category_slug"] for c in cands[:3]]
        if not exact:
            wrong.append(
                {
                    "test_id": row["test_id"],
                    "ground_truth": gt,
                    "predicted": pred,
                    "top1_score": top1,
                    "top2_score": top2,
                    "margin": margin,
                }
            )
            pair_counts[(gt, pred)] += 1
            if margin is not None:
                margins_wrong.append((row["test_id"], float(margin), gt, pred))
            if gt in {
                "MOTORCYCLES",
                "WATER_TRANSPORT",
                "BUSES",
                "TRUCK_TRANSPORT",
                "COMMERCIAL_TRANSPORT",
                "OTHER",
                "UNCLEAR",
            }:
                low_support_errors.append(row["test_id"])
        elif top3 and not exact:
            pass
        if (not exact) and top3:
            top3_only.append(row["test_id"])

    focus = []
    for gt, pred in FOCUS_PAIRS:
        focus.append(
            {
                "ground_truth": gt,
                "predicted": pred,
                "count": int(pair_counts.get((gt, pred), 0)),
            }
        )

    # transport confusions from REAL_ESTATE
    re_to_transport = sum(
        pair_counts[(gt, pred)]
        for (gt, pred) in pair_counts
        if gt == "REAL_ESTATE"
        and pred
        in {
            "CAR_SALE",
            "AUTO_PARTS",
            "TRUCK_TRANSPORT",
            "SPECIAL_MACHINERY",
            "MOTORCYCLES",
            "WATER_TRANSPORT",
            "BUSES",
            "COMMERCIAL_TRANSPORT",
        }
    )

    hard_extra = {
        "wrong_top1": [w["test_id"] for w in wrong],
        "correct_only_in_top3": top3_only,
        "smallest_margins": [
            {"test_id": t, "margin": m, "gt": g, "pred": p}
            for t, m, g, p, *_ in sorted(margins_all, key=lambda x: x[1])[:20]
        ],
        "largest_wrong_margins": [
            {"test_id": t, "margin": m, "gt": g, "pred": p}
            for t, m, g, p in sorted(margins_wrong, key=lambda x: -x[1])[:20]
        ],
        "low_support_class_errors": low_support_errors,
        "unclear_gt_cases": unclear_cases,
        "focus_confusion_pairs": focus,
        "real_estate_to_transport_count": re_to_transport,
        "score_note": (
            "SigLIP sigmoid similarity is NOT a calibrated probability; "
            "false-high-confidence threshold is exploratory."
        ),
    }

    hard_path = report_dir / "hard_cases.json"
    existing = {}
    if hard_path.is_file():
        existing = json.loads(hard_path.read_text(encoding="utf-8"))
    existing.update(hard_extra)
    hard_path.write_text(json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8")

    confusion_focus = {
        "focus_pairs": focus,
        "top_pairs": [
            {"ground_truth": a, "predicted": b, "count": c}
            for (a, b), c in pair_counts.most_common(30)
        ],
        "real_estate_to_transport_count": re_to_transport,
    }
    (report_dir / "confusion_focus.json").write_text(
        json.dumps(confusion_focus, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # Append analysis block to summary.md
    summary_path = report_dir / "summary.md"
    extra = [
        "",
        "## SigLIP2 private baseline notes",
        f"- Wrong Top-1: {len(wrong)}",
        f"- Correct only in Top-3: {len(top3_only)}",
        f"- UNCLEAR GT cases kept in predictions: {len(unclear_cases)}",
        f"- Primary Top-1 (excl. UNCLEAR): {metrics.get('leaf_top1')}",
        f"- Primary evaluated: {metrics.get('primary_evaluated')}",
        f"- REAL_ESTATE → transport confusions: {re_to_transport}",
        "- Score semantics: sigmoid similarity (NOT calibrated probability)",
        "- Baseline name: LOCAL VISION V0 — ZERO-SHOT (not aivai-vision-v1)",
        "",
    ]
    if summary_path.is_file():
        summary_path.write_text(
            summary_path.read_text(encoding="utf-8") + "\n".join(extra),
            encoding="utf-8",
        )

    metrics["siglip2_analysis"] = {
        "wrong_top1": len(wrong),
        "top3_only_correct": len(top3_only),
        "unclear_gt": len(unclear_cases),
        "real_estate_to_transport": re_to_transport,
    }
    metrics_path.write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    return hard_extra
