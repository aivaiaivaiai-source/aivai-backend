"""Human labeling business logic for private seed (3B-2P3).

No AI, no network, no raw mutation. GUI-agnostic for unit tests.
11-class benchmark-private taxonomy.
"""

from __future__ import annotations

import csv
import json
import os
import tempfile
from dataclasses import dataclass, field
from io import BytesIO
from pathlib import Path
from typing import Any

from benchmarks.media_classification.private_seed import (
    LABEL_TAXONOMY,
    InventoryRow,
    sha256_file,
    write_labeling_summary,
)

LABEL_FIELDS = (
    "private_id",
    "label",
    "listing_group",
    "difficulty",
    "notes",
    "reviewed",
)

# Hotkeys: 1-9, 0=OTHER, X=UNCLEAR (no multi-digit sequences).
KEY_TO_LABEL: dict[str, str] = {
    "1": "CAR_SALE",
    "2": "AUTO_PARTS",
    "3": "TRUCK_TRANSPORT",
    "4": "SPECIAL_MACHINERY",
    "5": "MOTORCYCLES",
    "6": "WATER_TRANSPORT",
    "7": "BUSES",
    "8": "COMMERCIAL_TRANSPORT",
    "9": "REAL_ESTATE",
    "0": "OTHER",
    "x": "UNCLEAR",
    "X": "UNCLEAR",
}

# Display order for buttons (canonical key shown on UI).
BUTTON_KEYS: tuple[tuple[str, str], ...] = (
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
)

LABEL_TO_KEY: dict[str, str] = {label: key for key, label in BUTTON_KEYS}

LABEL_RU: dict[str, str] = {
    "CAR_SALE": "Продажа авто",
    "AUTO_PARTS": "Автозапчасти",
    "TRUCK_TRANSPORT": "Грузовой транспорт",
    "SPECIAL_MACHINERY": "Спецтехника",
    "MOTORCYCLES": "Мототехника",
    "WATER_TRANSPORT": "Водный транспорт",
    "BUSES": "Автобусы",
    "COMMERCIAL_TRANSPORT": "Коммерческий транспорт",
    "REAL_ESTATE": "Недвижимость",
    "OTHER": "Другое",
    "UNCLEAR": "Непонятно",
}

LABEL_HINTS_RU: tuple[str, ...] = (
    "1 Продажа авто — легковой/SUV/кроссовер/минивэн целиком (не грузовик/мото/запчасти).",
    "2 Автозапчасти — отдельная деталь: двигатель, фара, колесо, диск, бампер и т.п.",
    "3 Грузовой транспорт — грузовик/тягач/самосвал целиком (не спецтехника).",
    "4 Спецтехника — экскаватор, погрузчик, кран, бульдозер, дорожная техника.",
    "5 Мототехника — мотоцикл, скутер, мопед, квадроцикл.",
    "6 Водный транспорт — лодка, катер, гидроцикл.",
    "7 Автобусы — автобус / пассажирский микроавтобус.",
    "8 Коммерческий транспорт — коммерческий фургон/малотоннажный, не CAR/TRUCK/BUS.",
    "9 Недвижимость — квартира, дом, помещение, участок.",
    "0 Другое — очевидно не классы 1–9.",
    "X Непонятно — нельзя уверенно определить; при сомнении — X, не угадывать.",
)

DISPLAY_LONG_EDGE = 1200


@dataclass
class LabelRow:
    private_id: str
    label: str
    listing_group: str
    difficulty: str
    notes: str
    reviewed: bool


@dataclass
class DatasetBundle:
    private_root: Path
    raw_dir: Path
    review_dir: Path
    inventory_path: Path
    labels_path: Path
    inventory: list[InventoryRow]
    labels: list[LabelRow]
    raw_paths: dict[str, Path]  # private_id -> raw file


@dataclass
class UndoRecord:
    private_id: str
    previous_label: str
    previous_reviewed: bool


