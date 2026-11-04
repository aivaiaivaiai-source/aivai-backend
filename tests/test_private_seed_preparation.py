"""Tests for private seed ground-truth preparation (3B-2P)."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from PIL import Image

from benchmarks.media_classification.private_seed import (
    assign_stable_ids,
    build_inventory,
    create_contact_sheets,
    jpeg_has_exif,
    list_raw_images,
    move_screens_to_private_raw,
    prepare_private_seed_review,
    sha256_file,
    write_blank_labels_csv,
)


def _make_jpeg(path: Path, *, size: tuple[int, int] = (400, 300), color=(10, 20, 30)) -> None:
    Image.new("RGB", size, color).save(path, format="JPEG", quality=90)


def test_stable_id_assignment(tmp_path: Path) -> None:
    names = ["b_shot.jpg", "A_shot.jpg", "c_shot.jpg"]
    for n in names:
        _make_jpeg(tmp_path / n)
    files = list_raw_images(tmp_path)
    ids = assign_stable_ids(files)
    assert [i for i, _ in ids] == ["P001", "P002", "P003"]
    # casefold sort: A_shot, b_shot, c_shot
    assert [p.name for _, p in ids] == ["A_shot.jpg", "b_shot.jpg", "c_shot.jpg"]


def test_unique_mapping_entries(tmp_path: Path) -> None:
    for i in range(5):
        _make_jpeg(tmp_path / f"img_{i:02d}.jpg", color=(i * 40, 0, 0))
    rows = build_inventory(tmp_path)
    assert len(rows) == 5
    assert len({r.private_id for r in rows}) == 5
    assert len({r.sha256 for r in rows}) == 5


def test_raw_hash_preservation_on_move(tmp_path: Path) -> None:
    src = tmp_path / "скрины"
    src.mkdir()
    for i in range(3):
        _make_jpeg(src / f"shot_{i}.jpg")
    before = {p.name: sha256_file(p) for p in src.iterdir()}
    dst = tmp_path / "aivai_private_seed_v1" / "raw"
    result = move_screens_to_private_raw(src_dir=src, dst_raw=dst)
    assert result["moved"] == 3
    assert not src.exists()
    after = {p.name: sha256_file(p) for p in dst.iterdir()}
    assert before == after


def test_contact_sheet_coverage(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    raw.mkdir()
    for i in range(30):
        _make_jpeg(raw / f"x_{i:03d}.jpg", size=(500, 800), color=(i, 50, 50))
    inv = build_inventory(raw)
    review = tmp_path / "review"
    sheets = create_contact_sheets(raw_dir=raw, inventory=inv, out_dir=review, tiles_per_sheet=24)
    assert len(sheets) == 2
    assert [r.private_id for r in inv] == [f"P{i:03d}" for i in range(1, 31)]
    # each sheet is EXIF-free derivative
    for s in sheets:
        assert not jpeg_has_exif(s)


def test_blank_labels(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    raw.mkdir()
    for i in range(4):
        _make_jpeg(raw / f"n_{i}.jpg")
    inv = build_inventory(raw)
    csv_path = tmp_path / "labels_to_review.csv"
    write_blank_labels_csv(inv, csv_path)
    with csv_path.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 4
    assert all(r["label"] == "" for r in rows)
    assert all(r["reviewed"] == "false" for r in rows)
    assert len({r["private_id"] for r in rows}) == 4


def test_prepare_full_and_no_duplicate_ids(tmp_path: Path) -> None:
    root = tmp_path / "aivai_private_seed_v1"
    raw = root / "raw"
    raw.mkdir(parents=True)
    for i in range(6):
        _make_jpeg(raw / f"file_{i}.jpg")
    status = prepare_private_seed_review(private_root=root)
    assert status["status"] == "LABELING_PENDING"
    assert status["auto_labels"] is False
    assert len(status["private_ids"]) == len(set(status["private_ids"])) == 6
    inv = json.loads((root / "review" / "inventory.json").read_text(encoding="utf-8"))
    assert inv["count"] == 6


def test_private_data_gitignored() -> None:
    repo = Path(__file__).resolve().parents[1]
    text = (repo / ".gitignore").read_text(encoding="utf-8")
    assert "benchmarks/media_classification/data/" in text
