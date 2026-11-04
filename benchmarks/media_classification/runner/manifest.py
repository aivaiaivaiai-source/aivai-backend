"""Manifest load + validation."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from benchmarks.media_classification.runner.catalog import CatalogSnapshot

ALLOWED_DIFFICULTY = frozenset({"easy", "medium", "hard", "ambiguous"})
ALLOWED_SPLITS = frozenset({"train", "validation", "test"})
ALLOWED_IMAGE_SUFFIXES = frozenset({".jpg", ".jpeg", ".png", ".webp"})


@dataclass
class ManifestRecord:
    test_id: str
    images: list[str]
    ground_truth_slug: str
    ground_truth_id: int | None
    ground_truth_path: list[str]
    acceptable_slugs: list[str]
    difficulty: str
    tags: list[str]
    notes: str
    split: str
    source_group_id: str | None
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationResult:
    ok: bool
    records: list[ManifestRecord]
    errors: list[str]


def _parse_line(line: str, line_no: int) -> dict[str, Any]:
    import json

    try:
        obj = json.loads(line)
    except json.JSONDecodeError as exc:
        raise ValueError(f"line {line_no}: invalid JSON ({exc})") from exc
    if not isinstance(obj, dict):
        raise ValueError(f"line {line_no}: record must be a JSON object")
    return obj


def load_manifest_records(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    text = path.read_text(encoding="utf-8")
    for i, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        rows.append(_parse_line(stripped, i))
    return rows


def validate_manifest(
    *,
    manifest_path: Path,
    images_root: Path,
    catalog: CatalogSnapshot,
    split_filter: str | None = "test",
) -> ValidationResult:
    errors: list[str] = []
    records: list[ManifestRecord] = []
    seen_ids: set[str] = set()

    try:
        raw_rows = load_manifest_records(manifest_path)
    except ValueError as exc:
        return ValidationResult(ok=False, records=[], errors=[str(exc)])

    if not raw_rows:
        return ValidationResult(ok=False, records=[], errors=["manifest is empty"])

    for idx, raw in enumerate(raw_rows, start=1):
        test_id = str(raw.get("test_id") or "").strip()
        if not test_id:
            errors.append(f"record {idx}: missing test_id")
            continue
        if test_id in seen_ids:
            errors.append(f"duplicate test_id: {test_id}")
            continue
        seen_ids.add(test_id)

        images = raw.get("images")
        if not isinstance(images, list) or not images:
            errors.append(f"{test_id}: images must be a non-empty list")
            continue
        if len(images) > 9:
            errors.append(f"{test_id}: more than 9 images ({len(images)})")
            continue

        norm_images: list[str] = []
        seen_paths: set[str] = set()
        for p in images:
            if not isinstance(p, str) or not p.strip():
                errors.append(f"{test_id}: empty image path")
                continue
            rel = p.replace("\\", "/").strip()
            if rel in seen_paths:
                errors.append(f"{test_id}: duplicate image path {rel}")
                continue
            seen_paths.add(rel)
            suffix = Path(rel).suffix.lower()
            if suffix not in ALLOWED_IMAGE_SUFFIXES:
                errors.append(f"{test_id}: unsupported image type {suffix}")
                continue
            abs_path = (images_root / rel).resolve()
            try:
                abs_path.relative_to(images_root.resolve())
            except ValueError:
                errors.append(f"{test_id}: image path escapes images root: {rel}")
                continue
            if not abs_path.is_file():
                errors.append(f"{test_id}: missing image file: {rel}")
                continue
            norm_images.append(rel)

        gt = raw.get("ground_truth")
        if not isinstance(gt, dict):
            errors.append(f"{test_id}: ground_truth must be an object")
            continue
        gt_slug = str(gt.get("category_slug") or "").strip()
        if not gt_slug:
            errors.append(f"{test_id}: ground_truth.category_slug required")
            continue
        cat = catalog.get_by_slug(gt_slug)
        if cat is None or not cat.is_active:
            errors.append(f"{test_id}: ground_truth slug not in catalog: {gt_slug}")
            continue
        gt_id = gt.get("category_id")
        if gt_id is not None and int(gt_id) != cat.category_id:
            errors.append(
                f"{test_id}: ground_truth.category_id {gt_id} != catalog id {cat.category_id}"
            )

        difficulty = str(raw.get("difficulty") or "medium")
        if difficulty not in ALLOWED_DIFFICULTY:
            errors.append(f"{test_id}: invalid difficulty {difficulty}")
            continue

        split = str(raw.get("split") or "test")
        if split not in ALLOWED_SPLITS:
            errors.append(f"{test_id}: invalid split {split}")
            continue

        alts_raw = raw.get("acceptable_alternatives") or []
        if not isinstance(alts_raw, list):
            errors.append(f"{test_id}: acceptable_alternatives must be a list")
            continue
        alt_slugs: list[str] = []
        for alt in alts_raw:
            if not isinstance(alt, dict):
                errors.append(f"{test_id}: alternative must be object")
                continue
            a_slug = str(alt.get("category_slug") or "").strip()
            if not a_slug:
                errors.append(f"{test_id}: alternative missing category_slug")
                continue
            if a_slug == gt_slug:
                errors.append(f"{test_id}: alternative duplicates ground_truth")
                continue
            if catalog.get_by_slug(a_slug) is None:
                errors.append(f"{test_id}: alternative slug not in catalog: {a_slug}")
                continue
            alt_slugs.append(a_slug)

        if split_filter is not None and split != split_filter:
            continue

        if not norm_images:
            errors.append(f"{test_id}: no valid images after checks")
            continue

        records.append(
            ManifestRecord(
                test_id=test_id,
                images=norm_images,
                ground_truth_slug=gt_slug,
                ground_truth_id=cat.category_id,
                ground_truth_path=list(gt.get("path") or list(cat.hierarchy_path)),
                acceptable_slugs=alt_slugs,
                difficulty=difficulty,
                tags=[str(t) for t in (raw.get("tags") or [])],
                notes=str(raw.get("notes") or ""),
                split=split,
                source_group_id=(
                    str(raw["source_group_id"])
                    if raw.get("source_group_id") is not None
                    else None
                ),
                raw=raw,
            )
        )

    return ValidationResult(ok=not errors, records=records, errors=errors)
