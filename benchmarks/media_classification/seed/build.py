"""Build public-seed-v1 from APPROVED sources only."""

from __future__ import annotations

import json
import shutil
from collections import Counter
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from benchmarks.media_classification.runner.catalog import load_catalog
from benchmarks.media_classification.runner.hashing import dataset_hash, sha256_file
from benchmarks.media_classification.runner.manifest import validate_manifest
from benchmarks.media_classification.seed.download import (
    DownloadLimits,
    download_clothing_small_subset,
)
from benchmarks.media_classification.seed.mapping import (
    NO_CURRENT_AIVAI_MATCH,
    aivai_match_status,
    map_clothing_label,
)
from benchmarks.media_classification.seed.provenance import (
    SOURCE_AUDITS,
    audits_by_verdict,
    get_audit,
)

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_ROOT = PACKAGE_ROOT / "data" / "public_seed_v1"
DEFAULT_CATALOG = PACKAGE_ROOT / "catalog" / "seed_catalog.json"
SEED_VERSION = "public-seed-v1"


def inspect_sources() -> dict[str, Any]:
    by = audits_by_verdict()
    return {
        "checked_at": "2026-08-25",
        "counts": {k: len(v) for k, v in by.items()},
        "sources": [a.to_json() for a in SOURCE_AUDITS],
    }


def _difficulty_for(mapping_confidence: str, review: bool) -> str:
    if review or mapping_confidence == "ambiguous":
        return "ambiguous"
    if mapping_confidence == "approximate":
        return "medium"
    return "easy"