@dataclass
class LabelingSession:
    bundle: DatasetBundle
    labels_by_id: dict[str, LabelRow] = field(default_factory=dict)
    ordered_ids: list[str] = field(default_factory=list)
    current_index: int = 0
    undo_stack: list[UndoRecord] = field(default_factory=list)

    @classmethod
    def open(cls, private_root: Path, *, expected_count: int = 132) -> LabelingSession:
        bundle = load_and_validate_dataset(private_root, expected_count=expected_count)
        labels_by_id = {r.private_id: r for r in bundle.labels}
        ordered_ids = [r.private_id for r in bundle.inventory]
        session = cls(
            bundle=bundle,
            labels_by_id=labels_by_id,
            ordered_ids=ordered_ids,
            current_index=first_unreviewed_index(ordered_ids, labels_by_id),
        )
        return session

    @property
    def total(self) -> int:
        return len(self.ordered_ids)

    @property
    def current_id(self) -> str:
        return self.ordered_ids[self.current_index]

    def current_row(self) -> LabelRow:
        return self.labels_by_id[self.current_id]

    def current_raw_path(self) -> Path:
        return self.bundle.raw_paths[self.current_id]

    def progress(self) -> dict[str, Any]:
        reviewed = sum(1 for r in self.labels_by_id.values() if r.reviewed)
        counts = {k: 0 for k in LABEL_TAXONOMY}
        for r in self.labels_by_id.values():
            if r.reviewed and r.label in counts:
                counts[r.label] += 1
        return {
            "reviewed": reviewed,
            "remaining": self.total - reviewed,
            "total": self.total,
            "counts": counts,
            "complete": reviewed == self.total,
        }

    def apply_label(self, private_id: str, label: str) -> None:
        assert_writable_private_seed(self.bundle.private_root)
        if label not in LABEL_TAXONOMY:
            raise ValueError(f"invalid label: {label}")
        row = self.labels_by_id[private_id]
        self.undo_stack.append(
            UndoRecord(
                private_id=private_id,
                previous_label=row.label,
                previous_reviewed=row.reviewed,
            )
        )
        row.label = label
        row.reviewed = True
        save_labels_csv(self.bundle.labels_path, list(self.labels_by_id.values()))
        write_labeling_summary(
            self.bundle.review_dir / "labeling_summary.txt",
            total=self.total,
            labels=self.progress()["counts"],
        )

    def label_current_and_advance(self, label: str) -> bool:
        """Apply label to current item; advance to next unreviewed. Returns True if complete."""
        pid = self.current_id
        self.apply_label(pid, label)
        if self.progress()["complete"]:
            return True
        self.current_index = first_unreviewed_index(self.ordered_ids, self.labels_by_id)
        return False

    def relabel_current(self, label: str) -> None:
        """Replace label on current item without auto-advance."""
        assert_writable_private_seed(self.bundle.private_root)
        pid = self.current_id
        row = self.labels_by_id[pid]
        self.undo_stack.append(
            UndoRecord(
                private_id=pid,
                previous_label=row.label,
                previous_reviewed=row.reviewed,
            )
        )
        row.label = label
        row.reviewed = True
        save_labels_csv(self.bundle.labels_path, list(self.labels_by_id.values()))
        write_labeling_summary(
            self.bundle.review_dir / "labeling_summary.txt",
            total=self.total,
            labels=self.progress()["counts"],
        )

    def undo_last(self) -> bool:
        assert_writable_private_seed(self.bundle.private_root)
        if not self.undo_stack:
            return False
        rec = self.undo_stack.pop()
        row = self.labels_by_id[rec.private_id]
        row.label = rec.previous_label
        row.reviewed = rec.previous_reviewed
        save_labels_csv(self.bundle.labels_path, list(self.labels_by_id.values()))
        write_labeling_summary(
            self.bundle.review_dir / "labeling_summary.txt",
            total=self.total,
            labels=self.progress()["counts"],
        )
        self.current_index = self.ordered_ids.index(rec.private_id)
        return True

    def go_previous(self) -> None:
        if self.current_index > 0:
            self.current_index -= 1

    def go_next(self) -> None:
        if self.current_index < self.total - 1:
            self.current_index += 1


def _parse_reviewed(value: str) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def load_inventory_json(path: Path) -> list[InventoryRow]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    items = raw.get("items") or []
    out: list[InventoryRow] = []
    for item in items:
        out.append(
            InventoryRow(
                private_id=str(item["private_id"]),
                original_filename=str(item["original_filename"]),
                sha256=str(item["sha256"]),
                width=int(item["width"]),
                height=int(item["height"]),
                bytes=int(item["bytes"]),
            )
        )
    return out


