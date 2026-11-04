"""Benchmark image preprocessing — bounded, non-destructive to dataset files."""

from __future__ import annotations

import io
import time
from dataclasses import dataclass
from pathlib import Path


@dataclass
class PreparedImage:
    source_path: Path
    bytes_data: bytes
    width: int | None
    height: int | None
    preprocess_ms: float
    max_edge_applied: int | None


def _minimal_pass_through(path: Path) -> PreparedImage:
    t0 = time.perf_counter()
    data = path.read_bytes()
    return PreparedImage(
        source_path=path,
        bytes_data=data,
        width=None,
        height=None,
        preprocess_ms=(time.perf_counter() - t0) * 1000,
        max_edge_applied=None,
    )


def prepare_image(path: Path, *, max_edge: int | None) -> PreparedImage:
    """
    EXIF transpose + RGB + bounded resize when Pillow is available.
    Does not write back to dataset. No enhance/crop that favors one model.
    """
    if max_edge is None or max_edge <= 0:
        return _minimal_pass_through(path)

    try:
        from PIL import Image, ImageOps
    except ImportError:
        return _minimal_pass_through(path)

    t0 = time.perf_counter()
    with Image.open(path) as im:
        im = ImageOps.exif_transpose(im)
        if im.mode not in ("RGB", "L"):
            im = im.convert("RGB")
        elif im.mode == "L":
            im = im.convert("RGB")
        w, h = im.size
        long_edge = max(w, h)
        if long_edge > max_edge:
            scale = max_edge / float(long_edge)
            nw = max(1, int(round(w * scale)))
            nh = max(1, int(round(h * scale)))
            im = im.resize((nw, nh), Image.Resampling.BILINEAR)
            w, h = im.size
        buf = io.BytesIO()
        im.save(buf, format="JPEG", quality=90)
        data = buf.getvalue()
    return PreparedImage(
        source_path=path,
        bytes_data=data,
        width=w,
        height=h,
        preprocess_ms=(time.perf_counter() - t0) * 1000,
        max_edge_applied=max_edge,
    )


def select_image_paths(
    paths: list[str],
    *,
    mode: str,
    adapter_max: int,
) -> list[str]:
    mode_key = (mode or "first_3").strip().lower()
    if mode_key == "cover_only":
        return paths[:1]
    if mode_key == "first_2":
        return paths[:2]
    if mode_key == "first_3":
        return paths[:3]
    if mode_key == "all":
        return paths[:9]
    if mode_key == "adaptive":
        # Adapter-driven: still cap by adapter_max; adaptive confidence is adapter-side.
        return paths[: max(1, adapter_max)]
    raise ValueError(
        f"Unknown image-count mode '{mode}'. "
        "Use: cover_only, first_2, first_3, all, adaptive"
    )