def build_seed(
    *,
    data_root: Path = DEFAULT_DATA_ROOT,
    catalog_path: Path = DEFAULT_CATALOG,
    seed: int = 42,
    target_cases: int = 120,
    dry_run: bool = False,
    limits: DownloadLimits | None = None,
) -> dict[str, Any]:
    limits = limits or DownloadLimits()
    data_root = data_root.resolve()
    report: dict[str, Any] = {
        "seed_version": SEED_VERSION,
        "seed": seed,
        "target_cases": target_cases,
        "dry_run": dry_run,
        "started_at": datetime.now(UTC).isoformat(),
        "provenance": inspect_sources(),
        "downloads": [],
        "limits": asdict(limits),
    }

    approved = [a for a in SOURCE_AUDITS if a.verdict == "APPROVED_FOR_BENCHMARK"]
    rejected_auto = [a for a in SOURCE_AUDITS if a.verdict != "APPROVED_FOR_BENCHMARK"]
    report["approved_for_auto_download"] = [a.source_name for a in approved]
    report["skipped_not_approved"] = [
        {"source": a.source_name, "verdict": a.verdict, "reason": a.notes}
        for a in rejected_auto
    ]

    if dry_run:
        for a in approved:
            report["downloads"].append(
                {
                    "source": a.source_name,
                    "action": "would_download",
                    "selective": a.selective_download,
                    "estimated_full_bytes": a.estimated_full_bytes,
                    "strategy": a.download_strategy,
                }
            )
        report["status"] = "dry_run_ok"
        report["expected_listing_cases_approx"] = min(
            target_cases, limits.max_total_files
        )
        return report

    data_root.mkdir(parents=True, exist_ok=True)
    images_root = data_root / "images"
    images_root.mkdir(parents=True, exist_ok=True)

    assets = []
    clothing_audit = get_audit("agrigorev_clothing_dataset_small")
    if clothing_audit and clothing_audit.verdict == "APPROVED_FOR_BENCHMARK":
        fetched, stats = download_clothing_small_subset(
            dest_root=data_root,
            limits=limits,
            rng_seed=seed,
            target_cases=target_cases,
            dry_run=False,
        )
        report["downloads"].append(stats)
        assets.extend(fetched)
    else:
        report["downloads"].append({"error": "no approved clothing source"})

    # Enforce bounds even if a source helper returns extra assets.
    assets = assets[
        : min(target_cases, limits.max_total_files, limits.max_per_source_files)
    ]

    catalog = load_catalog(catalog_path)
    manifest_rows: list[dict[str, Any]] = []
    review_rows: list[dict[str, Any]] = []
    download_manifest: list[dict[str, Any]] = []
    seen_hashes: set[str] = set()
    dup_count = 0

    case_i = 0
    for asset in assets:
        mapping = map_clothing_label(asset.source_label)
        if mapping is None:
            review_rows.append(
                {
                    "source_record_id": asset.source_record_id,
                    "source_label": asset.source_label,
                    "reason": "unmapped_label",
                }
            )
            continue
        if mapping.review_required:
            review_rows.append(
                {
                    "source_record_id": asset.source_record_id,
                    "source_label": asset.source_label,
                    "proposed_semantic": mapping.semantic_slug,
                    "reason": "ambiguous_mapping",
                }
            )
            continue

        if asset.content_hash in seen_hashes:
            dup_count += 1
            continue
        seen_hashes.add(asset.content_hash)

        cat = catalog.get_by_slug(mapping.semantic_slug)
        if cat is None:
            review_rows.append(
                {
                    "source_record_id": asset.source_record_id,
                    "reason": "semantic_slug_missing_in_seed_catalog",
                    "slug": mapping.semantic_slug,
                }
            )
            continue

        case_i += 1
        test_id = f"seed_{case_i:04d}"
        # relative to images_root parent (= data_root/images)
        try:
            rel = asset.local_path.relative_to(images_root).as_posix()
        except ValueError:
            rel = asset.local_path.name

        group = f"grp_clothing_{asset.content_hash[:12]}"
        row = {
            "test_id": test_id,
            "images": [rel],
            "ground_truth": {
                "category_id": cat.category_id,
                "category_slug": cat.slug,
                "path": list(mapping.semantic_path),
            },
            "acceptable_alternatives": [],
            "difficulty": _difficulty_for(
                mapping.mapping_confidence, mapping.review_required
            ),
            "tags": [
                "public_seed",
                "clothing",
                mapping.semantic_slug,
                f"src:{asset.source_label}",
            ],
            "notes": (
                f"source=agrigorev_clothing_dataset_small "
                f"label={asset.source_label} "
                f"aivai_match={aivai_match_status(mapping)}"
            ),
            "split": "test",
            "source_group_id": group,
        }
        manifest_rows.append(row)
        download_manifest.append(
            {
                "local_relative_path": rel,
                "source_dataset": "agrigorev_clothing_dataset_small",
                "source_record_id": asset.source_record_id,
                "source_url": clothing_audit.official_url if clothing_audit else None,
                "content_hash": asset.content_hash,
                "retrieved_at": datetime.now(UTC).isoformat(),
                "license_record": "agrigorev_clothing_dataset_small",
                "bytes": asset.bytes_len,
                "test_id": test_id,
                "aivai_match": aivai_match_status(mapping),
            }
        )

    # Write artifacts
    manifest_path = data_root / "manifest.jsonl"
    with manifest_path.open("w", encoding="utf-8") as f:
        for row in manifest_rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    review_path = data_root / "review_required.jsonl"
    with review_path.open("w", encoding="utf-8") as f:
        for row in review_rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    dl_path = data_root / "download_manifest.jsonl"
    with dl_path.open("w", encoding="utf-8") as f:
        for row in download_manifest:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    # Copy frozen catalog into seed dir
    seed_catalog = data_root / "category_catalog.json"
    shutil.copyfile(catalog_path, seed_catalog)

    # Validate via harness
    validation = validate_manifest(
        manifest_path=manifest_path,
        images_root=images_root,
        catalog=load_catalog(seed_catalog),
        split_filter="test",
    )
    if not validation.ok:
        # partial failure — do not write freeze markers as valid
        report["validation"] = {"ok": False, "errors": validation.errors}
        report["status"] = "build_failed_validation"
        (data_root / "build_report.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return report

    d_hash = dataset_hash(manifest_path, seed_catalog)
    c_hash = sha256_file(seed_catalog)
    freeze = {
        "seed_version": SEED_VERSION,
        "frozen_at": datetime.now(UTC).isoformat(),
        "dataset_hash": d_hash,
        "catalog_hash": c_hash,
        "catalog_version": load_catalog(seed_catalog).version,
        "source_versions": {
            "agrigorev_clothing_dataset_small": "github-master@2026-08-25-audit",
        },
        "listing_count": len(manifest_rows),
        "image_count": len(download_manifest),
        "duplicate_hashes_skipped": dup_count,
        "review_required_count": len(review_rows),
        "rng_seed": seed,
    }
    (data_root / "freeze.json").write_text(
        json.dumps(freeze, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    summary = summarize_seed_dir(data_root)
    report["validation"] = {"ok": True, "records": len(validation.records)}
    report["freeze"] = freeze
    report["summary"] = summary
    report["status"] = "frozen"
    (data_root / "build_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (data_root / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return report


def summarize_seed_dir(data_root: Path) -> dict[str, Any]:
    data_root = data_root.resolve()
    manifest_path = data_root / "manifest.jsonl"
    images_root = data_root / "images"
    rows: list[dict[str, Any]] = []
    if manifest_path.is_file():
        for line in manifest_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rows.append(json.loads(line))

    labels = Counter(r["ground_truth"]["category_slug"] for r in rows)
    difficulty = Counter(r.get("difficulty", "medium") for r in rows)
    imgs_per = Counter(len(r.get("images") or []) for r in rows)
    match_counter = Counter()
    for r in rows:
        notes = r.get("notes") or ""
        if f"aivai_match={NO_CURRENT_AIVAI_MATCH}" in notes:
            match_counter[NO_CURRENT_AIVAI_MATCH] += 1
        elif "aivai_match=transport-car-sale" in notes:
            match_counter["transport-car-sale"] += 1
        else:
            match_counter["other_or_unspecified"] += 1

    total_bytes = 0
    image_files = 0
    if images_root.is_dir():
        for p in images_root.rglob("*"):
            if p.is_file() and p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}:
                image_files += 1
                total_bytes += p.stat().st_size

    review_n = 0
    review_path = data_root / "review_required.jsonl"
    if review_path.is_file():
        review_n = sum(1 for line in review_path.read_text(encoding="utf-8").splitlines() if line.strip())

    freeze = {}
    freeze_path = data_root / "freeze.json"
    if freeze_path.is_file():
        freeze = json.loads(freeze_path.read_text(encoding="utf-8"))

    return {
        "seed_version": freeze.get("seed_version", SEED_VERSION),
        "total_listings": len(rows),
        "total_images": image_files,
        "images_per_listing": dict(sorted(imgs_per.items())),
        "source_distribution": {"agrigorev_clothing_dataset_small": len(rows)},
        "semantic_label_distribution": dict(labels),
        "aivai_match_distribution": dict(match_counter),
        "difficulty_distribution": dict(difficulty),
        "review_required_count": review_n,
        "disk_bytes": total_bytes,
        "dataset_hash": freeze.get("dataset_hash"),
        "catalog_hash": freeze.get("catalog_hash"),
    }