def load_labels_csv(path: Path) -> list[LabelRow]:
    with path.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    out: list[LabelRow] = []
    for row in rows:
        out.append(
            LabelRow(
                private_id=str(row["private_id"]).strip(),
                label=str(row.get("label") or "").strip(),
                listing_group=str(row.get("listing_group") or "").strip(),
                difficulty=str(row.get("difficulty") or "").strip(),
                notes=str(row.get("notes") or "").strip(),
                reviewed=_parse_reviewed(str(row.get("reviewed") or "false")),
            )
        )
    return out


def save_labels_csv(path: Path, rows: list[LabelRow]) -> None:
    """Atomic write preserving row order by private_id sort P001.."""
    ordered = sorted(rows, key=lambda r: r.private_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(
        prefix=".labels_", suffix=".csv", dir=str(path.parent)
    )
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=LABEL_FIELDS)
            writer.writeheader()
            for r in ordered:
                writer.writerow(
                    {
                        "private_id": r.private_id,
                        "label": r.label,
                        "listing_group": r.listing_group,
                        "difficulty": r.difficulty,
                        "notes": r.notes,
                        "reviewed": "true" if r.reviewed else "false",
                    }
                )
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, path)
    finally:
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:
                pass


def first_unreviewed_index(
    ordered_ids: list[str], labels_by_id: dict[str, LabelRow]
) -> int:
    for i, pid in enumerate(ordered_ids):
        if not labels_by_id[pid].reviewed:
            return i
    return max(0, len(ordered_ids) - 1)


def load_and_validate_dataset(
    private_root: Path, *, expected_count: int = 132
) -> DatasetBundle:
    private_root = private_root.resolve()
    raw_dir = private_root / "raw"
    review_dir = private_root / "review"
    inventory_path = review_dir / "inventory.json"
    labels_path = review_dir / "labels_to_review.csv"

    errors: list[str] = []
    if not inventory_path.is_file():
        errors.append(f"missing inventory: {inventory_path}")
    if not labels_path.is_file():
        errors.append(f"missing labels CSV: {labels_path}")
    if not raw_dir.is_dir():
        errors.append(f"missing raw dir: {raw_dir}")
    if errors:
        raise RuntimeError("dataset validation failed:\n  - " + "\n  - ".join(errors))

    inventory = load_inventory_json(inventory_path)
    labels = load_labels_csv(labels_path)

    if len(inventory) != expected_count:
        errors.append(f"inventory count {len(inventory)} != {expected_count}")
    if len(labels) != expected_count:
        errors.append(f"labels count {len(labels)} != {expected_count}")

    inv_ids = [r.private_id for r in inventory]
    label_ids = [r.private_id for r in labels]
    expected = [f"P{i:03d}" for i in range(1, expected_count + 1)]

    if inv_ids != expected:
        errors.append(f"inventory IDs are not P001..P{expected_count:03d} in order")
    if sorted(label_ids) != expected:
        errors.append(f"labels CSV IDs do not match P001..P{expected_count:03d}")
    if {r.private_id for r in inventory} != {r.private_id for r in labels}:
        errors.append("inventory/labels ID set mismatch")

    labels_by_id = {r.private_id: r for r in labels}
    raw_paths: dict[str, Path] = {}

    for item in inventory:
        raw_path = raw_dir / item.original_filename
        if not raw_path.is_file():
            errors.append(f"missing raw file for {item.private_id}: {item.original_filename}")
            continue
        digest = sha256_file(raw_path)
        if digest != item.sha256:
            errors.append(
                f"hash mismatch for {item.private_id}: "
                f"inventory={item.sha256[:12]} actual={digest[:12]}"
            )
        raw_paths[item.private_id] = raw_path

        lr = labels_by_id.get(item.private_id)
        if lr is None:
            errors.append(f"labels row missing for {item.private_id}")
        elif lr.reviewed and lr.label not in LABEL_TAXONOMY:
            errors.append(f"{item.private_id}: reviewed=true but invalid label {lr.label!r}")

    if errors:
        raise RuntimeError("dataset validation failed:\n  - " + "\n  - ".join(errors))

    return DatasetBundle(
        private_root=private_root,
        raw_dir=raw_dir,
        review_dir=review_dir,
        inventory_path=inventory_path,
        labels_path=labels_path,
        inventory=inventory,
        labels=labels,
        raw_paths=raw_paths,
    )


