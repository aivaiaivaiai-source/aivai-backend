"""Private seed ground-truth preparation helpers (3B-2P).

PRIVATE INTERNAL EVALUATION / SMOKE DATA ONLY.
Does not touch production, public seed freeze, models, or network inference.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
from dataclasses import asdict, dataclass
from io import BytesIO
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageDraw, ImageFont

LABEL_TAXONOMY = (
    "CAR_SALE",
    "AUTO_PARTS",
    "TRUCK_TRANSPORT",
    "SPECIAL_MACHINERY",
    "MOTORCYCLES",
    "WATER_TRANSPORT",
    "BUSES",
    "COMMERCIAL_TRANSPORT",
    "REAL_ESTATE",
    "OTHER",
    "UNCLEAR",
)

THUMB_LONG_EDGE = 280
TILES_PER_SHEET = 24  # 6x4
SHEET_COLS = 6
SHEET_PAD = 12
LABEL_BAND = 28


@dataclass(frozen=True)
class InventoryRow:
    private_id: str
    original_filename: str
    sha256: str
    width: int
    height: int
    bytes: int


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def list_raw_images(raw_dir: Path) -> list[Path]:
    files = [
        p
        for p in raw_dir.iterdir()
        if p.is_file() and p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}
    ]
    return sorted(files, key=lambda p: p.name.casefold())


def assign_stable_ids(files: Iterable[Path]) -> list[tuple[str, Path]]:
    out: list[tuple[str, Path]] = []
    for i, path in enumerate(files, start=1):
        out.append((f"P{i:03d}", path))
    return out


def build_inventory(raw_dir: Path) -> list[InventoryRow]:
    rows: list[InventoryRow] = []
    for private_id, path in assign_stable_ids(list_raw_images(raw_dir)):
        digest = sha256_file(path)
        with Image.open(path) as im:
            w, h = im.size
        rows.append(
            InventoryRow(
                private_id=private_id,
                original_filename=path.name,
                sha256=digest,
                width=int(w),
                height=int(h),
                bytes=path.stat().st_size,
            )
        )
    return rows


def write_inventory(rows: list[InventoryRow], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "status": "LABELING_PENDING",
        "dataset": "aivai_private_seed_v1",
        "classification": "PRIVATE INTERNAL EVALUATION / SMOKE DATA ONLY",
        "count": len(rows),
        "items": [asdict(r) for r in rows],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_blank_labels_csv(rows: list[InventoryRow], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
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
        writer.writeheader()
        for r in rows:
            writer.writerow(
                {
                    "private_id": r.private_id,
                    "label": "",
                    "listing_group": "",
                    "difficulty": "",
                    "notes": "",
                    "reviewed": "false",
                }
            )


def write_labeling_summary(path: Path, *, total: int, labels: dict[str, int] | None = None) -> None:
    labels = labels or {k: 0 for k in LABEL_TAXONOMY}
    reviewed = sum(labels.values())
    lines = [
        "AIVAI PRIVATE SEED - LABELING SUMMARY",
        "status: LABELING_PENDING",
        f"Total: {total}",
        f"Reviewed: {reviewed}",
        f"Remaining: {total - reviewed}",
    ]
    for key in LABEL_TAXONOMY:
        lines.append(f"{key}: {labels.get(key, 0)}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _thumbnail_no_exif(src: Path, long_edge: int = THUMB_LONG_EDGE) -> Image.Image:
    with Image.open(src) as im:
        im = im.convert("RGB")
        w, h = im.size
        scale = long_edge / max(w, h)
        if scale < 1:
            nw = max(1, int(round(w * scale)))
            nh = max(1, int(round(h * scale)))
            im = im.resize((nw, nh), Image.Resampling.LANCZOS)
        else:
            im = im.copy()
    # rebuild without EXIF
    buf = BytesIO()
    im.save(buf, format="JPEG", quality=88, optimize=True)
    buf.seek(0)
    clean = Image.open(buf)
    clean.load()
    return clean.convert("RGB")


def jpeg_has_exif(path: Path) -> bool:
    data = path.read_bytes()
    if data[:2] != b"\xff\xd8":
        return False
    i = 2
    while i + 4 < len(data):
        if data[i] != 0xFF:
            break
        marker = data[i + 1]
        if marker == 0xE1:
            return True
        if marker in (0xD9, 0xDA):
            break
        if marker == 0x01 or (0xD0 <= marker <= 0xD9):
            i += 2
            continue
        seglen = int.from_bytes(data[i + 2 : i + 4], "big")
        i += 2 + seglen
    return False


def create_contact_sheets(
    *,
    raw_dir: Path,
    inventory: list[InventoryRow],
    out_dir: Path,
    tiles_per_sheet: int = TILES_PER_SHEET,
    cols: int = SHEET_COLS,
) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    by_name = {r.original_filename: r for r in inventory}
    ordered = [(r.private_id, raw_dir / r.original_filename) for r in inventory]
    for private_id, path in ordered:
        if not path.is_file():
            raise FileNotFoundError(f"missing raw for {private_id}: {path}")
        if path.name not in by_name:
            raise RuntimeError(f"inventory mismatch: {path.name}")

    sheets: list[Path] = []
    n_sheets = max(1, math.ceil(len(ordered) / tiles_per_sheet))
    try:
        font = ImageFont.truetype("arial.ttf", 18)
    except OSError:
        font = ImageFont.load_default()

    for sheet_idx in range(n_sheets):
        chunk = ordered[sheet_idx * tiles_per_sheet : (sheet_idx + 1) * tiles_per_sheet]
        thumbs: list[tuple[str, Image.Image]] = []
        max_w = 0
        max_h = 0
        for private_id, path in chunk:
            thumb = _thumbnail_no_exif(path)
            thumbs.append((private_id, thumb))
            max_w = max(max_w, thumb.width)
            max_h = max(max_h, thumb.height)

        rows_n = math.ceil(len(thumbs) / cols)
        cell_w = max_w
        cell_h = max_h + LABEL_BAND
        sheet_w = cols * cell_w + (cols + 1) * SHEET_PAD
        sheet_h = rows_n * cell_h + (rows_n + 1) * SHEET_PAD
        canvas = Image.new("RGB", (sheet_w, sheet_h), (245, 245, 245))
        draw = ImageDraw.Draw(canvas)

        for i, (private_id, thumb) in enumerate(thumbs):
            r = i // cols
            c = i % cols
            x0 = SHEET_PAD + c * (cell_w + SHEET_PAD)
            y0 = SHEET_PAD + r * (cell_h + SHEET_PAD)
            ox = x0 + (cell_w - thumb.width) // 2
            oy = y0 + (max_h - thumb.height) // 2
            canvas.paste(thumb, (ox, oy))
            draw.rectangle(
                [x0, y0 + max_h, x0 + cell_w, y0 + cell_h],
                fill=(30, 30, 30),
            )
            draw.text(
                (x0 + 8, y0 + max_h + 4),
                private_id,
                fill=(255, 255, 255),
                font=font,
            )

        out_path = out_dir / f"contact_sheet_{sheet_idx + 1:02d}.jpg"
        canvas.save(out_path, format="JPEG", quality=90, optimize=True)
        sheets.append(out_path)
    return sheets


def contact_sheet_private_ids(inventory_private_ids: list[str], tiles_per_sheet: int) -> list[list[str]]:
    """Deterministic sheet membership from inventory order (no OCR)."""
    sheets: list[list[str]] = []
    for i in range(0, len(inventory_private_ids), tiles_per_sheet):
        sheets.append(inventory_private_ids[i : i + tiles_per_sheet])
    return sheets


def move_screens_to_private_raw(*, src_dir: Path, dst_raw: Path) -> dict:
    """Move files into dst_raw. Fails if destination exists. Verifies hashes."""
    if not src_dir.is_dir():
        raise FileNotFoundError(f"source missing: {src_dir}")
    if dst_raw.exists():
        raise FileExistsError(f"destination exists (refusing overwrite): {dst_raw}")

    before: dict[str, tuple[str, int]] = {}
    files = [p for p in src_dir.iterdir() if p.is_file()]
    for p in files:
        before[p.name] = (sha256_file(p), p.stat().st_size)

    dst_raw.parent.mkdir(parents=True, exist_ok=True)
    src_dir.rename(dst_raw)

    if src_dir.exists():
        raise RuntimeError("source still exists after move")
    after_files = [p for p in dst_raw.iterdir() if p.is_file()]
    if len(after_files) != len(before):
        raise RuntimeError(
            f"count mismatch after move: {len(after_files)} != {len(before)}"
        )

    mismatches = []
    total_before = sum(s for _, s in before.values())
    total_after = 0
    for p in after_files:
        digest = sha256_file(p)
        size = p.stat().st_size
        total_after += size
        prev = before.get(p.name)
        if prev is None or prev[0] != digest or prev[1] != size:
            mismatches.append(p.name)
    if mismatches:
        raise RuntimeError(f"hash/size mismatch after move: {mismatches[:10]}")
    if total_before != total_after:
        raise RuntimeError("total bytes mismatch after move")

    return {
        "moved": len(after_files),
        "total_bytes": total_after,
        "source_gone": not src_dir.exists(),
        "destination": str(dst_raw),
    }


def prepare_private_seed_review(*, private_root: Path) -> dict:
    """Build inventory, blank labels, contact sheets, summary under private_root."""
    raw = private_root / "raw"
    review = private_root / "review"
    review.mkdir(parents=True, exist_ok=True)

    inventory = build_inventory(raw)
    write_inventory(inventory, review / "inventory.json")
    write_blank_labels_csv(inventory, review / "labels_to_review.csv")
    write_labeling_summary(review / "labeling_summary.txt", total=len(inventory))
    sheets = create_contact_sheets(raw_dir=raw, inventory=inventory, out_dir=review)

    exif_free = all(not jpeg_has_exif(p) for p in sheets)
    taxonomy_path = review / "label_taxonomy.json"
    taxonomy_path.write_text(
        json.dumps(
            {
                "labels": list(LABEL_TAXONOMY),
                "notes": (
                    "Benchmark-private taxonomy only. "
                    "Do not create these in production DB. "
                    "Image-level labels; listing_group filled by human later."
                ),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    status = {
        "status": "LABELING_PENDING",
        "raw_count": len(inventory),
        "contact_sheets": [p.name for p in sheets],
        "tiles_per_sheet": TILES_PER_SHEET,
        "review_exif_free": exif_free,
        "auto_labels": False,
        "private_ids": [r.private_id for r in inventory],
    }
    (review / "prepare_status.json").write_text(
        json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return status
