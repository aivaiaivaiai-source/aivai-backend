"""Tests for private seed human labeling helper (3B-2P3 — 11-class taxonomy)."""

from __future__ import annotations

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
from benchmarks.media_classification.private_seed.labeling import (
    KEY_TO_LABEL,
    LabelRow,
    LabelingSession,
    first_unreviewed_index,
    load_and_validate_dataset,
    load_labels_csv,
    reset_human_labels,
    save_labels_csv,
)


def _make_jpeg(path: Path, *, color=(10, 20, 30)) -> None:
    Image.new("RGB", (400, 300), color).save(path, format="JPEG", quality=90)


def _setup_private_root(tmp_path: Path, n: int = 5) -> Path:
    root = tmp_path / "aivai_private_seed_v1"
    raw = root / "raw"
    review = root / "review"
    raw.mkdir(parents=True)
    review.mkdir()
    for i in range(n):
        _make_jpeg(raw / f"shot_{i:03d}.jpg", color=(i * 30, 0, 0))
    inv = build_inventory(raw)
    write_inventory(inv, review / "inventory.json")
    write_blank_labels_csv(inv, review / "labels_to_review.csv")
    return root


def test_loads_inventory_rows(tmp_path: Path) -> None:
    root = _setup_private_root(tmp_path, n=5)
    bundle = load_and_validate_dataset(root, expected_count=5)
    assert len(bundle.inventory) == 5
    assert len(bundle.labels) == 5


def test_refuse_on_id_mismatch(tmp_path: Path) -> None:
    root = _setup_private_root(tmp_path, n=3)
    csv_path = root / "review" / "labels_to_review.csv"
    rows = load_labels_csv(csv_path)
    rows[0] = LabelRow(
        private_id="P999",
        label="",
        listing_group="",
        difficulty="",
        notes="",
        reviewed=False,
    )
    save_labels_csv(csv_path, rows)
    with pytest.raises(RuntimeError, match="validation failed"):
        load_and_validate_dataset(root, expected_count=3)


def test_refuse_on_hash_mismatch(tmp_path: Path) -> None:
    root = _setup_private_root(tmp_path, n=2)
    raw = root / "raw"
    p = next(raw.glob("*.jpg"))
    p.write_bytes(b"corrupted")
    with pytest.raises(RuntimeError, match="hash mismatch"):
        load_and_validate_dataset(root, expected_count=2)


@pytest.mark.parametrize(
    ("key", "expected"),
    [
        ("1", "CAR_SALE"),
        ("2", "AUTO_PARTS"),
        ("3", "TRUCK_TRANSPORT"),
        ("4", "SPECIAL_MACHINERY"),
        ("5", "MOTORCYCLES"),
        ("6", "WATER_TRANSPORT"),
        ("7", "BUSES"),
        ("8", "COMMERCIAL_TRANSPORT"),
        ("9", "REAL_ESTATE"),
        ("0", "OTHER"),
        ("X", "UNCLEAR"),
        ("x", "UNCLEAR"),
    ],
)
def test_key_to_label_mapping(key: str, expected: str) -> None:
    assert KEY_TO_LABEL[key] == expected


def test_taxonomy_has_eleven_classes() -> None:
    assert len(LABEL_TAXONOMY) == 11
    assert "TRUCK_TRANSPORT" in LABEL_TAXONOMY
    assert "SPECIAL_MACHINERY" in LABEL_TAXONOMY


def test_apply_label_sets_reviewed_and_autosave(tmp_path: Path) -> None:
    root = _setup_private_root(tmp_path, n=3)
    session = LabelingSession.open(root, expected_count=3)
    session.apply_label("P001", "CAR_SALE")
    reloaded = load_labels_csv(root / "review" / "labels_to_review.csv")
    row = next(r for r in reloaded if r.private_id == "P001")
    assert row.label == "CAR_SALE"
    assert row.reviewed is True


def test_resume_first_unreviewed(tmp_path: Path) -> None:
    root = _setup_private_root(tmp_path, n=4)
    session = LabelingSession.open(root, expected_count=4)
    session.apply_label("P001", "OTHER")
    session.apply_label("P002", "UNCLEAR")
    session2 = LabelingSession.open(root, expected_count=4)
    assert session2.current_id == "P003"
    assert first_unreviewed_index(session2.ordered_ids, session2.labels_by_id) == 2


def test_relabel_existing_item(tmp_path: Path) -> None:
    root = _setup_private_root(tmp_path, n=3)
    session = LabelingSession.open(root, expected_count=3)
    session.apply_label("P001", "AUTO_PARTS")
    session.current_index = 0
    session.relabel_current("TRUCK_TRANSPORT")
    row = session.labels_by_id["P001"]
    assert row.label == "TRUCK_TRANSPORT"
    assert row.reviewed is True


