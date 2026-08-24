"""Adaptive smart framing from normalized bbox."""

from __future__ import annotations

from dataclasses import dataclass

from app.services.focus_bbox_detection import NormalizedBbox


@dataclass(frozen=True)
class CropBox:
    left: int
    top: int
    right: int
    bottom: int

    @property
    def width(self) -> int:
        return max(1, self.right - self.left)

    @property
    def height(self) -> int:
        return max(1, self.bottom - self.top)


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def normalized_bbox_from_focus(
    left: float,
    top: float,
    width: float,
    height: float,
) -> NormalizedBbox:
    return NormalizedBbox(
        left=_clamp(left, 0.0, 1.0),
        top=_clamp(top, 0.0, 1.0),
        width=_clamp(width, 0.001, 1.0),
        height=_clamp(height, 0.001, 1.0),
    )


def compute_crop_box(
    img_w: int,
    img_h: int,
    *,
    target_aspect: float,
    bbox: NormalizedBbox | None,
    padding_ratio: float = 0.04,
    target_fill: float = 0.85,
) -> CropBox:
    """
    Compute a crop region with adaptive geometry (no independent width/height stretch).
    Falls back to centered contain crop when bbox is absent.
    """
    if img_w <= 0 or img_h <= 0:
        raise ValueError("invalid image dimensions")

    if bbox is None:
        bbox = NormalizedBbox(left=0.0, top=0.0, width=1.0, height=1.0)

    pad_x = img_w * padding_ratio
    pad_y = img_h * padding_ratio
    bx = bbox.left * img_w
    by = bbox.top * img_h
    bw = max(1.0, bbox.width * img_w)
    bh = max(1.0, bbox.height * img_h)

    cx = bx + bw / 2.0
    cy = by + bh / 2.0

    crop_h = bh / target_fill
    crop_w = crop_h * target_aspect

    if crop_w < bw / target_fill:
        crop_w = bw / target_fill
        crop_h = crop_w / target_aspect

    crop_w = min(crop_w, img_w)
    crop_h = min(crop_h, img_h)

    if crop_w / crop_h > target_aspect:
        crop_w = crop_h * target_aspect
    else:
        crop_h = crop_w / target_aspect

    left = _clamp(cx - crop_w / 2.0, 0.0, img_w - crop_w)
    top = _clamp(cy - crop_h / 2.0, 0.0, img_h - crop_h)

    left = max(0.0, min(left, bx - pad_x))
    top = max(0.0, min(top, by - pad_y))
    right = min(img_w, max(left + crop_w, bx + bw + pad_x))
    bottom = min(img_h, max(top + crop_h, by + bh + pad_y))

    if right - left < 1 or bottom - top < 1:
        return CropBox(0, 0, img_w, img_h)

    current_aspect = (right - left) / (bottom - top)
    if current_aspect > target_aspect:
        new_w = (bottom - top) * target_aspect
        cx = (left + right) / 2.0
        left = _clamp(cx - new_w / 2.0, 0.0, img_w - new_w)
        right = left + new_w
    elif current_aspect < target_aspect:
        new_h = (right - left) / target_aspect
        cy = (top + bottom) / 2.0
        top = _clamp(cy - new_h / 2.0, 0.0, img_h - new_h)
        bottom = top + new_h

    return CropBox(
        left=int(round(left)),
        top=int(round(top)),
        right=int(round(min(img_w, right))),
        bottom=int(round(min(img_h, bottom))),
    )
