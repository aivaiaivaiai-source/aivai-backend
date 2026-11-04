"""Offline benchmark runner."""

from __future__ import annotations

import json
import os
import platform
import subprocess
import sys
import time
import uuid
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from benchmarks.media_classification.adapters import build_adapter
from benchmarks.media_classification.adapters.base import AdapterClassifyResult
from benchmarks.media_classification.adapters.oracle import ORACLE_BANNER
from benchmarks.media_classification.metrics.quality import (
    CaseEval,
    evaluate_cases,
    fill_cost,
    fill_latency,
)
from benchmarks.media_classification.runner.catalog import load_catalog
from benchmarks.media_classification.runner.hashing import dataset_hash
from benchmarks.media_classification.runner.manifest import validate_manifest
from benchmarks.media_classification.runner.preprocess import (
    prepare_image,
    select_image_paths,
)

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPORTS = PACKAGE_ROOT / "reports"


def _git_hash() -> str | None:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=str(PACKAGE_ROOT.parents[1]),
            stderr=subprocess.DEVNULL,
            text=True,
        )
        return out.strip() or None
    except Exception:
        return None


def _resource_snapshot() -> dict[str, Any]:
    rss = None
    try:
        import psutil  # type: ignore

        rss = psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024)
    except Exception:
        try:
            import resource

            rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            # Linux KB, macOS bytes — leave raw with unit note
            rss = float(rss)
        except Exception:
            rss = None

    cuda: dict[str, Any] = {
        "cuda_allocated_mb": None,
        "cuda_reserved_mb": None,
        "cuda_peak_mb": None,
        "available": False,
    }
    try:
        import torch  # type: ignore

        if torch.cuda.is_available():
            cuda["available"] = True
            cuda["cuda_allocated_mb"] = torch.cuda.memory_allocated() / (1024 * 1024)
            cuda["cuda_reserved_mb"] = torch.cuda.memory_reserved() / (1024 * 1024)
            cuda["cuda_peak_mb"] = torch.cuda.max_memory_allocated() / (1024 * 1024)
    except Exception:
        pass

    return {"rss_mb": rss, "cuda": cuda}


def _case_eval_from_result(
    *,
    test_id: str,
    status: str,
    gt_slug: str,
    gt_hierarchy: tuple[str, ...],
    result: AdapterClassifyResult | None,
    acceptable: list[str],
    high_threshold: float,
    catalog_hierarchy_fn,
) -> CaseEval:
    pred = None
    conf = None
    cands: list[str] = []
    pred_hier: tuple[str, ...] = ()
    if result and result.candidates:
        pred = result.candidates[0].category_slug
        conf = float(result.candidates[0].confidence)
        cands = [c.category_slug for c in result.candidates]
        pred_hier = catalog_hierarchy_fn(pred) if pred else ()

    exact = pred == gt_slug
    acceptable_match = pred in acceptable if pred else False
    l1 = bool(gt_hierarchy and pred_hier and gt_hierarchy[0] == pred_hier[0])
    l2 = bool(
        len(gt_hierarchy) >= 2
        and len(pred_hier) >= 2
        and gt_hierarchy[1] == pred_hier[1]
    )
    top3 = gt_slug in cands[:3]
    false_hi = (
        status == "success"
        and pred is not None
        and not exact
        and conf is not None
        and conf >= high_threshold
    )
    return CaseEval(
        test_id=test_id,
        status=status,
        gt_slug=gt_slug,
        gt_hierarchy_slugs=gt_hierarchy,
        pred_slug=pred,
        pred_hierarchy_slugs=pred_hier,
        top_confidence=conf,
        candidates=cands,
        acceptable_slugs=list(acceptable),
        exact_match=exact,
        acceptable_match=acceptable_match,
        l1_match=l1,
        l2_match=l2,
        top3_exact=top3,
        false_high_confidence=false_hi,
    )


