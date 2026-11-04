"""Bounded download helpers for APPROVED sources only."""

from __future__ import annotations

import hashlib
import io
import json
import random
from dataclasses import dataclass
from pathlib import Path
from urllib.request import Request, urlopen

DEFAULT_TIMEOUT_S = 60
DEFAULT_RETRIES = 2

CLOTHING_REPO = "alexeygrigorev/clothing-dataset-small"
CLOTHING_TREE_API = (
    f"https://api.github.com/repos/{CLOTHING_REPO}/git/trees/master?recursive=1"
)
CLOTHING_RAW_BASE = (
    f"https://raw.githubusercontent.com/{CLOTHING_REPO}/master/"
)
CLOTHING_OFFICIAL = f"https://github.com/{CLOTHING_REPO}"


@dataclass
class DownloadLimits:
    max_total_files: int = 250
    max_total_bytes: int = 80 * 1024 * 1024  # 80 MB
    max_per_source_files: int = 200
    timeout_s: int = DEFAULT_TIMEOUT_S
    retries: int = DEFAULT_RETRIES


@dataclass
class FetchedAsset:
    local_path: Path
    source_record_id: str
    source_label: str
    content_hash: str
    bytes_len: int


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def http_get(url: str, *, timeout_s: int, retries: int) -> bytes:
    last_err: Exception | None = None
    for _ in range(max(1, retries + 1)):
        try:
            req = Request(url, headers={"User-Agent": "aivai-seed-builder/3b2"})
            with urlopen(req, timeout=timeout_s) as resp:  # noqa: S310 — curated URL
                return resp.read()
        except Exception as exc:  # noqa: BLE001
            last_err = exc
    raise RuntimeError(f"download failed after retries: {url}: {last_err}")


def strip_exif_jpeg_if_possible(data: bytes) -> bytes:
    """Best-effort EXIF strip; returns original bytes if Pillow unavailable/fails."""
    try:
        from PIL import Image, ImageOps
    except ImportError:
        return data
    try:
        with Image.open(io.BytesIO(data)) as im:
            im = ImageOps.exif_transpose(im)
            if im.mode not in ("RGB", "L"):
                im = im.convert("RGB")
            elif im.mode == "L":
                im = im.convert("RGB")
            out = io.BytesIO()
            im.save(out, format="JPEG", quality=92)
            return out.getvalue()
    except Exception:
        return data


def _list_clothing_train_paths(*, timeout_s: int, retries: int) -> dict[str, list[str]]:
    """Return {class_label: [repo-relative paths]} for train split only."""
    from benchmarks.media_classification.seed.mapping import CLOTHING_SMALL_MAP

    raw = http_get(CLOTHING_TREE_API, timeout_s=timeout_s, retries=retries)
    tree = json.loads(raw.decode("utf-8"))
    by_class: dict[str, list[str]] = {}
    for node in tree.get("tree") or []:
        if node.get("type") != "blob":
            continue
        path = str(node.get("path") or "").replace("\\", "/")
        if not path.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
            continue
        parts = path.split("/")
        if len(parts) < 3:
            continue
        split, cls, name = parts[0], parts[1], parts[2]
        if split.lower() != "train":
            continue
        key = cls.lower().replace("_", "-")
        if key not in CLOTHING_SMALL_MAP:
            continue
        if name.startswith("."):
            continue
        by_class.setdefault(key, []).append(path)
    for key in by_class:
        by_class[key] = sorted(by_class[key])
    if not by_class:
        raise RuntimeError("no train class paths found via GitHub tree API")
    return by_class


def download_clothing_small_subset(
    *,
    dest_root: Path,
    limits: DownloadLimits,
    rng_seed: int,
    target_cases: int,
    dry_run: bool,
) -> tuple[list[FetchedAsset], dict]:
    """
    Selectively download a deterministic subset of clothing-dataset-small (train/).
    Avoids full-repo zip (slow / oversized for seed).
    """
    stats: dict = {
        "source": "agrigorev_clothing_dataset_small",
        "url": CLOTHING_OFFICIAL,
        "strategy": "github_raw_selective",
        "dry_run": dry_run,
        "planned_cases": target_cases,
    }
    if dry_run:
        stats["action"] = "would_list_tree_and_fetch_raw_subset"
        stats["estimated_bytes_hint"] = target_cases * 45_000
        return [], stats

    by_class = _list_clothing_train_paths(
        timeout_s=limits.timeout_s, retries=limits.retries
    )
    stats["classes_found"] = sorted(by_class.keys())

    rng = random.Random(rng_seed)
    classes = sorted(by_class.keys())
    # Prefer non-ambiguous classes for auto-include (still map later).
    from benchmarks.media_classification.seed.mapping import CLOTHING_SMALL_MAP

    preferred = [
        c
        for c in classes
        if not CLOTHING_SMALL_MAP[c].review_required
    ]
    if not preferred:
        preferred = classes

    per_class = max(1, target_cases // max(1, len(preferred)))
    chosen: list[tuple[str, str]] = []
    for cls in preferred:
        files = list(by_class[cls])
        rng.shuffle(files)
        for path in files[:per_class]:
            chosen.append((cls, path))
        if len(chosen) >= target_cases:
            break
    if len(chosen) < target_cases:
        pool = [(c, p) for c in preferred for p in by_class[c]]
        rng.shuffle(pool)
        seen = set(chosen)
        for item in pool:
            if len(chosen) >= target_cases:
                break
            if item not in seen:
                chosen.append(item)
                seen.add(item)

    max_n = min(target_cases, limits.max_per_source_files, limits.max_total_files)
    chosen = chosen[:max_n]
    stats["selected_paths"] = len(chosen)
    stats["estimated_bytes_hint"] = sum(
        # size unknown until fetch; use conservative hint from tree if present
        40_000
        for _ in chosen
    )

    out_images = dest_root / "images" / "agrigorev_clothing_small"
    out_images.mkdir(parents=True, exist_ok=True)
    assets: list[FetchedAsset] = []
    total_bytes = 0

    for cls, rel_path in chosen:
        url = CLOTHING_RAW_BASE + rel_path
        data = http_get(url, timeout_s=limits.timeout_s, retries=limits.retries)
        data = strip_exif_jpeg_if_possible(data)
        h = sha256_bytes(data)
        total_bytes += len(data)
        if total_bytes > limits.max_total_bytes:
            raise RuntimeError(
                f"max_total_bytes exceeded while writing assets "
                f"({total_bytes} > {limits.max_total_bytes})"
            )
        fname = Path(rel_path).name
        dest = out_images / f"{cls}_{Path(fname).stem}_{h[:10]}.jpg"
        dest.write_bytes(data)
        assets.append(
            FetchedAsset(
                local_path=dest,
                source_record_id=f"clothing-small:{rel_path}",
                source_label=cls,
                content_hash=h,
                bytes_len=len(data),
            )
        )
        if len(assets) >= limits.max_total_files:
            break

    if not assets:
        raise RuntimeError("clothing selective download produced zero assets")

    stats.update(
        {
            "assets": len(assets),
            "bytes_written": total_bytes,
            "partial": False,
        }
    )
    return assets, stats
