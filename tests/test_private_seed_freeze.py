"""Tests for private seed freeze (3B-2P4)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from PIL import Image

from benchmarks.media_classification.private_seed import (
    LABEL_TAXONOMY,
    build_inventory,
    sha256_file,
    write_blank_labels_csv,
    write_inventory,
)
from benchmarks.media_classification.private_seed.freeze import (
    DEFAULT_CATALOG,
    freeze_private_seed,
    is_frozen,
    metric_status_for_support,
    pre_freeze_integrity,
)
from benchmarks.media_classification.private_seed.labeling import (
    LabelingSession,
    assert_writable_private_seed,
    reset_human_labels,
)
from benchmarks.media_classification.runner.catalog import load_catalog
from benchmarks.media_classification.runner.manifest import validate_manifest


def _make_jpeg(path: Path, *, color=(10, 20, 30)) -> None:
    Image.new("RGB", (320, 240), color).save(path, format="JPEG", quality=85)


def _setup_labeled(tmp_path: Path, n: int = 11) -> Path:
    root = tmp_path / "aivai_private_seed_v1"
    raw = root / "raw"
    review = root / "review"
    raw.mkdir(parents=True)
    review.mkdir()
    for i in range(n):
        _make_jpeg(raw / f"shot_{i:03d}.jpg", color=(i * 20 % 255, 40, 40))
    inv = build_inventory(raw)
    write_inventory(inv, review / "inventory.json")
    write_blank_labels_csv(inv, review / "labels_to_review.csv")
    session = LabelingSession.open(root, expected_count=n)
    # cycle through taxonomy so distribution is non-trivial; allow OTHER=0 by skipping OTHER
    labels = [l for l in LABEL_TAXONOMY if l != "OTHER"]
    for i, pid in enumerate(session.ordered_ids):
        session.apply_label(pid, labels[i % len(labels)])
    return root


def test_reviewed_required_for_freeze(tmp_path: Path) -> None:
    root = tmp_path / "aivai_private_seed_v1"
    raw = root / "raw"
    review = root / "review"
    raw.mkdir(parents=True)
    review.mkdir()
    for i in range(5):
        _make_jpeg(raw / f"s_{i}.jpg")
    inv = build_inventory(raw)
    write_inventory(inv, review / "inventory.json")
    write_blank_labels_csv(inv, review / "labels_to_review.csv")
    with pytest.raises(RuntimeError, match="pre-freeze integrity failed"):
        freeze_private_seed(
            private_root=root, catalog_path=DEFAULT_CATALOG, expected_count=5
        )


def test_invalid_label_blocks_freeze(tmp_path: Path) -> None:
    root = _setup_labeled(tmp_path, n=5)
    # corrupt a label to invalid enum while keeping reviewed=true via direct CSV edit
    import csv

    path = root / "review" / "labels_to_review.csv"
    rows = list(csv.DictReader(path.open(encoding="utf-8")))
    rows[0]["label"] = "NOT_A_REAL_CLASS"
    rows[0]["reviewed"] = "true"
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "private_id",
                "label",
                "listing_group",
                "difficulty",
                "notes",
                "reviewed",
            ],
        )
        w.writeheader()
        w.writerows(rows)
    with pytest.raises(RuntimeError):
        freeze_private_seed(
            private_root=root, catalog_path=DEFAULT_CATALOG, expected_count=5
        )


def test_raw_hash_mismatch_blocks_freeze(tmp_path: Path) -> None:
    root = _setup_labeled(tmp_path, n=5)
    p = next((root / "raw").glob("*.jpg"))
    p.write_bytes(b"corrupted-bytes")
    with pytest.raises(RuntimeError, match="hash mismatch"):
        freeze_private_seed(
            private_root=root, catalog_path=DEFAULT_CATALOG, expected_count=5
        )


def test_freeze_creates_version_and_manifest(tmp_path: Path) -> None:
    root = _setup_labeled(tmp_path, n=11)
    before = {p.name: sha256_file(p) for p in (root / "raw").iterdir()}
    result = freeze_private_seed(
        private_root=root, catalog_path=DEFAULT_CATALOG, expected_count=11
    )
    assert result["status"] == "FROZEN"
    assert result["dataset_version"] == "aivai-private-seed-v1"
    assert result["case_count"] == 11
    assert is_frozen(root)
    assert (root / "manifest.jsonl").is_file()
    assert (root / "freeze.json").is_file()
    assert (root / "FROZEN").is_file()
    assert (root / "metric_support.json").is_file()
    freeze = json.loads((root / "freeze.json").read_text(encoding="utf-8"))
    assert freeze["unclear_metric_policy"]["exclude_from_primary_top1_denominator"] is True
    assert any("single-image" in x for x in freeze["limitations"])
    assert freeze["models_api_ocr_used_at_freeze"] is False
    assert result["manifest_hash"]
    assert result["raw_aggregate_hash"]
    assert result["labels_hash"]
    assert result["inventory_hash"]
    # OTHER=0 allowed
    assert result["label_counts"].get("OTHER", 0) == 0
    man_lines = [
        ln
        for ln in (root / "manifest.jsonl").read_text(encoding="utf-8").splitlines()
        if ln.strip()
    ]
    assert len(man_lines) == 11
    # distribution preserved
    from collections import Counter

    slugs = Counter(json.loads(ln)["ground_truth"]["category_slug"] for ln in man_lines)
    assert dict(slugs) == {k: v for k, v in result["label_counts"].items() if v > 0}
    # harness validate
    v = validate_manifest(
        manifest_path=root / "manifest.jsonl",
        images_root=root / "raw",
        catalog=load_catalog(root / "category_catalog.json"),
    )
    assert v.ok, v.errors
    assert {p.name: sha256_file(p) for p in (root / "raw").iterdir()} == before


def test_second_freeze_refuses_without_force(tmp_path: Path) -> None:
    root = _setup_labeled(tmp_path, n=11)
    freeze_private_seed(
        private_root=root, catalog_path=DEFAULT_CATALOG, expected_count=11
    )
    with pytest.raises(RuntimeError, match="refuse silent overwrite"):
        freeze_private_seed(
            private_root=root, catalog_path=DEFAULT_CATALOG, expected_count=11
        )


def test_label_helper_refuses_frozen(tmp_path: Path) -> None:
    root = _setup_labeled(tmp_path, n=11)
    freeze_private_seed(
        private_root=root, catalog_path=DEFAULT_CATALOG, expected_count=11
    )
    with pytest.raises(RuntimeError, match="FROZEN"):
        assert_writable_private_seed(root)
    session = LabelingSession.open(root, expected_count=11)
    with pytest.raises(RuntimeError, match="FROZEN"):
        session.apply_label("P001", "CAR_SALE")
    with pytest.raises(RuntimeError, match="FROZEN"):
        reset_human_labels(private_root=root)


def test_metric_status_helpers() -> None:
    assert metric_status_for_support(0) == "UNSUPPORTED"
    assert metric_status_for_support(1) == "INSUFFICIENT"
    assert metric_status_for_support(4) == "LOW_SUPPORT"
    assert metric_status_for_support(10) == "OK"


def test_private_freeze_artifacts_gitignored() -> None:
    repo = Path(__file__).resolve().parents[1]
    text = (repo / ".gitignore").read_text(encoding="utf-8")
    assert "benchmarks/media_classification/data/" in text
