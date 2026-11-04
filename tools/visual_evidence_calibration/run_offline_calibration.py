"""Offline Visual Evidence calibration on frozen aivai-private-seed-v1 (3C-2B).

PRIVATE — reports are gitignored. No image bytes in output.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
import time
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[2]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.visual_evidence.calibration.decision_policy import (  # noqa: E402
    CalibrationConfig,
    apply_decision_policy,
)
from app.visual_evidence.calibration.prompt_utils import (  # noqa: E402
    compute_prompt_hash,
    load_prompt_metadata,
)
from app.visual_evidence.siglip2_runtime import (  # noqa: E402
    DEFAULT_PROMPT_SET,
    MODEL_VERSION,
    PROMPT_VERSION,
    SigLIP2ModelRuntime,
    reset_siglip2_runtime_for_tests,
)

PRIVATE_SEED = (
    BACKEND_ROOT
    / "benchmarks"
    / "media_classification"
    / "data"
    / "aivai_private_seed_v1"
)
MAPPING_PATH = (
    BACKEND_ROOT
    / "app"
    / "visual_evidence"
    / "calibration"
    / "gt_visual_mapping_v1.json"
)
REPORTS_ROOT = BACKEND_ROOT / "benchmarks" / "visual_evidence_calibration" / "reports"
CALIBRATION_OUT = (
    BACKEND_ROOT
    / "app"
    / "visual_evidence"
    / "calibration"
    / "visual_evidence_calibration_v1.json"
)


@dataclass
class CaseRecord:
    test_id: str
    gt_slug: str
    image_path: str
    source_group_id: str
    split: str


def load_mapping() -> dict:
    return json.loads(MAPPING_PATH.read_text(encoding="utf-8"))


def expected_concepts(mapping: dict, gt_slug: str) -> tuple[list[str], bool]:
    rule = mapping["slug_to_visual_family"][gt_slug]
    primary = list(rule.get("primary") or [])
    acceptable = list(rule.get("acceptable") or [])
    exclude = bool(rule.get("exclude_from_primary_denominator"))
    return primary + acceptable, exclude


def load_cases(seed_root: Path) -> list[CaseRecord]:
    manifest = seed_root / "manifest.jsonl"
    raw_dir = seed_root / "raw"
    cases: list[CaseRecord] = []
    for line in manifest.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        img_name = row["images"][0]
        cases.append(
            CaseRecord(
                test_id=row["test_id"],
                gt_slug=row["ground_truth"]["category_slug"],
                image_path=str(raw_dir / img_name),
                source_group_id=row.get("source_group_id") or row["test_id"],
                split=row.get("split") or "test",
            )
        )
    return cases


def deterministic_split(cases: list[CaseRecord], *, holdout_ratio: float = 0.2) -> dict[str, str]:
    """Stratified-by-slug split with source_group_id isolation."""
    by_slug: dict[str, list[CaseRecord]] = defaultdict(list)
    for c in cases:
        by_slug[c.gt_slug].append(c)
    assignment: dict[str, str] = {}
    for slug, group in by_slug.items():
        ordered = sorted(group, key=lambda c: c.test_id)
        n_hold = max(1, int(round(len(ordered) * holdout_ratio))) if len(ordered) >= 5 else 1
        if slug in ("UNCLEAR", "OTHER"):
            n_hold = min(n_hold, len(ordered))
        hold_ids = {c.test_id for c in ordered[-n_hold:]}
        for c in ordered:
            assignment[c.test_id] = "holdout" if c.test_id in hold_ids else "calibration"
    return assignment


def score_production_runtime(cases: list[CaseRecord]) -> list[dict]:
    reset_siglip2_runtime_for_tests()
    rt = SigLIP2ModelRuntime()
    rt.prepare()
    rows: list[dict] = []
    t0 = time.perf_counter()
    for i, case in enumerate(cases, start=1):
        blob = Path(case.image_path).read_bytes()
        scores = rt.score_image_bytes(blob)
        ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
        top1 = ranked[0] if ranked else (None, 0.0)
        top2 = ranked[1] if len(ranked) > 1 else (None, 0.0)
        rows.append(
            {
                "test_id": case.test_id,
                "gt_slug": case.gt_slug,
                "source_group_id": case.source_group_id,
                "scores": scores,
                "top1": top1[0],
                "top1_score": top1[1],
                "top2": top2[0],
                "top2_score": top2[1],
                "margin_top1_top2": top1[1] - top2[1],
            }
        )
        if i % 20 == 0:
            elapsed = time.perf_counter() - t0
            print(f"scored {i}/{len(cases)} elapsed_s={elapsed:.1f}", flush=True)
    return rows


def compare_benchmark_adapter(sample_paths: list[Path]) -> list[dict]:
    """Score semantics: production runtime vs benchmark-adapter forward pass on VE prompts."""
    import torch
    from PIL import Image

    from benchmarks.media_classification.adapters.siglip2 import SigLIP2BenchmarkAdapter

    prompt_set = json.loads(DEFAULT_PROMPT_SET.read_text(encoding="utf-8"))
    overlay = BACKEND_ROOT / "benchmarks" / "visual_evidence_calibration" / "_ve_prompt_overlay.json"
    overlay.parent.mkdir(parents=True, exist_ok=True)
    adapter_prompt = {
        "prompt_set_version": "siglip2-zero-shot-prompts-v1",
        "prompts": prompt_set["concepts"],
        "exclude_from_candidates": ["UNKNOWN_VISUAL"],
    }
    overlay.write_text(json.dumps(adapter_prompt, indent=2), encoding="utf-8")

    reset_siglip2_runtime_for_tests()
    rt = SigLIP2ModelRuntime()
    rt.prepare()
    adapter = SigLIP2BenchmarkAdapter(prompt_set_path=overlay, target_max_edge=224)
    adapter.prepare()

    concept_order = list(prompt_set["concepts"].keys())
    texts = [prompt_set["concepts"][c] for c in concept_order]

    comparisons: list[dict] = []
    for path in sample_paths:
        blob = path.read_bytes()
        prod = rt.score_image_bytes(blob)

        with Image.open(path) as im:
            image = im.convert("RGB")
            image.thumbnail((896, 896))
        inputs = adapter._processor(
            text=texts,
            images=image,
            padding="max_length",
            return_tensors="pt",
        )
        inputs = {k: v.to(adapter._device) for k, v in inputs.items()}
        with torch.no_grad():
            outputs = adapter._model(**inputs)
            logits = outputs.logits_per_image.squeeze(0)
            scores = torch.sigmoid(logits).detach().float().cpu()
        bench = dict(zip(concept_order, [float(x) for x in scores.tolist()], strict=True))

        diffs = {k: abs(prod[k] - bench[k]) for k in prod}
        max_diff = max(diffs.values()) if diffs else 0.0
        comparisons.append(
            {
                "image": str(path),
                "max_abs_diff": max_diff,
                "prod_top3": sorted(prod.items(), key=lambda kv: kv[1], reverse=True)[:3],
                "bench_top3": sorted(bench.items(), key=lambda kv: kv[1], reverse=True)[:3],
            }
        )
    return comparisons


def concept_hits(concept: str | None, expected: list[str]) -> bool:
    return bool(concept and concept in expected)


def evaluate_policy(
    scored_rows: list[dict],
    *,
    mapping: dict,
    split_assignment: dict[str, str],
    subset: str,
    config: CalibrationConfig,
) -> dict:
    primary_total = 0
    top1_correct = 0
    top3_recall = 0
    accepted = 0
    accepted_correct = 0
    false_accepts = 0
    no_match = 0
    per_slug = Counter()
    per_slug_correct = Counter()
    confusion: Counter[tuple[str, str]] = Counter()

    for row in scored_rows:
        if split_assignment.get(row["test_id"]) != subset:
            continue
        expected, exclude = expected_concepts(mapping, row["gt_slug"])
        if exclude:
            continue
        primary_total += 1
        per_slug[row["gt_slug"]] += 1

        decision = apply_decision_policy(row["scores"], config=config)
        ranked = sorted(row["scores"].items(), key=lambda kv: kv[1], reverse=True)
        top3 = [c for c, _ in ranked[:3]]

        if concept_hits(row["top1"], expected):
            top1_correct += 1
        if any(concept_hits(c, expected) for c in top3):
            top3_recall += 1

        if decision.no_match:
            no_match += 1
            continue

        accepted += 1
        pred = decision.accepted_concepts[0]
        if concept_hits(pred, expected):
            accepted_correct += 1
            per_slug_correct[row["gt_slug"]] += 1
        else:
            false_accepts += 1
            confusion[(row["gt_slug"], pred)] += 1

    coverage = accepted / primary_total if primary_total else 0.0
    return {
        "subset": subset,
        "primary_total": primary_total,
        "coverage": coverage,
        "no_match_rate": no_match / primary_total if primary_total else 0.0,
        "top1_visual_family_accuracy": top1_correct / primary_total if primary_total else 0.0,
        "top3_visual_family_recall": top3_recall / primary_total if primary_total else 0.0,
        "accepted_accuracy": accepted_correct / accepted if accepted else 0.0,
        "false_accept_rate": false_accepts / accepted if accepted else 0.0,
        "accepted_count": accepted,
        "false_accepts": false_accepts,
        "per_slug_support": dict(per_slug),
        "per_slug_accepted_correct": dict(per_slug_correct),
        "confusion_pairs": {f"{a}->{b}": n for (a, b), n in confusion.most_common(15)},
    }


def grid_search(
    scored_rows: list[dict],
    *,
    mapping: dict,
    split_assignment: dict[str, str],
) -> list[dict]:
    candidates: list[dict] = []

    # Policy A — absolute threshold only
    for t in [0.01, 0.015, 0.02, 0.025, 0.03, 0.04, 0.05, 0.06, 0.08, 0.10, 0.12, 0.15]:
        for max_obs in [1, 2, 3]:
            cfg = CalibrationConfig(
                calibration_version="search",
                model_version=MODEL_VERSION,
                prompt_version=PROMPT_VERSION,
                prompt_hash="",
                policy_family="absolute_threshold",
                min_evidence_score=t,
                min_margin=0.0,
                max_observations=max_obs,
                exclude_concepts=frozenset({"UNKNOWN_VISUAL"}),
                aggregation="max_score_per_concept",
            )
            cal = evaluate_policy(
                scored_rows, mapping=mapping, split_assignment=split_assignment, subset="calibration", config=cfg
            )
            candidates.append(
                {
                    "config": {
                        **{k: v for k, v in asdict(cfg).items() if k != "exclude_concepts"},
                        "exclude_concepts": sorted(cfg.exclude_concepts),
                    },
                    "calibration": cal,
                }
            )

    # Policy B/C — margin oriented
    for t in [0.01, 0.015, 0.02, 0.03, 0.04, 0.05, 0.06, 0.08, 0.10]:
        for m in [0.0, 0.005, 0.01, 0.015, 0.02, 0.03, 0.04, 0.05]:
            for max_obs in [1, 2, 3]:
                cfg = CalibrationConfig(
                    calibration_version="search",
                    model_version=MODEL_VERSION,
                    prompt_version=PROMPT_VERSION,
                    prompt_hash="",
                    policy_family="margin_oriented",
                    min_evidence_score=t,
                    min_margin=m,
                    max_observations=max_obs,
                    exclude_concepts=frozenset({"UNKNOWN_VISUAL"}),
                    aggregation="max_score_per_concept",
                )
                cal = evaluate_policy(
                    scored_rows, mapping=mapping, split_assignment=split_assignment, subset="calibration", config=cfg
                )
                candidates.append(
                {
                    "config": {
                        **{k: v for k, v in asdict(cfg).items() if k != "exclude_concepts"},
                        "exclude_concepts": sorted(cfg.exclude_concepts),
                    },
                    "calibration": cal,
                }
            )

    return candidates


def score_candidate(item: dict) -> float:
    cal = item["calibration"]
    coverage = cal["coverage"]
    acc = cal["accepted_accuracy"]
    false_rate = cal["false_accept_rate"]
    top3 = cal["top3_visual_family_recall"]
    # Conservative utility: reward useful coverage + accuracy, penalize false accepts heavily
    if coverage <= 0.05:
        return -1.0
    return (
        0.35 * acc
        + 0.20 * top3
        + 0.25 * coverage
        - 0.45 * false_rate
        - 0.10 * max(0.0, false_rate - 0.15) * 2
    )


def select_best(candidates: list[dict]) -> dict:
    ranked = sorted(candidates, key=score_candidate, reverse=True)
    return ranked[0]


def write_calibration_config(best: dict, *, report_dir: Path, prompt_hash: str) -> None:
    cfg_dict = best["config"]
    policy = {
        "family": cfg_dict["policy_family"],
        "min_evidence_score": cfg_dict["min_evidence_score"],
        "min_margin": cfg_dict["min_margin"],
        "max_observations": cfg_dict["max_observations"],
        "exclude_concepts": sorted(cfg_dict["exclude_concepts"]),
        "score_semantics": "evidence_score — sigmoid similarity, NOT calibrated probability",
    }
    payload = {
        "calibration_version": "visual-evidence-calibration-v1",
        "model_version": MODEL_VERSION,
        "prompt_version": PROMPT_VERSION,
        "prompt_hash": prompt_hash,
        "dataset_version": "aivai-private-seed-v1",
        "mapping_version": "gt-visual-mapping-v1",
        "aggregation": "max_score_per_concept",
        "policy": policy,
        "selection": {
            "selected_on": "calibration_subset",
            "utility_score": score_candidate(best),
            "calibration_metrics": best["calibration"],
        },
        "report_dir": str(report_dir.name),
        "generated_at": datetime.now(UTC).isoformat(),
    }
    CALIBRATION_OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Offline Visual Evidence calibration")
    parser.add_argument("--seed-root", type=Path, default=PRIVATE_SEED)
    parser.add_argument("--holdout-ratio", type=float, default=0.2)
    parser.add_argument("--scores-file", type=Path, default=None)
    args = parser.parse_args()

    if not (args.seed_root / "FROZEN").is_file():
        raise SystemExit(f"refuse: dataset not frozen at {args.seed_root}")

    mapping = load_mapping()
    mapping_hash = hashlib.sha256(
        json.dumps(mapping, sort_keys=True).encode("utf-8")
    ).hexdigest()[:16]
    prompt_version, prompt_hash = load_prompt_metadata()

    cases = load_cases(args.seed_root)
    split_assignment = deterministic_split(cases, holdout_ratio=args.holdout_ratio)

    ts = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    report_dir = REPORTS_ROOT / f"{ts}_{mapping_hash[:8]}"
    report_dir.mkdir(parents=True, exist_ok=True)

    print(f"cases={len(cases)} mapping_hash={mapping_hash} prompt_hash={prompt_hash}")

    # Score semantics on 5 stratified samples
    sample_paths = [
        Path(c.image_path)
        for c in sorted(cases, key=lambda x: x.test_id)[::26][:5]
    ]
    semantics = compare_benchmark_adapter(sample_paths)
    max_sem_diff = max(r["max_abs_diff"] for r in semantics)
    (report_dir / "score_semantics_check.json").write_text(
        json.dumps(
            {
                "production_runtime": "SigLIP2ModelRuntime + visual_evidence_prompts_v1",
                "benchmark_adapter": "SigLIP2BenchmarkAdapter + VE prompt overlay",
                "max_abs_diff": max_sem_diff,
                "samples": semantics,
                "pass": max_sem_diff < 1e-4,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"score_semantics max_abs_diff={max_sem_diff:.2e} pass={max_sem_diff < 1e-4}")

    if args.scores_file and args.scores_file.is_file():
        scored = [json.loads(line) for line in args.scores_file.read_text(encoding="utf-8").splitlines() if line.strip()]
        print(f"loaded scored rows={len(scored)} from {args.scores_file}")
    else:
        scored = score_production_runtime(cases)
        for row in scored:
            row["split"] = split_assignment[row["test_id"]]
            expected, exclude = expected_concepts(mapping, row["gt_slug"])
            row["expected_visual_family"] = expected
            row["exclude_from_primary"] = exclude
            ranked = sorted(row["scores"].items(), key=lambda kv: kv[1], reverse=True)
            expected_rank = next(
                (i + 1 for i, (c, _) in enumerate(ranked) if c in expected),
                None,
            )
            row["rank_of_expected"] = expected_rank

        with (report_dir / "raw_scores.jsonl").open("w", encoding="utf-8") as f:
            for row in scored:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")

    if not scored[0].get("split"):
        for row in scored:
            row["split"] = split_assignment[row["test_id"]]
            expected, exclude = expected_concepts(mapping, row["gt_slug"])
            row["expected_visual_family"] = expected
            row["exclude_from_primary"] = exclude

    candidates = grid_search(scored, mapping=mapping, split_assignment=split_assignment)
    best = select_best(candidates)
    cfg_raw = best["config"]
    chosen = CalibrationConfig(
        calibration_version="visual-evidence-calibration-v1",
        model_version=MODEL_VERSION,
        prompt_version=PROMPT_VERSION,
        prompt_hash=prompt_hash,
        policy_family=cfg_raw["policy_family"],
        min_evidence_score=cfg_raw["min_evidence_score"],
        min_margin=cfg_raw["min_margin"],
        max_observations=cfg_raw["max_observations"],
        exclude_concepts=frozenset(cfg_raw["exclude_concepts"]),
        aggregation="max_score_per_concept",
    )

    holdout = evaluate_policy(
        scored, mapping=mapping, split_assignment=split_assignment, subset="holdout", config=chosen
    )
    calibration = best["calibration"]

    chosen_dict = {
        "calibration_version": chosen.calibration_version,
        "model_version": chosen.model_version,
        "prompt_version": chosen.prompt_version,
        "prompt_hash": chosen.prompt_hash,
        "policy_family": chosen.policy_family,
        "min_evidence_score": chosen.min_evidence_score,
        "min_margin": chosen.min_margin,
        "max_observations": chosen.max_observations,
        "exclude_concepts": sorted(chosen.exclude_concepts),
        "aggregation": chosen.aggregation,
    }
    summary = {
        "report_id": report_dir.name,
        "dataset_version": "aivai-private-seed-v1",
        "mapping_version": mapping["mapping_version"],
        "mapping_hash": mapping_hash,
        "prompt_version": prompt_version,
        "prompt_hash": prompt_hash,
        "model_version": MODEL_VERSION,
        "score_semantics_pass": max_sem_diff < 1e-4,
        "split_counts": Counter(split_assignment.values()),
        "chosen_policy": chosen_dict,
        "calibration_metrics": calibration,
        "holdout_metrics": holdout,
        "utility_score": score_candidate(best),
    }
    (report_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    # Margin / score distribution stats
    margins = [r["margin_top1_top2"] for r in scored if not r["exclude_from_primary"]]
    top1_scores = [r["top1_score"] for r in scored if not r["exclude_from_primary"]]
    (report_dir / "distributions.json").write_text(
        json.dumps(
            {
                "top1_score": {
                    "min": min(top1_scores),
                    "max": max(top1_scores),
                    "mean": sum(top1_scores) / len(top1_scores),
                    "p50": sorted(top1_scores)[len(top1_scores) // 2],
                },
                "margin_top1_top2": {
                    "min": min(margins),
                    "max": max(margins),
                    "mean": sum(margins) / len(margins),
                    "p50": sorted(margins)[len(margins) // 2],
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    write_calibration_config(best, report_dir=report_dir, prompt_hash=prompt_hash)
    print(json.dumps(summary, indent=2))
    print(f"Wrote calibration to {CALIBRATION_OUT}")
    print(f"Reports in {report_dir}")


if __name__ == "__main__":
    main()