def run_benchmark(
    *,
    manifest_path: Path,
    catalog_path: Path,
    images_root: Path,
    adapter_name: str,
    reports_dir: Path = DEFAULT_REPORTS,
    image_max_edge: int | None = 640,
    image_count_mode: str = "first_3",
    high_confidence_threshold: float = 0.85,
    split_filter: str | None = "test",
    dry_run: bool = False,
    max_listings: int | None = None,
    max_requests: int | None = None,
    max_spend_usd: float | None = None,
    primary_exclude_gt_slugs: set[str] | None = None,
    prompt_set_path: Path | None = None,
    model_id: str | None = None,
    device: str | None = None,
    batch_size: int = 1,
) -> Path:
    catalog = load_catalog(catalog_path)
    validation = validate_manifest(
        manifest_path=manifest_path,
        images_root=images_root,
        catalog=catalog,
        split_filter=split_filter,
    )
    if not validation.ok:
        raise SystemExit(
            "Dataset validation failed:\n" + "\n".join(f"- {e}" for e in validation.errors)
        )

    adapter = build_adapter(
        adapter_name,
        max_images=9,
        image_max_edge=image_max_edge,
        prompt_set_path=prompt_set_path,
        model_id=model_id,
        device=device,
        batch_size=batch_size,
    )
    policy = adapter.input_policy()
    if image_max_edge is not None:
        # runner experiment override for logging; adapter may still apply its own
        pass

    run_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid.uuid4().hex[:8]
    out_dir = reports_dir / run_id
    if out_dir.exists():
        raise RuntimeError(f"Refusing to overwrite existing report dir: {out_dir}")
    out_dir.mkdir(parents=True, exist_ok=False)

    config = {
        "run_id": run_id,
        "adapter": adapter.name,
        "adapter_version": adapter.version,
        "oracle_banner": ORACLE_BANNER if adapter.name == "oracle" else None,
        "manifest": str(manifest_path),
        "catalog": str(catalog_path),
        "catalog_version": catalog.version,
        "catalog_hash": catalog.content_hash,
        "dataset_hash": dataset_hash(manifest_path, catalog_path),
        "images_root": str(images_root),
        "image_max_edge": image_max_edge,
        "image_count_mode": image_count_mode,
        "high_confidence_threshold": high_confidence_threshold,
        "split_filter": split_filter,
        "dry_run": dry_run,
        "max_listings": max_listings,
        "max_requests": max_requests,
        "max_spend_usd": max_spend_usd,
        "adapter_input_policy": asdict(policy),
        "primary_exclude_gt_slugs": sorted(primary_exclude_gt_slugs or []),
        "high_confidence_threshold_note": (
            "exploratory/un-calibrated for SigLIP similarity scores"
            if adapter_name.lower().startswith("siglip")
            else None
        ),
        "git_commit": _git_hash(),
        "timestamp_utc": datetime.now(UTC).isoformat(),
    }
    if hasattr(adapter, "metadata"):
        try:
            config["adapter_metadata"] = adapter.metadata()  # type: ignore[attr-defined]
        except Exception:
            pass
    (out_dir / "config.json").write_text(
        json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    env = {
        "python": sys.version,
        "platform": platform.platform(),
        "processor": platform.processor(),
        "machine": platform.machine(),
        "resources_at_start": _resource_snapshot(),
        "packages": {
            "note": "optional; not enumerating full site-packages",
        },
    }
    (out_dir / "environment.json").write_text(
        json.dumps(env, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    if dry_run:
        summary = {
            "dry_run": True,
            "validated_records": len(validation.records),
            "adapter": adapter.name,
            "adapter_version": adapter.version,
            "catalog_version": catalog.version,
            "catalog_hash": catalog.content_hash,
            "dataset_hash": config["dataset_hash"],
            "message": "Dry run OK — classify() not executed",
        }
        (out_dir / "metrics.json").write_text(
            json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        (out_dir / "predictions.jsonl").write_text("", encoding="utf-8")
        (out_dir / "summary.md").write_text(
            f"# Dry run {run_id}\n\nClassify not executed. Records: {len(validation.records)}\n",
            encoding="utf-8",
        )
        return out_dir

    prepare_t0 = time.perf_counter()
    adapter.prepare()
    cold_prepare_ms = (time.perf_counter() - prepare_t0) * 1000
    if hasattr(adapter, "metadata"):
        try:
            config["adapter_metadata"] = adapter.metadata()  # type: ignore[attr-defined]
            (out_dir / "config.json").write_text(
                json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        except Exception:
            pass

    cases: list[CaseEval] = []
    latencies: list[float] = []
    costs: list[float] = []
    tokens: list[int] = []
    predictions_fp = (out_dir / "predictions.jsonl").open("w", encoding="utf-8")
    wall_t0 = time.perf_counter()
    requests = 0
    spend = 0.0

    try:
        for i, rec in enumerate(validation.records):
            if max_listings is not None and i >= max_listings:
                break
            if max_requests is not None and requests >= max_requests:
                break
            if max_spend_usd is not None and spend >= max_spend_usd:
                break

            selected_rel = select_image_paths(
                rec.images,
                mode=image_count_mode,
                adapter_max=policy.max_images,
            )
            abs_paths = [str((images_root / p).resolve()) for p in selected_rel]

            # Preprocess for metrics logging (adapters may ignore bytes in 3B-1)
            prep_ms = 0.0
            dims: list[dict[str, Any]] = []
            byte_sizes: list[int] = []
            for p in abs_paths:
                prepared = prepare_image(Path(p), max_edge=image_max_edge)
                prep_ms += prepared.preprocess_ms
                dims.append({"w": prepared.width, "h": prepared.height})
                byte_sizes.append(len(prepared.bytes_data))

            t_inf0 = time.perf_counter()
            try:
                result = adapter.classify(
                    test_id=rec.test_id,
                    image_paths=abs_paths,
                    allowed_categories=catalog.active_categories(),
                    ground_truth_slug=rec.ground_truth_slug,
                )
            except Exception as exc:  # noqa: BLE001 — capture as model_error
                result = AdapterClassifyResult(
                    status="model_error",
                    error_message=str(exc)[:500],
                )
            inf_ms = (time.perf_counter() - t_inf0) * 1000
            requests += 1
            if result.request_cost_usd is not None:
                spend += float(result.request_cost_usd)
                costs.append(float(result.request_cost_usd))
            tok = 0
            for part in (result.input_tokens, result.output_tokens, result.image_tokens):
                if part is not None:
                    tok += int(part)
            if tok:
                tokens.append(tok)

            total_ms = prep_ms + (result.latency_ms or inf_ms)
            latencies.append(total_ms)

            status = result.status
            case = _case_eval_from_result(
                test_id=rec.test_id,
                status=status,
                gt_slug=rec.ground_truth_slug,
                gt_hierarchy=catalog.hierarchy_slugs(rec.ground_truth_slug),
                result=result if status == "success" else result,
                acceptable=rec.acceptable_slugs,
                high_threshold=high_confidence_threshold,
                catalog_hierarchy_fn=catalog.hierarchy_slugs,
            )
            # For no_match / errors, clear exact flags appropriately
            if status != "success":
                case.exact_match = False
                case.acceptable_match = False
                case.l1_match = False
                case.l2_match = False
                case.top3_exact = False
                case.false_high_confidence = False
            cases.append(case)

            row = {
                "test_id": rec.test_id,
                "ground_truth": {
                    "category_slug": rec.ground_truth_slug,
                    "category_id": rec.ground_truth_id,
                    "path": rec.ground_truth_path,
                },
                "acceptable_alternatives": rec.acceptable_slugs,
                "status": status,
                "predicted_candidates": [c.to_json() for c in result.candidates],
                "confidence": case.top_confidence,
                "images_used": result.images_used or len(abs_paths),
                "image_paths_used": result.image_paths_used or selected_rel,
                "image_dims": dims,
                "image_bytes": byte_sizes,
                "timings": {
                    "preprocess_ms": prep_ms,
                    "inference_ms": result.inference_ms or inf_ms,
                    "total_ms": total_ms,
                },
                "resource_usage": {
                    "rss_mb": result.rss_mb,
                    "peak_rss_mb": result.peak_rss_mb,
                    "cuda_allocated_mb": result.cuda_allocated_mb,
                    "cuda_reserved_mb": result.cuda_reserved_mb,
                    "cuda_peak_mb": result.cuda_peak_mb,
                },
                "cost_metadata": {
                    "input_tokens": result.input_tokens,
                    "output_tokens": result.output_tokens,
                    "image_tokens": result.image_tokens,
                    "request_cost_usd": result.request_cost_usd,
                    "provider_request_id": result.provider_request_id,
                },
                "error": result.error_message,
                "raw_metadata": result.raw_metadata,
            }
            # Never persist secrets
            for secret_key in ("api_key", "authorization", "signed_url", "token"):
                row["raw_metadata"].pop(secret_key, None)
            predictions_fp.write(json.dumps(row, ensure_ascii=False) + "\n")
    finally:
        predictions_fp.close()
        adapter.close()

    wall_s = time.perf_counter() - wall_t0
    gt_slugs = {c.slug for c in catalog.active_categories()}
    # Prefer GT labels that appear in eval set + all catalog leaves for zero support
    appearing = {c.gt_slug for c in cases}
    metrics = evaluate_cases(
        cases,
        high_confidence_threshold=high_confidence_threshold,
        all_gt_slugs=appearing | gt_slugs,
        primary_exclude_gt_slugs=primary_exclude_gt_slugs,
    )
    fill_latency(metrics, latencies, wall_s)
    fill_cost(metrics, costs=costs, tokens=tokens)
    metrics.resources = _resource_snapshot()
    metrics_json = metrics.to_json()
    metrics_json["cold_prepare_ms"] = cold_prepare_ms
    metrics_json["wall_seconds"] = wall_s
    metrics_json["requests"] = requests
    metrics_json["spend_usd"] = spend if costs else None

    (out_dir / "metrics.json").write_text(
        json.dumps(metrics_json, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    summary_md = _render_summary(run_id, config, metrics_json)
    (out_dir / "summary.md").write_text(summary_md, encoding="utf-8")
    (out_dir / "hard_cases.json").write_text(
        json.dumps(metrics.hard_cases, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (out_dir / "confusion.json").write_text(
        json.dumps(metrics.confusion_pairs, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return out_dir


def _render_summary(run_id: str, config: dict[str, Any], metrics: dict[str, Any]) -> str:
    lines = [
        f"# Benchmark run `{run_id}`",
        "",
        f"- Adapter: `{config['adapter']}` @ `{config['adapter_version']}`",
        f"- Catalog: `{config['catalog_version']}` hash `{config['catalog_hash'][:12]}…`",
        f"- Dataset hash: `{config['dataset_hash'][:12]}…`",
        f"- Image max edge: `{config['image_max_edge']}`",
        f"- Image count mode: `{config['image_count_mode']}`",
        "",
        "## Quality",
        f"- Evaluated: {metrics.get('evaluated')} / total {metrics.get('total')}",
        f"- Errors: {metrics.get('errors')} | no_match: {metrics.get('status_counts', {}).get('no_match')}",
        f"- Leaf Top-1: {metrics.get('leaf_top1')}",
        f"- Leaf Top-3: {metrics.get('leaf_top3')}",
        f"- Leaf acceptable: {metrics.get('leaf_acceptable')}",
        f"- L1 accuracy (success only): {metrics.get('l1_accuracy')}",
        f"- L2 accuracy (success only): {metrics.get('l2_accuracy')}",
        f"- Macro F1: {metrics.get('macro_f1')}",
        f"- False high-confidence: {metrics.get('false_high_confidence_count')} "
        f"(rate {metrics.get('false_high_confidence_rate')})",
        "",
        "## Latency",
        f"- p50: {metrics.get('latency', {}).get('p50_ms')} ms",
        f"- p95: {metrics.get('latency', {}).get('p95_ms')} ms",
        f"- mean: {metrics.get('latency', {}).get('mean_ms')} ms",
        "",
        "## Cost / resources",
        f"- Cost: {metrics.get('cost')}",
        f"- Resources: {metrics.get('resources')}",
        "",
        "This is harness output — not a production model claim.",
    ]
    if config.get("oracle_banner"):
        lines.insert(2, f"- **{config['oracle_banner']}** — metrics self-check only")
    return "\n".join(lines) + "\n"