def load_display_preview(raw_path: Path, *, long_edge: int = DISPLAY_LONG_EDGE):
    """Bounded in-memory RGB preview. Does not write to disk."""
    from PIL import Image

    with Image.open(raw_path) as im:
        im = im.convert("RGB")
        w, h = im.size
        scale = long_edge / max(w, h)
        if scale < 1:
            nw = max(1, int(round(w * scale)))
            nh = max(1, int(round(h * scale)))
            im = im.resize((nw, nh), Image.Resampling.LANCZOS)
        else:
            im = im.copy()
    buf = BytesIO()
    im.save(buf, format="PNG")
    buf.seek(0)
    out = Image.open(buf)
    out.load()
    return out.convert("RGB")


def reset_human_labels(*, private_root: Path) -> dict:
    """Clear all human labels to blank; keep inventory/raw/contact sheets intact."""
    assert_writable_private_seed(private_root)
    private_root = private_root.resolve()
    review = private_root / "review"
    inventory_path = review / "inventory.json"
    labels_path = review / "labels_to_review.csv"
    if not inventory_path.is_file():
        raise FileNotFoundError(f"missing inventory: {inventory_path}")

    inventory = load_inventory_json(inventory_path)
    if len(inventory) != 132:
        raise RuntimeError(f"refuse reset: inventory count {len(inventory)} != 132")
    expected = [f"P{i:03d}" for i in range(1, 133)]
    if [r.private_id for r in inventory] != expected:
        raise RuntimeError("refuse reset: inventory IDs are not P001..P132")

    blank = [
        LabelRow(
            private_id=item.private_id,
            label="",
            listing_group="",
            difficulty="",
            notes="",
            reviewed=False,
        )
        for item in inventory
    ]
    save_labels_csv(labels_path, blank)
    write_labeling_summary(
        review / "labeling_summary.txt",
        total=len(blank),
        labels={k: 0 for k in LABEL_TAXONOMY},
    )
    (review / "label_taxonomy.json").write_text(
        json.dumps(
            {
                "labels": list(LABEL_TAXONOMY),
                "keyboard": {
                    "1": "CAR_SALE",
                    "2": "AUTO_PARTS",
                    "3": "TRUCK_TRANSPORT",
                    "4": "SPECIAL_MACHINERY",
                    "5": "MOTORCYCLES",
                    "6": "WATER_TRANSPORT",
                    "7": "BUSES",
                    "8": "COMMERCIAL_TRANSPORT",
                    "9": "REAL_ESTATE",
                    "0": "OTHER",
                    "X": "UNCLEAR",
                },
                "notes": (
                    "BENCHMARK-PRIVATE TAXONOMY ONLY. "
                    "Do not create these in production DB. "
                    "Human ground truth only; no auto labels."
                ),
                "status": "LABELING_PENDING",
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    status_path = review / "prepare_status.json"
    if status_path.is_file():
        status = json.loads(status_path.read_text(encoding="utf-8"))
        status["status"] = "LABELING_PENDING"
        status["taxonomy_version"] = "private-11-class-v1"
        status["auto_labels"] = False
        status_path.write_text(
            json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    return {
        "status": "LABELING_PENDING",
        "reset_rows": len(blank),
        "reviewed": 0,
        "remaining": len(blank),
        "taxonomy": list(LABEL_TAXONOMY),
    }


def assert_writable_private_seed(private_root: Path) -> None:
    """Refuse label mutations once freeze markers exist."""
    from benchmarks.media_classification.private_seed.freeze import is_frozen

    root = private_root.resolve()
    if is_frozen(root) or (root / "freeze.json").is_file():
        raise RuntimeError(
            f"dataset is FROZEN ({root}) — refuse label/reset writes; "
            "create aivai-private-seed-v2 for changes"
        )
