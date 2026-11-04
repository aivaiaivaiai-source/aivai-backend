"""Quality / hierarchical / confidence metrics for offline benchmark."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Any


@dataclass
class CaseEval:
    test_id: str
    status: str
    gt_slug: str
    gt_hierarchy_slugs: tuple[str, ...]
    pred_slug: str | None
    pred_hierarchy_slugs: tuple[str, ...]
    top_confidence: float | None
    candidates: list[str]
    acceptable_slugs: list[str]
    exact_match: bool = False
    acceptable_match: bool = False
    l1_match: bool = False
    l2_match: bool = False
    top3_exact: bool = False
    false_high_confidence: bool = False


@dataclass
class MetricsBundle:
    total: int = 0
    evaluated: int = 0
    skipped: int = 0
    errors: int = 0
    success: int = 0
    no_match: int = 0
    timeout: int = 0
    model_error: int = 0
    invalid_output: int = 0
    leaf_top1: float | None = None
    leaf_top3: float | None = None
    leaf_acceptable: float | None = None
    primary_evaluated: int | None = None
    primary_exclude_gt_slugs: list[str] = field(default_factory=list)
    l1_accuracy: float | None = None
    l2_accuracy: float | None = None
    macro_f1: float | None = None
    per_category: dict[str, dict[str, float]] = field(default_factory=dict)
    confusion_pairs: list[dict[str, Any]] = field(default_factory=list)
    false_high_confidence_count: int = 0
    false_high_confidence_rate: float | None = None
    override_required_proxy: int = 0
    hard_cases: dict[str, list[str]] = field(default_factory=dict)
    latency: dict[str, float | None] = field(default_factory=dict)
    cost: dict[str, Any] = field(default_factory=dict)
    resources: dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> dict[str, Any]:
        return {
            "total": self.total,
            "evaluated": self.evaluated,
            "skipped": self.skipped,
            "errors": self.errors,
            "status_counts": {
                "success": self.success,
                "no_match": self.no_match,
                "timeout": self.timeout,
                "model_error": self.model_error,
                "invalid_output": self.invalid_output,
            },
            "leaf_top1": self.leaf_top1,
            "leaf_top3": self.leaf_top3,
            "leaf_acceptable": self.leaf_acceptable,
            "primary_evaluated": self.primary_evaluated,
            "primary_exclude_gt_slugs": self.primary_exclude_gt_slugs,
            "l1_accuracy": self.l1_accuracy,
            "l2_accuracy": self.l2_accuracy,
            "macro_f1": self.macro_f1,
            "per_category": self.per_category,
            "confusion_pairs": self.confusion_pairs,
            "false_high_confidence_count": self.false_high_confidence_count,
            "false_high_confidence_rate": self.false_high_confidence_rate,
            "override_required_proxy": self.override_required_proxy,
            "hard_cases": self.hard_cases,
            "latency": self.latency,
            "cost": self.cost,
            "resources": self.resources,
        }


def _rate(num: int, den: int) -> float | None:
    if den <= 0:
        return None
    return num / den


def evaluate_cases(
    cases: list[CaseEval],
    *,
    high_confidence_threshold: float,
    all_gt_slugs: set[str],
    primary_exclude_gt_slugs: set[str] | None = None,
) -> MetricsBundle:
    bundle = MetricsBundle(total=len(cases))
    tp: dict[str, int] = defaultdict(int)
    fp: dict[str, int] = defaultdict(int)
    fn: dict[str, int] = defaultdict(int)
    confusion: Counter[tuple[str, str]] = Counter()
    confusion_examples: dict[tuple[str, str], list[str]] = defaultdict(list)

    hard: dict[str, list[str]] = {
        "wrong_high_confidence": [],
        "no_match": [],
        "timeout": [],
        "model_error": [],
        "invalid_output": [],
        "ambiguous_alternatives": [],
        "rare_or_zero_sample_categories": [],
    }

    for c in cases:
        if c.status == "skipped":
            bundle.skipped += 1
            continue
        if c.status in ("timeout", "model_error", "invalid_output"):
            bundle.errors += 1
            hard[c.status].append(c.test_id)
            if c.status == "timeout":
                bundle.timeout += 1
            elif c.status == "model_error":
                bundle.model_error += 1
            else:
                bundle.invalid_output += 1
            continue
        if c.status == "no_match":
            bundle.no_match += 1
            hard["no_match"].append(c.test_id)
            # counts as evaluated miss for leaf metrics
            bundle.evaluated += 1
            fn[c.gt_slug] += 1
            bundle.override_required_proxy += 1
            continue

        # success
        bundle.success += 1
        bundle.evaluated += 1

        if c.exact_match:
            tp[c.gt_slug] += 1
        else:
            fn[c.gt_slug] += 1
            if c.pred_slug:
                fp[c.pred_slug] += 1
                key = (c.gt_slug, c.pred_slug)
                confusion[key] += 1
                if len(confusion_examples[key]) < 5:
                    confusion_examples[key].append(c.test_id)
            bundle.override_required_proxy += 1

        if c.false_high_confidence:
            bundle.false_high_confidence_count += 1
            hard["wrong_high_confidence"].append(c.test_id)

        if c.acceptable_slugs:
            hard["ambiguous_alternatives"].append(c.test_id)

    # leaf rates among evaluated (success + no_match)
    exclude = set(primary_exclude_gt_slugs or ())
    primary_cases = [c for c in cases if c.gt_slug not in exclude]
    exact = sum(1 for c in primary_cases if c.status == "success" and c.exact_match)
    top3 = sum(1 for c in primary_cases if c.status == "success" and c.top3_exact)
    acceptable = sum(
        1
        for c in primary_cases
        if c.status == "success" and (c.exact_match or c.acceptable_match)
    )
    l1 = sum(1 for c in cases if c.status == "success" and c.l1_match)
    l2 = sum(1 for c in cases if c.status == "success" and c.l2_match)
    success_n = bundle.success
    eval_n = bundle.evaluated
    primary_eval_n = sum(
        1
        for c in primary_cases
        if c.status in ("success", "no_match")
    )

    bundle.leaf_top1 = _rate(exact, primary_eval_n)
    bundle.leaf_top3 = _rate(top3, primary_eval_n)
    bundle.leaf_acceptable = _rate(acceptable, primary_eval_n)
    bundle.primary_evaluated = primary_eval_n
    bundle.primary_exclude_gt_slugs = sorted(exclude)
    bundle.l1_accuracy = _rate(l1, success_n) if success_n else None
    bundle.l2_accuracy = _rate(l2, success_n) if success_n else None
    # false-high uses exploratory threshold; note scores may be uncalibrated
    primary_false_hi = sum(
        1
        for c in primary_cases
        if c.status == "success" and c.false_high_confidence
    )
    bundle.false_high_confidence_rate = _rate(primary_false_hi, primary_eval_n)

    # per-category P/R/F1 including zero-sample classes from catalog set
    labels = sorted(all_gt_slugs | set(tp) | set(fp) | set(fn))
    f1s: list[float] = []
    for slug in labels:
        tpi, fpi, fni = tp[slug], fp[slug], fn[slug]
        prec = tpi / (tpi + fpi) if (tpi + fpi) else 0.0
        rec = tpi / (tpi + fni) if (tpi + fni) else 0.0
        f1 = (2 * prec * rec / (prec + rec)) if (prec + rec) else 0.0
        support = tpi + fni
        bundle.per_category[slug] = {
            "precision": prec,
            "recall": rec,
            "f1": f1,
            "support": float(support),
        }
        if support > 0:
            f1s.append(f1)
        else:
            hard["rare_or_zero_sample_categories"].append(slug)

    bundle.macro_f1 = (sum(f1s) / len(f1s)) if f1s else None

    for (gt, pred), count in confusion.most_common(50):
        bundle.confusion_pairs.append(
            {
                "ground_truth": gt,
                "predicted": pred,
                "count": count,
                "example_test_ids": confusion_examples[(gt, pred)],
            }
        )

    bundle.hard_cases = hard
    bundle.latency = {
        "p50_ms": None,
        "p95_ms": None,
        "mean_ms": None,
        "throughput_per_s": None,
    }
    bundle.cost = {
        "total_usd": None,
        "cost_per_listing": None,
        "projected_cost_per_1k": None,
        "projected_cost_per_1m": None,
        "total_tokens": None,
        "note": "N/A until external adapters report costs",
    }
    bundle.resources = {
        "rss_mb": None,
        "peak_rss_mb": None,
        "cuda_allocated_mb": None,
        "cuda_reserved_mb": None,
        "cuda_peak_mb": None,
        "note": "N/A until local GPU adapters instrument",
    }
    return bundle


def percentile(values: list[float], p: float) -> float | None:
    if not values:
        return None
    xs = sorted(values)
    if len(xs) == 1:
        return xs[0]
    k = (len(xs) - 1) * (p / 100.0)
    f = int(k)
    c = min(f + 1, len(xs) - 1)
    if f == c:
        return xs[f]
    return xs[f] + (xs[c] - xs[f]) * (k - f)


def fill_latency(bundle: MetricsBundle, latencies_ms: list[float], wall_s: float) -> None:
    bundle.latency = {
        "p50_ms": percentile(latencies_ms, 50),
        "p95_ms": percentile(latencies_ms, 95),
        "mean_ms": (sum(latencies_ms) / len(latencies_ms)) if latencies_ms else None,
        "throughput_per_s": (len(latencies_ms) / wall_s) if wall_s > 0 else None,
        "count": float(len(latencies_ms)),
    }


def fill_cost(
    bundle: MetricsBundle,
    *,
    costs: list[float],
    tokens: list[int],
) -> None:
    if not costs:
        return
    total = sum(costs)
    n = len(costs)
    per = total / n if n else None
    bundle.cost = {
        "total_usd": total,
        "cost_per_listing": per,
        "projected_cost_per_1k": (per * 1000) if per is not None else None,
        "projected_cost_per_1m": (per * 1_000_000) if per is not None else None,
        "total_tokens": sum(tokens) if tokens else None,
        "note": "from adapter-reported costs only",
    }
