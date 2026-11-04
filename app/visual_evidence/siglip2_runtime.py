"""Resident SigLIP2 runtime — loaded once per worker process."""

from __future__ import annotations

import json
import logging
import threading
import time
from pathlib import Path
from typing import Any

from app.visual_evidence.calibration.prompt_utils import compute_prompt_hash

logger = logging.getLogger(__name__)

PACKAGE_ROOT = Path(__file__).resolve().parent
DEFAULT_PROMPT_SET = PACKAGE_ROOT / "prompts" / "visual_evidence_prompts_v1.json"
DEFAULT_MODEL_ID = "google/siglip2-base-patch16-224"
MODEL_VERSION = "local-visual-evidence-v0-siglip2-base"
PROMPT_VERSION = "visual-evidence-prompts-v1"

_lock = threading.Lock()
_runtime: SigLIP2ModelRuntime | None = None


class SigLIP2ModelRuntime:
    def __init__(
        self,
        *,
        model_id: str = DEFAULT_MODEL_ID,
        prompt_set_path: Path = DEFAULT_PROMPT_SET,
    ) -> None:
        self._model_id = model_id
        self._prompt_set_path = Path(prompt_set_path)
        self._model = None
        self._processor = None
        self._device = "cpu"
        self._prompt_set: dict[str, Any] = {}
        self._prompt_hash = compute_prompt_hash(self._prompt_set_path)
        self._concept_order: list[str] = []
        self._prepared = False

    @property
    def model_version(self) -> str:
        return MODEL_VERSION

    @property
    def prompt_version(self) -> str:
        return PROMPT_VERSION

    @property
    def prompt_hash(self) -> str:
        return self._prompt_hash

    def prepare(self) -> None:
        if self._prepared:
            return
        if not self._prompt_set_path.is_file():
            raise FileNotFoundError(f"prompt set missing: {self._prompt_set_path}")
        raw = self._prompt_set_path.read_text(encoding="utf-8")
        self._prompt_set = json.loads(raw)
        self._prompt_hash = compute_prompt_hash(self._prompt_set_path)
        if self._prompt_set.get("prompt_set_version") != PROMPT_VERSION:
            raise RuntimeError("unexpected prompt_set_version — refuse silent drift")
        concepts = self._prompt_set.get("concepts") or {}
        self._concept_order = list(concepts.keys())

        import torch
        from transformers import AutoModel, AutoProcessor

        if torch.cuda.is_available():
            self._device = "cuda"
        else:
            self._device = "cpu"
        dtype = torch.float16 if self._device == "cuda" else torch.float32

        t0 = time.perf_counter()
        self._processor = AutoProcessor.from_pretrained(self._model_id)
        self._model = AutoModel.from_pretrained(self._model_id)
        self._model.to(self._device, dtype=dtype)
        self._model.eval()
        load_ms = (time.perf_counter() - t0) * 1000
        logger.info(
            "siglip2_runtime_ready device=%s load_ms=%.0f model=%s prompt=%s",
            self._device,
            load_ms,
            self._model_id,
            self._prompt_hash,
        )
        self._prepared = True

    def score_image_bytes(self, image_bytes: bytes) -> dict[str, float]:
        if not self._prepared:
            self.prepare()

        import io

        import torch
        from PIL import Image

        concepts: dict[str, str] = dict(self._prompt_set["concepts"])
        texts = [concepts[c] for c in self._concept_order]
        with Image.open(io.BytesIO(image_bytes)) as im:
            image = im.convert("RGB")
            image.thumbnail((896, 896))

        inputs = self._processor(
            text=texts,
            images=image,
            padding="max_length",
            return_tensors="pt",
        )
        inputs = {k: v.to(self._device) for k, v in inputs.items()}
        with torch.no_grad():
            outputs = self._model(**inputs)
            logits = outputs.logits_per_image.squeeze(0)
            scores = torch.sigmoid(logits).detach().float().cpu()
        score_list = [float(x) for x in scores.tolist()]
        return dict(zip(self._concept_order, score_list, strict=True))


def get_siglip2_runtime() -> SigLIP2ModelRuntime:
    global _runtime
    if _runtime is not None:
        return _runtime
    with _lock:
        if _runtime is None:
            _runtime = SigLIP2ModelRuntime()
        return _runtime


def reset_siglip2_runtime_for_tests() -> None:
    global _runtime
    with _lock:
        _runtime = None
