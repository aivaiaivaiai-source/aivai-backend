"""Conservative server-side photo enhance — no generative edits."""

from __future__ import annotations

import math
from dataclasses import dataclass

from PIL import Image, ImageEnhance

from app.core.config import Settings


@dataclass(frozen=True)
class EnhanceParams:
    brightness: float = 1.0
    contrast: float = 1.04
    saturation: float = 1.09
    sharpness: float = 1.02


def _sample_stats(image: Image.Image) -> tuple[float, float, float]:
    w, h = image.size
    step = max(1, max(w, h) // 120)
    sum_l = 0.0
    sum_l_sq = 0.0
    sum_sat = 0.0
    n = 0
    pixels = image.load()
    for y in range(0, h, step):
        for x in range(0, w, step):
            r, g, b = pixels[x, y][:3]
            luma = 0.299 * r + 0.587 * g + 0.114 * b
            sum_l += luma
            sum_l_sq += luma * luma
            max_c = max(r, g, b)
            min_c = min(r, g, b)
            sum_sat += 0.0 if max_c <= 0 else ((max_c - min_c) / max_c) * 255.0
            n += 1
    if n == 0:
        return 128.0, 50.0, 50.0
    mean = sum_l / n
    variance = max(0.0, sum_l_sq / n - mean * mean)
    return mean, math.sqrt(variance), sum_sat / n


def compute_enhance_params(image: Image.Image, settings: Settings) -> EnhanceParams:
    del settings
    mean_l, std_l, mean_sat = _sample_stats(image)
    brightness = 1.0
    contrast = 1.04
    saturation = 1.09
    sharpness = 1.02

    if mean_l < 70:
        brightness = 1.12
        contrast = 1.08
    elif mean_l < 100:
        brightness = 1.06
        contrast = 1.07
    elif mean_l > 205:
        brightness = 0.94
        contrast = 1.06
    elif mean_l > 178:
        brightness = 0.97
        contrast = 1.05

    if std_l < 28:
        contrast = max(contrast, 1.16)
    elif std_l < 40:
        contrast = max(contrast, 1.10)
    elif std_l > 70:
        contrast = min(contrast, 1.03)

    if mean_sat < 32:
        saturation = 1.18
    elif mean_sat < 50:
        saturation = 1.13
    elif mean_sat > 90:
        saturation = 1.04

    return EnhanceParams(
        brightness=max(0.93, min(1.14, brightness)),
        contrast=max(1.0, min(1.18, contrast)),
        saturation=max(1.0, min(1.19, saturation)),
        sharpness=max(1.0, min(1.08, sharpness)),
    )


def enhance_image(image: Image.Image, settings: Settings) -> Image.Image:
    params = compute_enhance_params(image, settings)
    if (
        abs(params.brightness - 1.0) < 0.01
        and abs(params.contrast - 1.0) < 0.01
        and abs(params.saturation - 1.0) < 0.01
        and abs(params.sharpness - 1.0) < 0.01
    ):
        return image.copy()

    out = image.copy()
    out = ImageEnhance.Brightness(out).enhance(params.brightness)
    out = ImageEnhance.Contrast(out).enhance(params.contrast)
    out = ImageEnhance.Color(out).enhance(params.saturation)
    out = ImageEnhance.Sharpness(out).enhance(params.sharpness)
    return out
