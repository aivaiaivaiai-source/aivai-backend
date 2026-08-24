"""RT-DETR focus bbox detector (Apache-2.0, sync inference)."""

from __future__ import annotations

from io import BytesIO
from typing import Protocol

from PIL import Image, ImageOps

from app.services.focus_bbox_detection import (
    DETECTION_THRESHOLD,
    FocusBBoxResult,
    RawDetection,
    box_to_norm,
    focus_result_from_detections,
)


class FocusBBoxDetector(Protocol):
    def detect(self, content: bytes, content_type: str) -> FocusBBoxResult | None: ...


class NullFocusBBoxDetector:
    def detect(self, content: bytes, content_type: str) -> FocusBBoxResult | None:
        return None


class RtDetrFocusBBoxDetector:
    """Lazy-loaded RT-DETR pipeline; one instance per process."""

    def __init__(
        self,
        model_id: str,
        *,
        min_confidence: float,
        device: str = "cpu",
        inference_max_edge: int = 1280,
    ) -> None:
        self._model_id = model_id
        self._min_confidence = min_confidence
        self._device = device
        self._inference_max_edge = inference_max_edge
        self._pipeline = None

    def _get_pipeline(self):
        if self._pipeline is None:
            from transformers import pipeline

            self._pipeline = pipeline(
                "object-detection",
                model=self._model_id,
                device=self._device,
            )
        return self._pipeline

    def _prepare_inference_image(self, image: Image.Image) -> Image.Image:
        w, h = image.size
        long_edge = max(w, h)
        if long_edge <= self._inference_max_edge:
            return image
        scale = self._inference_max_edge / long_edge
        nw = max(1, int(w * scale))
        nh = max(1, int(h * scale))
        return image.resize((nw, nh), Image.Resampling.BILINEAR)

    def detect_image(self, image: Image.Image) -> FocusBBoxResult | None:
        infer = self._prepare_inference_image(image)
        width, height = image.size
        raw = self._get_pipeline()(infer, threshold=DETECTION_THRESHOLD)
        scale_x = width / infer.width
        scale_y = height / infer.height
        detections = []
        for row in raw:
            box = row["box"]
            norm = box_to_norm(
                {
                    "xmin": float(box["xmin"]) * scale_x,
                    "ymin": float(box["ymin"]) * scale_y,
                    "xmax": float(box["xmax"]) * scale_x,
                    "ymax": float(box["ymax"]) * scale_y,
                },
                width,
                height,
            )
            detections.append(
                RawDetection(
                    label=str(row["label"]),
                    score=float(row["score"]),
                    bbox=norm,
                ),
            )
        return focus_result_from_detections(
            detections,
            min_confidence=self._min_confidence,
        )

    def detect(self, content: bytes, content_type: str) -> FocusBBoxResult | None:
        del content_type
        image = Image.open(BytesIO(content)).convert("RGB")
        image = ImageOps.exif_transpose(image)
        return self.detect_image(image)
