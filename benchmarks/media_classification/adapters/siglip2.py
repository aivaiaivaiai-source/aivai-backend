"""SigLIP2 Base zero-shot offline benchmark adapter (3B-3).

LOCAL VISION V0 — ZERO-SHOT baseline only.
Not production MediaCategoryClassifier. No external image upload.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from benchmarks.media_classification.adapters.base import (
    AdapterClassifyResult,
    AdapterInputPolicy,
    BenchCandidate,
    BenchCategory,
)
from benchmarks.media_classification.runner.hashing import sha256_file

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROMPT_SET = (
    PACKAGE_ROOT / "prompts" / "siglip2_zero_shot_prompts_v1.json"
)
DEFAULT_MODEL_ID = "google/siglip2-base-patch16-224"
ADAPTER_VERSION = "siglip2-base-zero-shot-v0"


class SigLIP2BenchmarkAdapter:
    """Zero-shot image-text similarity via official SigLIP2 Base checkpoint."""

    def __init__(
        self,
        *,
        model_id: str = DEFAULT_MODEL_ID,
        prompt_set_path: Path = DEFAULT_PROMPT_SET,
        max_images: int = 1,
        target_max_edge: int | None = 224,
        device: str | None = None,
        batch_size: int = 1,
    ) -> None:
        self._model_id = model_id
        self._prompt_set_path = Path(prompt_set_path)
        self._max_images = max(1, min(9, max_images))
        self._target_max_edge = target_max_edge
        self._batch_size = max(1, batch_size)
        self._device_override = device
        self._model = None
        self._processor = None
        self._device = "cpu"
        self._dtype_name = "float32"
        self._prompt_set: dict[str, Any] = {}
        self._prompt_hash = ""
        self._model_revision: str | None = None
        self._prepared = False
        self._load_ms: float | None = None
        self._warmup_ms: float | None = None
        self._download_note = "weights via huggingface hub cache (official google/*)"

    @property
    def name(self) -> str:
        return "siglip2"

    @property
    def version(self) -> str:
        return ADAPTER_VERSION

    def input_policy(self) -> AdapterInputPolicy:
        return AdapterInputPolicy(
            max_images=self._max_images,
            target_max_edge=self._target_max_edge,
            cover_first=True,
            batch_strategy=f"sequential_bs{self._batch_size}",
        )

    def metadata(self) -> dict[str, Any]:
        return {
            "adapter": self.name,
            "adapter_version": self.version,
            "model_id": self._model_id,
            "model_revision": self._model_revision,
            "publisher": "Google",
            "license": "apache-2.0",
            "download_source": "https://huggingface.co/google/siglip2-base-patch16-224",
            "prompt_set_version": self._prompt_set.get("prompt_set_version"),
            "prompt_set_hash": self._prompt_hash,
            "prompt_set_path": str(self._prompt_set_path),
            "device": self._device,
            "dtype": self._dtype_name,
            "batch_size": self._batch_size,
            "input_resolution": 224,
            "score_semantics": "siglip_sigmoid_similarity_NOT_calibrated_probability",
            "external_image_upload": False,
            "load_ms": self._load_ms,
            "warmup_ms": self._warmup_ms,
            "baseline_name": "LOCAL VISION V0 — ZERO-SHOT",
            "not_aivai_vision_v1": True,
        }

    def prepare(self) -> None:
        if self._prepared:
            return

        if not self._prompt_set_path.is_file():
            raise FileNotFoundError(f"prompt set missing: {self._prompt_set_path}")
        self._prompt_set = json.loads(
            self._prompt_set_path.read_text(encoding="utf-8")
        )
        self._prompt_hash = sha256_file(self._prompt_set_path)
        if self._prompt_set.get("prompt_set_version") != "siglip2-zero-shot-prompts-v1":
            raise RuntimeError("unexpected prompt_set_version — refuse silent drift")

        import torch
        from transformers import AutoModel, AutoProcessor

        if self._device_override:
            self._device = self._device_override
        elif torch.cuda.is_available():
            self._device = "cuda"
        else:
            self._device = "cpu"

        self._dtype_name = "float16" if self._device == "cuda" else "float32"
        dtype = torch.float16 if self._device == "cuda" else torch.float32

        t0 = time.perf_counter()
        self._processor = AutoProcessor.from_pretrained(self._model_id)
        self._model = AutoModel.from_pretrained(self._model_id)
        self._model.to(self._device, dtype=dtype)
        self._model.eval()
        self._load_ms = (time.perf_counter() - t0) * 1000

        # Best-effort revision from hub cache
        try:
            from huggingface_hub import model_info

            info = model_info(self._model_id)
            self._model_revision = getattr(info, "sha", None)
        except Exception:
            self._model_revision = None

        # Warmup with solid color to separate cold start
        from PIL import Image

        warm = Image.new("RGB", (224, 224), (120, 120, 120))
        texts = list(self._prompt_set["prompts"].values())[:3]
        tw = time.perf_counter()
        inputs = self._processor(
            text=texts,
            images=warm,
            padding="max_length",
            return_tensors="pt",
        )
        inputs = {k: v.to(self._device) for k, v in inputs.items()}
        with torch.no_grad():
            _ = self._model(**inputs)
        if self._device == "cuda":
            torch.cuda.synchronize()
        self._warmup_ms = (time.perf_counter() - tw) * 1000
        self._prepared = True

    def classify(
        self,
        *,
        test_id: str,
        image_paths: list[str],
        allowed_categories: list[BenchCategory],
        ground_truth_slug: str | None = None,
    ) -> AdapterClassifyResult:
        del ground_truth_slug  # never used for prediction (no leakage)
        if not self._prepared:
            self.prepare()

        import math

        import torch
        from PIL import Image

        t0 = time.perf_counter()
        if not image_paths:
            return AdapterClassifyResult(
                status="invalid_output",
                error_message="no image paths",
            )

        path = image_paths[0]
        try:
            with Image.open(path) as im:
                image = im.convert("RGB")
                if self._target_max_edge and max(image.size) > self._target_max_edge:
                    # processor also resizes; keep bounded decode memory
                    image.thumbnail(
                        (self._target_max_edge * 4, self._target_max_edge * 4)
                    )
                image.load()
        except Exception as exc:  # noqa: BLE001
            return AdapterClassifyResult(
                status="model_error",
                error_message=f"image open failed: {exc}"[:400],
            )

        prompts_map: dict[str, str] = dict(self._prompt_set["prompts"])
        exclude = set(self._prompt_set.get("exclude_from_candidates") or [])
        # Intersection: catalog-active ∩ prompt keys − UNCLEAR
        by_slug = {c.slug: c for c in allowed_categories if c.is_active}
        ordered_slugs = [
            s
            for s in prompts_map
            if s in by_slug and s not in exclude
        ]
        if not ordered_slugs:
            return AdapterClassifyResult(
                status="invalid_output",
                error_message="no overlapping prompt/catalog categories",
            )

        texts = [prompts_map[s] for s in ordered_slugs]
        prep_t0 = time.perf_counter()
        inputs = self._processor(
            text=texts,
            images=image,
            padding="max_length",
            return_tensors="pt",
        )
        inputs = {k: v.to(self._device) for k, v in inputs.items()}
        preprocess_ms = (time.perf_counter() - prep_t0) * 1000

        inf_t0 = time.perf_counter()
        try:
            with torch.no_grad():
                outputs = self._model(**inputs)
                # SigLIP / SigLIP2: sigmoid over image-text logits (not softmax)
                logits = outputs.logits_per_image.squeeze(0)
                scores = torch.sigmoid(logits).detach().float().cpu()
        except Exception as exc:  # noqa: BLE001
            return AdapterClassifyResult(
                status="model_error",
                error_message=str(exc)[:500],
                preprocess_ms=preprocess_ms,
            )
        if self._device == "cuda":
            torch.cuda.synchronize()
        inference_ms = (time.perf_counter() - inf_t0) * 1000

        score_list = [float(x) for x in scores.tolist()]
        if any(not math.isfinite(s) for s in score_list):
            return AdapterClassifyResult(
                status="invalid_output",
                error_message="non-finite similarity scores",
                preprocess_ms=preprocess_ms,
                inference_ms=inference_ms,
            )

        ranked = sorted(
            zip(ordered_slugs, score_list, strict=True),
            key=lambda x: x[1],
            reverse=True,
        )
        candidates: list[BenchCandidate] = []
        for slug, score in ranked[:5]:
            cat = by_slug[slug]
            candidates.append(
                BenchCandidate(
                    category_id=cat.category_id,
                    category_slug=cat.slug,
                    category_name=cat.name,
                    hierarchy_path=cat.hierarchy_path,
                    confidence=float(score),
                )
            )

        top1 = ranked[0][1] if ranked else None
        top2 = ranked[1][1] if len(ranked) > 1 else None
        margin = (top1 - top2) if top1 is not None and top2 is not None else None

        latency_ms = (time.perf_counter() - t0) * 1000
        rss_mb = None
        try:
            import psutil

            rss_mb = psutil.Process().memory_info().rss / (1024 * 1024)
        except Exception:
            pass

        cuda_alloc = cuda_res = cuda_peak = None
        if self._device == "cuda":
            cuda_alloc = torch.cuda.memory_allocated() / (1024 * 1024)
            cuda_res = torch.cuda.memory_reserved() / (1024 * 1024)
            cuda_peak = torch.cuda.max_memory_allocated() / (1024 * 1024)

        return AdapterClassifyResult(
            status="success",
            candidates=candidates,
            images_used=1,
            image_paths_used=[path],
            latency_ms=latency_ms,
            preprocess_ms=preprocess_ms,
            inference_ms=inference_ms,
            rss_mb=rss_mb,
            cuda_allocated_mb=cuda_alloc,
            cuda_reserved_mb=cuda_res,
            cuda_peak_mb=cuda_peak,
            raw_metadata={
                "top1_score": top1,
                "top2_score": top2,
                "margin": margin,
                "score_semantics": "siglip_sigmoid_similarity_NOT_calibrated_probability",
                "model_id": self._model_id,
                "prompt_set_version": self._prompt_set.get("prompt_set_version"),
                "external_image_upload": False,
                "test_id": test_id,
            },
        )

    def close(self) -> None:
        self._model = None
        self._processor = None
        self._prepared = False
        try:
            import torch

            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except Exception:
            pass
