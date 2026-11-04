"""CLI entry: python -m benchmarks.media_classification ..."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from benchmarks.media_classification.runner.catalog import load_catalog
from benchmarks.media_classification.runner.compare import compare_runs
from benchmarks.media_classification.runner.manifest import validate_manifest
from benchmarks.media_classification.runner.run import DEFAULT_REPORTS, run_benchmark
from benchmarks.media_classification.seed.build import (
    DEFAULT_CATALOG,
    DEFAULT_DATA_ROOT,
    build_seed,
    inspect_sources,
    summarize_seed_dir,
)
from benchmarks.media_classification.seed.download import DownloadLimits


def _add_common(p: argparse.ArgumentParser) -> None:
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--catalog", type=Path, required=True)
    p.add_argument("--images-root", type=Path, required=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m benchmarks.media_classification",
        description=(
            "AiVai offline media-classification benchmark harness "
            "(3B-1 validate/run + 3B-2 public seed builder)"
        ),
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_val = sub.add_parser("validate", help="Validate manifest + catalog + images")
    _add_common(p_val)
    p_val.add_argument("--split", default="test")

    p_run = sub.add_parser("run", help="Run benchmark adapter over frozen dataset")
    _add_common(p_run)
    p_run.add_argument(
        "--adapter",
        required=True,
        choices=["dummy", "oracle", "siglip2"],
    )
    p_run.add_argument("--image-max-edge", type=int, default=640)
    p_run.add_argument(
        "--image-count-mode",
        default="first_3",
        choices=["cover_only", "first_2", "first_3", "all", "adaptive"],
    )
    p_run.add_argument("--high-confidence-threshold", type=float, default=0.85)
    p_run.add_argument("--split", default="test")
    p_run.add_argument("--reports-dir", type=Path, default=DEFAULT_REPORTS)
    p_run.add_argument("--dry-run", action="store_true")
    p_run.add_argument("--max-listings", type=int, default=None)
    p_run.add_argument("--max-requests", type=int, default=None)
    p_run.add_argument("--max-spend-usd", type=float, default=None)
    p_run.add_argument(
        "--exclude-gt",
        action="append",
        default=[],
        help="GT slugs excluded from primary Top-1 denominator (e.g. UNCLEAR)",
    )
    p_run.add_argument("--prompt-set", type=Path, default=None)
    p_run.add_argument("--model-id", type=str, default=None)
    p_run.add_argument("--device", type=str, default=None)
    p_run.add_argument("--batch-size", type=int, default=1)

    p_cmp = sub.add_parser("compare", help="Compare existing report directories")
    p_cmp.add_argument("runs", nargs="+", type=Path)

    sub.add_parser(
        "inspect-sources",
        help="Print provenance/license audit table (no download)",
    )

    p_seed = sub.add_parser(
        "build-seed",
        help="Build public-seed-v1 from APPROVED sources only",
    )
    p_seed.add_argument("--seed", type=int, default=42)
    p_seed.add_argument("--target-cases", type=int, default=120)
    p_seed.add_argument("--data-root", type=Path, default=DEFAULT_DATA_ROOT)
    p_seed.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    p_seed.add_argument("--dry-run", action="store_true")
    p_seed.add_argument("--max-total-files", type=int, default=250)
    p_seed.add_argument("--max-total-bytes", type=int, default=80 * 1024 * 1024)
    p_seed.add_argument("--max-per-source-files", type=int, default=200)
    p_seed.add_argument("--timeout-s", type=int, default=60)
    p_seed.add_argument("--retries", type=int, default=2)

    p_vs = sub.add_parser(
        "validate-seed",
        help="Validate built seed via 3B-1 harness",
    )
    p_vs.add_argument("--data-root", type=Path, default=DEFAULT_DATA_ROOT)
    p_vs.add_argument("--split", default="test")

    p_sum = sub.add_parser("summarize-seed", help="Summarize built seed directory")
    p_sum.add_argument("--data-root", type=Path, default=DEFAULT_DATA_ROOT)

    args = parser.parse_args(argv)

    if args.cmd == "validate":
        catalog = load_catalog(args.catalog)
        result = validate_manifest(
            manifest_path=args.manifest,
            images_root=args.images_root,
            catalog=catalog,
            split_filter=args.split,
        )
        if not result.ok:
            print("FAIL")
            for e in result.errors:
                print(f"  - {e}")
            return 1
        print(
            f"OK records={len(result.records)} catalog={catalog.version} "
            f"hash={catalog.content_hash[:16]}…"
        )
        return 0

    if args.cmd == "run":
        edge = args.image_max_edge
        exclude = set(args.exclude_gt or [])
        out = run_benchmark(
            manifest_path=args.manifest,
            catalog_path=args.catalog,
            images_root=args.images_root,
            adapter_name=args.adapter,
            reports_dir=args.reports_dir,
            image_max_edge=edge if edge > 0 else None,
            image_count_mode=args.image_count_mode,
            high_confidence_threshold=args.high_confidence_threshold,
            split_filter=args.split,
            dry_run=args.dry_run,
            max_listings=args.max_listings,
            max_requests=args.max_requests,
            max_spend_usd=args.max_spend_usd,
            primary_exclude_gt_slugs=exclude or None,
            prompt_set_path=args.prompt_set,
            model_id=args.model_id,
            device=args.device,
            batch_size=args.batch_size,
        )
        if args.adapter == "siglip2" and not args.dry_run:
            from benchmarks.media_classification.runner.siglip2_analysis import (
                enrich_siglip2_report,
            )

            enrich_siglip2_report(out)
        print(f"Report written: {out}")
        return 0

    if args.cmd == "compare":
        print(compare_runs(list(args.runs)))
        return 0

    if args.cmd == "inspect-sources":
        print(json.dumps(inspect_sources(), ensure_ascii=False, indent=2))
        return 0

    if args.cmd == "build-seed":
        limits = DownloadLimits(
            max_total_files=args.max_total_files,
            max_total_bytes=args.max_total_bytes,
            max_per_source_files=args.max_per_source_files,
            timeout_s=args.timeout_s,
            retries=args.retries,
        )
        report = build_seed(
            data_root=args.data_root,
            catalog_path=args.catalog,
            seed=args.seed,
            target_cases=args.target_cases,
            dry_run=args.dry_run,
            limits=limits,
        )
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0 if report.get("status") in {"dry_run_ok", "frozen"} else 1

    if args.cmd == "validate-seed":
        root = args.data_root.resolve()
        manifest = root / "manifest.jsonl"
        catalog_path = root / "category_catalog.json"
        images = root / "images"
        if not manifest.is_file() or not catalog_path.is_file():
            print("FAIL: seed artifacts missing (run build-seed first)")
            return 1
        catalog = load_catalog(catalog_path)
        result = validate_manifest(
            manifest_path=manifest,
            images_root=images,
            catalog=catalog,
            split_filter=args.split,
        )
        if not result.ok:
            print("FAIL")
            for e in result.errors:
                print(f"  - {e}")
            return 1
        print(f"OK seed records={len(result.records)} catalog={catalog.version}")
        return 0

    if args.cmd == "summarize-seed":
        print(json.dumps(summarize_seed_dir(args.data_root), ensure_ascii=False, indent=2))
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