def test_undo_session_action(tmp_path: Path) -> None:
    root = _setup_private_root(tmp_path, n=3)
    session = LabelingSession.open(root, expected_count=3)
    session.apply_label("P001", "OTHER")
    assert session.undo_last() is True
    row = session.labels_by_id["P001"]
    assert row.label == ""
    assert row.reviewed is False
    reloaded = load_labels_csv(root / "review" / "labels_to_review.csv")
    assert not next(r for r in reloaded if r.private_id == "P001").reviewed


def test_completion_detection(tmp_path: Path) -> None:
    root = _setup_private_root(tmp_path, n=2)
    session = LabelingSession.open(root, expected_count=2)
    session.apply_label("P001", "OTHER")
    assert not session.progress()["complete"]
    session.apply_label("P002", "UNCLEAR")
    assert session.progress()["complete"]
    assert session.progress()["counts"]["OTHER"] == 1
    assert session.progress()["counts"]["UNCLEAR"] == 1


def test_progress_counts_eleven_classes(tmp_path: Path) -> None:
    root = _setup_private_root(tmp_path, n=5)
    session = LabelingSession.open(root, expected_count=5)
    session.apply_label("P001", "CAR_SALE")
    session.apply_label("P002", "SPECIAL_MACHINERY")
    session.apply_label("P003", "REAL_ESTATE")
    prog = session.progress()
    assert prog["reviewed"] == 3
    assert prog["remaining"] == 2
    assert len(prog["counts"]) == 11
    assert prog["counts"]["CAR_SALE"] == 1
    assert prog["counts"]["SPECIAL_MACHINERY"] == 1
    assert prog["counts"]["REAL_ESTATE"] == 1


def test_raw_hash_unchanged_after_labeling(tmp_path: Path) -> None:
    root = _setup_private_root(tmp_path, n=2)
    raw = root / "raw"
    before = {p.name: sha256_file(p) for p in raw.iterdir()}
    session = LabelingSession.open(root, expected_count=2)
    session.apply_label("P001", "OTHER")
    after = {p.name: sha256_file(p) for p in raw.iterdir()}
    assert before == after


def test_private_label_file_gitignored() -> None:
    repo = Path(__file__).resolve().parents[1]
    text = (repo / ".gitignore").read_text(encoding="utf-8")
    assert "benchmarks/media_classification/data/" in text


def test_label_and_advance(tmp_path: Path) -> None:
    root = _setup_private_root(tmp_path, n=3)
    session = LabelingSession.open(root, expected_count=3)
    assert session.current_id == "P001"
    done = session.label_current_and_advance("CAR_SALE")
    assert not done
    assert session.current_id == "P002"
    session.label_current_and_advance("MOTORCYCLES")
    done = session.label_current_and_advance("UNCLEAR")
    assert done


def test_navigation_does_not_change_label(tmp_path: Path) -> None:
    root = _setup_private_root(tmp_path, n=3)
    session = LabelingSession.open(root, expected_count=3)
    session.go_next()
    assert session.current_id == "P002"
    assert session.labels_by_id["P002"].label == ""


def test_reset_clears_labels_and_keeps_ids(tmp_path: Path) -> None:
    # Build fake 132 inventory for reset API contract
    root = tmp_path / "aivai_private_seed_v1"
    raw = root / "raw"
    review = root / "review"
    raw.mkdir(parents=True)
    review.mkdir()
    for i in range(132):
        _make_jpeg(raw / f"shot_{i:03d}.jpg", color=(i % 200, 10, 10))
    inv = build_inventory(raw)
    write_inventory(inv, review / "inventory.json")
    write_blank_labels_csv(inv, review / "labels_to_review.csv")
    session = LabelingSession.open(root, expected_count=132)
    session.apply_label("P001", "CAR_SALE")
    session.apply_label("P002", "AUTO_PARTS")
    assert session.progress()["reviewed"] == 2

    before_hashes = {p.name: sha256_file(p) for p in raw.iterdir()}
    before_ids = [r.private_id for r in inv]
    result = reset_human_labels(private_root=root)
    assert result["reviewed"] == 0
    assert result["reset_rows"] == 132

    rows = load_labels_csv(review / "labels_to_review.csv")
    assert len(rows) == 132
    assert all(r.label == "" and not r.reviewed for r in rows)
    assert [r.private_id for r in rows] == before_ids
    assert before_ids[0] == "P001" and before_ids[-1] == "P132"
    assert {p.name: sha256_file(p) for p in raw.iterdir()} == before_hashes

    session2 = LabelingSession.open(root, expected_count=132)
    assert session2.current_id == "P001"
    assert session2.progress()["reviewed"] == 0
