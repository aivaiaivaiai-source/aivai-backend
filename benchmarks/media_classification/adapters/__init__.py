"""Adapter registry for the offline harness."""

from __future__ import annotations

from pathlib import Path

from benchmarks.media_classification.adapters.base import ClassifierAdapter
from benchmarks.media_classification.adapters.dummy import DummyDeterministicAdapter
from benchmarks.media_classification.adapters.oracle import OracleTestOnlyAdapter


def build_adapter(
    name: str,
    *,
    max_images: int = 3,
    image_max_edge: int | None = 640,
    prompt_set_path: Path | None = None,
    model_id: str | None = None,
    device: str | None = None,
    batch_size: int = 1,
) -> ClassifierAdapter:
    key = (name or "").strip().lower()
    if key == "dummy":
        return DummyDeterministicAdapter(
            max_images=max_images, target_max_edge=image_max_edge
        )
    if key == "oracle":
        return OracleTestOnlyAdapter()
    if key in {"siglip2", "siglip2-base"}:
        from benchmarks.media_classification.adapters.siglip2 import (
            DEFAULT_MODEL_ID,
            DEFAULT_PROMPT_SET,
            SigLIP2BenchmarkAdapter,
        )

        return SigLIP2BenchmarkAdapter(
            model_id=model_id or DEFAULT_MODEL_ID,
            prompt_set_path=prompt_set_path or DEFAULT_PROMPT_SET,
            max_images=max_images,
            target_max_edge=image_max_edge if image_max_edge else 224,
            device=device,
            batch_size=batch_size,
        )
    raise ValueError(
        f"Unknown adapter '{name}'. Available: dummy, oracle (ORACLE_TEST_ONLY), siglip2."
    )


__all__ = (
    "build_adapter",
    "DummyDeterministicAdapter",
    "OracleTestOnlyAdapter",
)
