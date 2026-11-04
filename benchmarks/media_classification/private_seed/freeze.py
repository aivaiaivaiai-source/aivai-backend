"""Freeze aivai-private-seed-v1 after complete human ground truth (3B-2P4).

No model inference. No label mutation. Human labels are ground truth.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from benchmarks.media_classification.private_seed import LABEL_TAXONOMY, sha256_file
from benchmarks.media_classification.private_seed.labeling import (
    LABEL_HINTS_RU,
    LABEL_RU,
    load_and_validate_dataset,
)
from benchmarks.media_classification.runner.catalog import load_catalog
from benchmarks.media_classification.runner.hashing import dataset_hash
from benchmarks.media_classification.runner.manifest import validate_manifest

DATASET_VERSION = "aivai-private-seed-v1"
TAXONOMY_VERSION = "private-11-class-v1"
PACKAGE_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CATALOG = PACKAGE_ROOT / "catalog" / "private_seed_v1_catalog.json"
DEFAULT_PRIVATE = PACKAGE_ROOT / "data" / "aivai_private_seed_v1"

UNCLEAR_METRIC_POLICY = {
    "exclude_from_primary_top1_denominator": True,
    "keep_in_predictions_and_hard_case_report": True,
    "do_not_award_or_penalize_without_explicit_policy": True,
    "notes": (
        "UNCLEAR is not a normal leaf accuracy target. "
        "Primary Top-1 accuracy may exclude UNCLEAR cases from the denominator; "
        "cases must still appear in predictions/hard-case reporting."
    ),
}

PURPOSE = {
    "classification": "AIVAI PRIVATE INTERNAL EVALUATION / SMOKE BENCHMARK",
    "intended_for": [
        "first local Vision benchmark",
        "confusion analysis",
        "false-high-confidence analysis",
        "candidate model comparison",
        "car vs parts vs other transport vs real estate checks",
    ],
    "not": [
        "training dataset",
        "production accuracy certification",
        "statistically representative Kyrgyzstan marketplace dataset",
    ],
}

LIMITATIONS = [
    "v1 primarily measures single-image classification capability.",
    "Multi-photo listing grouping was not performed.",
    "OTHER has zero support in v1; per-class metrics for OTHER are not meaningful.",
    "Several classes have low/insufficient support for stable per-class metrics.",
]


def is_frozen(private_root: Path) -> bool:
    root = private_root.resolve()
    return (root / "freeze.json").is_file() and (root / "FROZEN").is_file()


def metric_status_for_support(support: int) -> str:
    if support <= 0:
        return "UNSUPPORTED"
    if support <= 3:
        return "INSUFFICIENT"
    if support <= 9:
        return "LOW_SUPPORT"
    return "OK"


def build_support_table(counts: dict[str, int]) -> list[dict[str, Any]]:
    rows = []
    for label in LABEL_TAXONOMY:
        support = int(counts.get(label, 0))
        rows.append(
            {
                "class": label,
                "support": support,
                "metric_status": metric_status_for_support(support),
            }
        )
    return rows


def pre_freeze_integrity(
    private_root: Path, *, expected_count: int = 132, allow_existing_freeze: bool = False
) -> dict[str, Any]:
    """Validate readiness for freeze. Raises RuntimeError on failure."""
    private_root = private_root.resolve()
    errors: list[str] = []

    if is_frozen(private_root) and not allow_existing_freeze:
        errors.append("dataset already frozen")

    try:
        bundle = load_and_validate_dataset(private_root, expected_count=expected_count)
    except RuntimeError as exc:
        raise RuntimeError(f"pre-freeze integrity failed:\n{exc}") from exc

    reviewed = [r for r in bundle.labels if r.reviewed]
    if len(reviewed) != expected_count:
        errors.append(f"reviewed={len(reviewed)} != {expected_count}")

    empty_labels = [r.private_id for r in reviewed if not r.label]
    if empty_labels:
        errors.append(f"empty labels: {empty_labels[:5]}")

    invalid = [
        r.private_id for r in reviewed if r.label and r.label not in LABEL_TAXONOMY
    ]
    if invalid:
        errors.append(f"invalid labels: {invalid[:5]}")

    # bytes consistency with inventory
    inv_bytes = sum(i.bytes for i in bundle.inventory)
    raw_bytes = sum(p.stat().st_size for p in bundle.raw_paths.values())
    if inv_bytes != raw_bytes:
        errors.append(f"byte mismatch inventory={inv_bytes} raw={raw_bytes}")

    if errors:
        raise RuntimeError("pre-freeze integrity failed:\n  - " + "\n  - ".join(errors))

    counts = Counter(r.label for r in reviewed)
    return {
        "ok": True,
        "case_count": expected_count,
        "reviewed": len(reviewed),
        "label_counts": {k: counts.get(k, 0) for k in LABEL_TAXONOMY},
        "raw_bytes": raw_bytes,
        "inventory_bytes": inv_bytes,
        "bundle": bundle,
    }


def _raw_aggregate_hash(inventory_rows, raw_paths: dict[str, Path]) -> str:
    """Deterministic aggregate over inventory order: id + filename + content hash."""
    h = hashlib.sha256()
    for item in inventory_rows:
        path = raw_paths[item.private_id]
        digest = sha256_file(path)
        h.update(item.private_id.encode("utf-8"))
        h.update(b"\0")
        h.update(item.original_filename.encode("utf-8"))
        h.update(b"\0")
        h.update(digest.encode("utf-8"))
        h.update(b"\n")
    return h.hexdigest()


def build_frozen_manifest(
    *,
    inventory,
    labels_by_id: dict,
    catalog,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in inventory:
        lr = labels_by_id[item.private_id]
        cat = catalog.get_by_slug(lr.label)
        if cat is None:
            raise RuntimeError(f"label {lr.label} missing from private catalog")
        difficulty = "ambiguous" if lr.label == "UNCLEAR" else "medium"
        rows.append(
            {
                "test_id": item.private_id,
                "images": [item.original_filename],
                "ground_truth": {
                    "category_id": cat.category_id,
                    "category_slug": cat.slug,
                    "path": [cat.name],
                },
                "acceptable_alternatives": [],
                "difficulty": difficulty,
                "tags": [
                    "private_seed",
                    "image_level",
                    "human_gt",
                    lr.label,
                    TAXONOMY_VERSION,
                ],
                "notes": (
                    f"taxonomy={TAXONOMY_VERSION}; "
                    f"image_level_v1; human_label={lr.label}"
                ),
                "split": "test",
                "source_group_id": f"grp_{item.private_id}",
            }
        )
    return rows


def freeze_private_seed(
    *,
    private_root: Path = DEFAULT_PRIVATE,
    catalog_path: Path = DEFAULT_CATALOG,
    expected_count: int = 132,
    force: bool = False,
) -> dict[str, Any]:
    private_root = private_root.resolve()
    catalog_path = catalog_path.resolve()

    if (private_root / "freeze.json").exists() and not force:
        raise RuntimeError(
            "dataset already has freeze.json — refuse silent overwrite "
            "(use force=True / --force only intentionally)"
        )

    integrity = pre_freeze_integrity(
        private_root,
        expected_count=expected_count,
        allow_existing_freeze=force,
    )
    bundle = integrity["bundle"]
    counts = integrity["label_counts"]
    support_table = build_support_table(counts)

    catalog = load_catalog(catalog_path)
    labels_by_id = {r.private_id: r for r in bundle.labels}
    manifest_rows = build_frozen_manifest(
        inventory=bundle.inventory,
        labels_by_id=labels_by_id,
        catalog=catalog,
    )

    # Write frozen catalog copy + manifest
    frozen_catalog = private_root / "category_catalog.json"
    shutil.copyfile(catalog_path, frozen_catalog)

    manifest_path = private_root / "manifest.jsonl"
    with manifest_path.open("w", encoding="utf-8") as f:
        for row in manifest_rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    # Harness validation (no classifier)
    validation = validate_manifest(
        manifest_path=manifest_path,
        images_root=bundle.raw_dir,
        catalog=load_catalog(frozen_catalog),
        split_filter="test",
    )
    if not validation.ok:
        # Clean partial freeze artifacts on failure
        for p in (manifest_path, frozen_catalog):
            if p.exists():
                p.unlink()
        raise RuntimeError(
            "harness validation failed:\n  - " + "\n  - ".join(validation.errors[:20])
        )

    inventory_hash = sha256_file(bundle.inventory_path)
    labels_hash = sha256_file(bundle.labels_path)
    catalog_hash = sha256_file(frozen_catalog)
    manifest_hash = sha256_file(manifest_path)
    raw_agg = _raw_aggregate_hash(bundle.inventory, bundle.raw_paths)
    ds_hash = dataset_hash(manifest_path, frozen_catalog)

    support_path = private_root / "metric_support.json"
    support_payload = {
        "dataset_version": DATASET_VERSION,
        "classes": support_table,
        "notes": [
            "OTHER has zero support in v1; per-class metrics for OTHER are not meaningful.",
            "Low/insufficient support classes should be treated cautiously in reports.",
        ],
    }
    support_path.write_text(
        json.dumps(support_payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    definitions = {
        label: {
            "name_ru": LABEL_RU[label],
            "hint_ru": next(
                (h for h in LABEL_HINTS_RU if LABEL_RU[label] in h or label in h),
                LABEL_RU[label],
            ),
        }
        for label in LABEL_TAXONOMY
    }
    # Attach full hints by index order
    for i, label in enumerate(LABEL_TAXONOMY):
        definitions[label]["definition_ru"] = LABEL_HINTS_RU[i]

    freeze = {
        "status": "FROZEN",
        "dataset_version": DATASET_VERSION,
        "taxonomy_version": TAXONOMY_VERSION,
        "frozen_at": datetime.now(UTC).isoformat(),
        "purpose": PURPOSE,
        "limitations": LIMITATIONS,
        "unclear_metric_policy": UNCLEAR_METRIC_POLICY,
        "label_definitions": definitions,
        "case_count": expected_count,
        "image_count": expected_count,
        "label_counts": counts,
        "metric_support": support_table,
        "raw_aggregate_hash": raw_agg,
        "raw_total_bytes": integrity["raw_bytes"],
        "inventory_hash": inventory_hash,
        "labels_hash": labels_hash,
        "catalog_hash": catalog_hash,
        "manifest_hash": manifest_hash,
        "dataset_hash": ds_hash,
        "images_root_relative": "raw",
        "manifest_relative": "manifest.jsonl",
        "catalog_relative": "category_catalog.json",
        "immutability": {
            "rule": "Do not silently mutate v1; create aivai-private-seed-v2 for changes.",
            "label_helper": "refuses writes when FROZEN marker present",
        },
        "models_api_ocr_used_at_freeze": False,
    }

    freeze_path = private_root / "freeze.json"
    freeze_path.write_text(
        json.dumps(freeze, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (private_root / "FROZEN").write_text(
        f"{DATASET_VERSION}\nfrozen_at={freeze['frozen_at']}\n",
        encoding="utf-8",
    )

    return {
        "status": "FROZEN",
        "dataset_version": DATASET_VERSION,
        "case_count": expected_count,
        "label_counts": counts,
        "raw_aggregate_hash": freeze["raw_aggregate_hash"],
        "manifest_hash": freeze["manifest_hash"],
        "labels_hash": freeze["labels_hash"],
        "inventory_hash": freeze["inventory_hash"],
        "catalog_hash": freeze["catalog_hash"],
        "dataset_hash": freeze["dataset_hash"],
        "validation_records": len(validation.records),
        "metric_support": support_table,
        "frozen_at": freeze["frozen_at"],
    }
