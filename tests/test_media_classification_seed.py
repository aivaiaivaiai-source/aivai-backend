"""Substage 3B-2 — public seed dataset builder tests."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from benchmarks.media_classification.runner.catalog import load_catalog
from benchmarks.media_classification.runner.hashing import dataset_hash
from benchmarks.media_classification.runner.manifest import validate_manifest
from benchmarks.media_classification.seed.build import (
    DEFAULT_CATALOG,
    build_seed,
    inspect_sources,
    summarize_seed_dir,
)
from benchmarks.media_classification.seed.download import (
    DownloadLimits,
    download_clothing_small_subset,
    sha256_bytes,
)
from benchmarks.media_classification.seed.mapping import (
    NO_CURRENT_AIVAI_MATCH,
    aivai_match_status,
    map_clothing_label,
)
from benchmarks.media_classification.seed.provenance import (
    SOURCE_AUDITS,
    get_audit,
)

ROOT = Path(__file__).resolve().parents[1]
GITIGNORE = ROOT / ".gitignore"


def test_unapproved_source_not_auto_downloaded() -> None:
    vehicles = get_audit("aiomarrehan_vehicles_hf")
    assert vehicles is not None
    assert vehicles.verdict == "REVIEW_REQUIRED"
    abo = get_audit("amazon_berkeley_objects_abo")
    assert abo is not None
    assert abo.verdict == "REJECTED"
    info = inspect_sources()
    assert info["counts"]["APPROVED_FOR_BENCHMARK"] >= 1
    assert info["counts"]["REVIEW_REQUIRED"] >= 1
    assert info["counts"]["REJECTED"] >= 1


def test_review_required_source_skipped_in_build_report(tmp_path: Path) -> None:
    report = build_seed(
        data_root=tmp_path / "seed",
        catalog_path=DEFAULT_CATALOG,
        seed=1,
        target_cases=5,
        dry_run=True,
    )
    skipped = {s["source"] for s in report["skipped_not_approved"]}
    assert "aiomarrehan_vehicles_hf" in skipped
    assert "amazon_berkeley_objects_abo" in skipped
    approved = set(report["approved_for_auto_download"])
    assert "agrigorev_clothing_dataset_small" in approved
    assert "aiomarrehan_vehicles_hf" not in approved


def test_download_limits_enforced(tmp_path: Path) -> None:
    limits = DownloadLimits(max_total_bytes=50, max_total_files=2, retries=0)
    tree = {
        "tree": [
            {
                "path": "train/t-shirt/a.jpg",
                "type": "blob",
                "sha": "x",
                "size": 10,
            },
            {
                "path": "train/t-shirt/b.jpg",
                "type": "blob",
                "sha": "y",
                "size": 10,
            },
        ]
    }

    def fake_get(url: str, *, timeout_s: int, retries: int) -> bytes:
        if "git/trees" in url:
            return json.dumps(tree).encode()
        return b"x" * 40  # each file exceeds remaining budget after first

    with patch(
        "benchmarks.media_classification.seed.download.http_get",
        side_effect=fake_get,
    ):
        with pytest.raises(RuntimeError, match="max_total_bytes"):
            download_clothing_small_subset(
                dest_root=tmp_path,
                limits=limits,
                rng_seed=0,
                target_cases=2,
                dry_run=False,
            )


def test_deterministic_sampling_same_seed(tmp_path: Path) -> None:
    from benchmarks.media_classification.seed.download import FetchedAsset

    def fake_assets(seed_root: Path, n: int = 8) -> list[FetchedAsset]:
        out = []
        for i in range(n):
            data = f"img-{i}".encode()
            h = sha256_bytes(data)
            p = (
                seed_root
                / "images"
                / "agrigorev_clothing_small"
                / f"t-shirt_{i}_{h[:10]}.jpg"
            )
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(data)
            out.append(
                FetchedAsset(
                    local_path=p,
                    source_record_id=f"clothing-small:t-shirt:{i}.jpg",
                    source_label="t-shirt",
                    content_hash=h,
                    bytes_len=len(data),
                )
            )
        return out

    def _run(seed_root: Path) -> list[str]:
        assets = fake_assets(seed_root)
        stats = {"source": "agrigorev_clothing_dataset_small", "assets": len(assets)}
        with patch(
            "benchmarks.media_classification.seed.build.download_clothing_small_subset",
            return_value=(assets, stats),
        ):
            report = build_seed(
                data_root=seed_root,
                catalog_path=DEFAULT_CATALOG,
                seed=42,
                target_cases=5,
                dry_run=False,
                limits=DownloadLimits(max_total_files=5),
            )
        assert report["status"] == "frozen"
        man = (seed_root / "manifest.jsonl").read_text(encoding="utf-8")
        return [json.loads(line)["test_id"] for line in man.splitlines() if line.strip()]

    a = _run(tmp_path / "a")
    b = _run(tmp_path / "b")
    assert a == b
    assert len(a) == 5


def test_multi_view_grouping_and_max_nine(tmp_path: Path) -> None:
    images = tmp_path / "images"
    images.mkdir()
    paths = []
    for i in range(3):
        p = images / f"{i:02d}.jpg"
        p.write_bytes(b"\xff\xd8\xff\xd9")
        paths.append(f"{i:02d}.jpg")
    group = "grp_product_abc"
    row = {
        "test_id": "mv1",
        "images": paths,
        "ground_truth": {
            "category_id": 900001,
            "category_slug": "benchmark-apparel",
            "path": ["Benchmark", "Apparel"],
        },
        "difficulty": "easy",
        "split": "test",
        "source_group_id": group,
        "tags": ["multi"],
    }
    man = tmp_path / "manifest.jsonl"
    man.write_text(json.dumps(row) + "\n", encoding="utf-8")
    catalog = load_catalog(DEFAULT_CATALOG)
    result = validate_manifest(
        manifest_path=man, images_root=images, catalog=catalog
    )
    assert result.ok, result.errors
    assert result.records[0].source_group_id == group

    for i in range(10):
        (images / f"x{i}.jpg").write_bytes(b"\xff\xd8\xff\xd9")
    bad = dict(row)
    bad["images"] = [f"x{i}.jpg" for i in range(10)]
    man2 = tmp_path / "m2.jsonl"
    man2.write_text(json.dumps(bad) + "\n", encoding="utf-8")
    bad_result = validate_manifest(
        manifest_path=man2, images_root=images, catalog=catalog
    )
    assert not bad_result.ok


def test_mapping_exact_and_no_match() -> None:
    m = map_clothing_label("t-shirt")
    assert m is not None
    assert m.semantic_slug == "benchmark-apparel"
    assert m.aivai_category_slug is None
    assert aivai_match_status(m) == NO_CURRENT_AIVAI_MATCH
    assert m.mapping_confidence == "exact"
    assert not m.review_required


def test_ambiguous_mapping_review_file(tmp_path: Path) -> None:
    from benchmarks.media_classification.seed.download import FetchedAsset

    seed_root = tmp_path / "seed"
    imgs = seed_root / "images" / "agrigorev_clothing_small"
    imgs.mkdir(parents=True)
    data = b"ambiguous-body"
    h = sha256_bytes(data)
    p = imgs / f"body_1_{h[:10]}.jpg"
    p.write_bytes(data)
    # include one valid + one ambiguous so freeze can succeed
    data2 = b"valid-shirt"
    h2 = sha256_bytes(data2)
    p2 = imgs / f"shirt_1_{h2[:10]}.jpg"
    p2.write_bytes(data2)
    assets = [
        FetchedAsset(
            local_path=p,
            source_record_id="clothing-small:body:1.jpg",
            source_label="body",
            content_hash=h,
            bytes_len=len(data),
        ),
        FetchedAsset(
            local_path=p2,
            source_record_id="clothing-small:shirt:1.jpg",
            source_label="shirt",
            content_hash=h2,
            bytes_len=len(data2),
        ),
    ]
    with patch(
        "benchmarks.media_classification.seed.build.download_clothing_small_subset",
        return_value=(assets, {"assets": 2}),
    ):
        report = build_seed(
            data_root=seed_root,
            catalog_path=DEFAULT_CATALOG,
            seed=7,
            target_cases=2,
            dry_run=False,
        )
    review = (seed_root / "review_required.jsonl").read_text(encoding="utf-8")
    assert "ambiguous_mapping" in review
    assert report["status"] == "frozen"
    assert report["freeze"]["listing_count"] == 1
    assert report["freeze"]["review_required_count"] >= 1


def test_duplicate_hash_skipped(tmp_path: Path) -> None:
    from benchmarks.media_classification.seed.download import FetchedAsset

    seed_root = tmp_path / "seed"
    data = b"same-bytes"
    h = sha256_bytes(data)
    imgs = seed_root / "images" / "agrigorev_clothing_small"
    imgs.mkdir(parents=True)
    assets = []
    for i in range(2):
        p = imgs / f"t-shirt_{i}_{h[:10]}.jpg"
        p.write_bytes(data)
        assets.append(
            FetchedAsset(
                local_path=p,
                source_record_id=f"clothing-small:t-shirt:{i}.jpg",
                source_label="t-shirt",
                content_hash=h,
                bytes_len=len(data),
            )
        )
    with patch(
        "benchmarks.media_classification.seed.build.download_clothing_small_subset",
        return_value=(assets, {"assets": 2}),
    ):
        report = build_seed(
            data_root=seed_root,
            catalog_path=DEFAULT_CATALOG,
            seed=3,
            target_cases=2,
            dry_run=False,
        )
    assert report["status"] == "frozen"
    assert report["freeze"]["listing_count"] == 1
    assert report["freeze"]["duplicate_hashes_skipped"] == 1


def test_source_provenance_fields() -> None:
    clothing = get_audit("agrigorev_clothing_dataset_small")
    assert clothing is not None
    assert clothing.dataset_license.startswith("CC0")
    assert clothing.verdict == "APPROVED_FOR_BENCHMARK"
    for field in (
        "source_name",
        "official_url",
        "upstream_source",
        "dataset_license",
        "image_content_license",
        "commercial_use",
        "redistribution",
        "derivative_use",
        "provenance_quality",
        "checked_at",
        "verdict",
        "notes",
    ):
        assert hasattr(clothing, field)


def test_partial_download_not_frozen(tmp_path: Path) -> None:
    with patch(
        "benchmarks.media_classification.seed.build.download_clothing_small_subset",
        side_effect=RuntimeError("network boom"),
    ):
        with pytest.raises(RuntimeError, match="network boom"):
            build_seed(
                data_root=tmp_path / "seed",
                catalog_path=DEFAULT_CATALOG,
                seed=1,
                target_cases=5,
                dry_run=False,
            )
    assert not (tmp_path / "seed" / "freeze.json").exists()


def test_dry_run_no_network_write(tmp_path: Path) -> None:
    with patch(
        "benchmarks.media_classification.seed.download.http_get"
    ) as http_get:
        report = build_seed(
            data_root=tmp_path / "seed",
            catalog_path=DEFAULT_CATALOG,
            seed=1,
            target_cases=10,
            dry_run=True,
        )
        http_get.assert_not_called()
    assert report["status"] == "dry_run_ok"
    assert not any((tmp_path / "seed").rglob("*.jpg")) if (tmp_path / "seed").exists() else True


def test_frozen_dataset_hash_stable(tmp_path: Path) -> None:
    from benchmarks.media_classification.seed.download import FetchedAsset

    def _freeze(root: Path) -> str:
        data = b"hash-stable"
        h = sha256_bytes(data)
        p = root / "images" / "agrigorev_clothing_small" / f"shoes_0_{h[:10]}.jpg"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
        assets = [
            FetchedAsset(
                local_path=p,
                source_record_id="clothing-small:shoes:0.jpg",
                source_label="shoes",
                content_hash=h,
                bytes_len=len(data),
            )
        ]
        with patch(
            "benchmarks.media_classification.seed.build.download_clothing_small_subset",
            return_value=(assets, {"assets": 1}),
        ):
            report = build_seed(
                data_root=root,
                catalog_path=DEFAULT_CATALOG,
                seed=11,
                target_cases=1,
                dry_run=False,
            )
        assert report["status"] == "frozen"
        return report["freeze"]["dataset_hash"]

    h1 = _freeze(tmp_path / "s1")
    h2 = _freeze(tmp_path / "s2")
    assert h1 == h2
    man = tmp_path / "s1" / "manifest.jsonl"
    cat = tmp_path / "s1" / "category_catalog.json"
    assert dataset_hash(man, cat) == h1


def test_downloaded_images_ignored_by_git() -> None:
    text = GITIGNORE.read_text(encoding="utf-8")
    assert "benchmarks/media_classification/data/" in text


def test_validator_accepts_valid_seed_fixture(tmp_path: Path) -> None:
    from benchmarks.media_classification.seed.download import FetchedAsset

    root = tmp_path / "seed"
    data = b"\xff\xd8\xff\xd9valid"
    h = sha256_bytes(data)
    p = root / "images" / "agrigorev_clothing_small" / f"pants_0_{h[:10]}.jpg"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(data)
    assets = [
        FetchedAsset(
            local_path=p,
            source_record_id="clothing-small:pants:0.jpg",
            source_label="pants",
            content_hash=h,
            bytes_len=len(data),
        )
    ]
    with patch(
        "benchmarks.media_classification.seed.build.download_clothing_small_subset",
        return_value=(assets, {"assets": 1}),
    ):
        report = build_seed(
            data_root=root,
            catalog_path=DEFAULT_CATALOG,
            seed=5,
            target_cases=1,
            dry_run=False,
        )
    assert report["status"] == "frozen"
    result = validate_manifest(
        manifest_path=root / "manifest.jsonl",
        images_root=root / "images",
        catalog=load_catalog(root / "category_catalog.json"),
    )
    assert result.ok, result.errors
    summary = summarize_seed_dir(root)
    assert summary["total_listings"] == 1
    assert summary["aivai_match_distribution"].get(NO_CURRENT_AIVAI_MATCH) == 1


def test_rejected_source_in_registry() -> None:
    names = {a.source_name for a in SOURCE_AUDITS}
    assert "amazon_berkeley_objects_abo" in names
