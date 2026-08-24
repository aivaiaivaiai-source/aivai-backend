"""Centralized media variant specifications and encoding."""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO

from PIL import Image

from app.core.config import Settings
from app.media_engine.framing import CropBox, compute_crop_box, normalized_bbox_from_focus
from app.services.focus_bbox_detection import FocusBBoxResult, NormalizedBbox

# AiVai portrait media aspect — shared by detail hero (430×573) and feed card
# (209×279; Δaspect ≈ 0.18% vs hero, negligible at cover fit).
HERO_ASPECT = 430.0 / 573.0
FEED_ASPECT = HERO_ASPECT
THUMB_ASPECT = 1.0

# Figma feed card container (logical px) — for tests / documentation alignment.
FEED_CONTAINER_ASPECT = 209.0 / 279.0


@dataclass(frozen=True)
class MediaVariantSpec:
    name: str
    long_edge: int
    aspect: float  # width / height


@dataclass(frozen=True)
class VariantOutput:
    name: str
    content: bytes
    width: int
    height: int


def variant_specs(settings: Settings) -> tuple[MediaVariantSpec, ...]:
    return (
        MediaVariantSpec(
            "display",
            settings.MEDIA_ENGINE_DISPLAY_LONG_EDGE,
            HERO_ASPECT,
        ),
        MediaVariantSpec(
            "feed",
            settings.MEDIA_ENGINE_FEED_LONG_EDGE,
            FEED_ASPECT,
        ),
        MediaVariantSpec(
            "thumb",
            settings.MEDIA_ENGINE_THUMB_LONG_EDGE,
            THUMB_ASPECT,
        ),
    )


def _output_dimensions(spec: MediaVariantSpec) -> tuple[int, int]:
    if spec.aspect >= 1.0:
        w = spec.long_edge
        h = max(1, int(round(spec.long_edge / spec.aspect)))
    else:
        h = spec.long_edge
        w = max(1, int(round(spec.long_edge * spec.aspect)))
    return w, h


def _encode_jpeg(image: Image.Image, *, quality: int) -> bytes:
    buf = BytesIO()
    image.save(
        buf,
        format="JPEG",
        quality=quality,
        optimize=True,
        subsampling="4:2:0",
    )
    return buf.getvalue()


def render_variant(
    source: Image.Image,
    spec: MediaVariantSpec,
    *,
    bbox: NormalizedBbox | None,
    jpeg_quality: int,
) -> VariantOutput:
    out_w, out_h = _output_dimensions(spec)
    crop = compute_crop_box(
        source.width,
        source.height,
        target_aspect=spec.aspect,
        bbox=bbox,
    )
    cropped = source.crop((crop.left, crop.top, crop.right, crop.bottom))
    resized = cropped.resize((out_w, out_h), Image.Resampling.LANCZOS)
    content = _encode_jpeg(resized, quality=jpeg_quality)
    return VariantOutput(name=spec.name, content=content, width=out_w, height=out_h)


def bbox_from_focus(focus: FocusBBoxResult | None) -> NormalizedBbox | None:
    if focus is None:
        return None
    return normalized_bbox_from_focus(
        focus.left,
        focus.top,
        focus.width,
        focus.height,
    )


def encode_all_variants(
    source: Image.Image,
    *,
    focus: FocusBBoxResult | None,
    settings: Settings,
) -> list[VariantOutput]:
    bbox = bbox_from_focus(focus)
    quality = settings.MEDIA_ENGINE_JPEG_QUALITY
    return [
        render_variant(source, spec, bbox=bbox, jpeg_quality=quality)
        for spec in variant_specs(settings)
    ]
