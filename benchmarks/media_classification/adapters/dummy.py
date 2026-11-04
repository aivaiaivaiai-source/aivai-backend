"""Deterministic dummy adapter for harness wiring tests."""

from __future__ import annotations

import time

from benchmarks.media_classification.adapters.base import (
    AdapterClassifyResult,
    AdapterInputPolicy,
    BenchCandidate,
    BenchCategory,
)


class DummyDeterministicAdapter:
    """
    Predictable adapter: maps filename hints → catalog slug when present;
    otherwise returns no_match. Not a vision model.
    """

    def __init__(self, *, max_images: int = 3, target_max_edge: int | None = 640) -> None:
        self._max_images = max_images
        self._target_max_edge = target_max_edge
        self._prepared = False

    @property
    def name(self) -> str:
        return "dummy"

    @property
    def version(self) -> str:
        return "dummy-deterministic-v1"

    def input_policy(self) -> AdapterInputPolicy:
        return AdapterInputPolicy(
            max_images=self._max_images,
            target_max_edge=self._target_max_edge,
            cover_first=True,
            batch_strategy="sequential",
        )

    def prepare(self) -> None:
        self._prepared = True

    def classify(
        self,
        *,
        test_id: str,
        image_paths: list[str],
        allowed_categories: list[BenchCategory],
        ground_truth_slug: str | None = None,
    ) -> AdapterClassifyResult:
        del ground_truth_slug
        if not self._prepared:
            return AdapterClassifyResult(
                status="model_error",
                error_message="adapter not prepared",
            )
        t0 = time.perf_counter()
        by_slug = {c.slug: c for c in allowed_categories}
        used = image_paths[: max(1, self._max_images)]
        slug: str | None = None
        for path in used:
            lower = path.replace("\\", "/").lower()
            if "car-sale" in lower or "case_0001" in lower:
                slug = "transport-car-sale"
                break
            if "parts" in lower or "case_0002" in lower:
                slug = "transport-auto-parts"
                break
            if "phone" in lower or "case_0003" in lower:
                slug = "electronics-phones"
                break
        elapsed = (time.perf_counter() - t0) * 1000
        if slug is None or slug not in by_slug:
            return AdapterClassifyResult(
                status="no_match",
                candidates=[],
                images_used=len(used),
                image_paths_used=list(used),
                latency_ms=elapsed,
                inference_ms=elapsed,
            )
        cat = by_slug[slug]
        cand = BenchCandidate(
            category_id=cat.category_id,
            category_slug=cat.slug,
            category_name=cat.name,
            hierarchy_path=cat.hierarchy_path,
            confidence=0.91,
        )
        return AdapterClassifyResult(
            status="success",
            candidates=[cand],
            images_used=len(used),
            image_paths_used=list(used),
            latency_ms=elapsed,
            inference_ms=elapsed,
            raw_metadata={"hint": "filename_path"},
        )

    def close(self) -> None:
        self._prepared = False
