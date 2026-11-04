"""ORACLE_TEST_ONLY — returns ground truth. Never a real benchmark candidate."""

from __future__ import annotations

import time

from benchmarks.media_classification.adapters.base import (
    AdapterClassifyResult,
    AdapterInputPolicy,
    BenchCandidate,
    BenchCategory,
)

ORACLE_NAME = "oracle"
ORACLE_BANNER = "ORACLE_TEST_ONLY"


class OracleTestOnlyAdapter:
    """
    Metrics self-check adapter: always emits ground_truth_slug as top-1.

    Must never be reported as a production/model shortlist candidate.
    """

    def __init__(self) -> None:
        self._prepared = False

    @property
    def name(self) -> str:
        return ORACLE_NAME

    @property
    def version(self) -> str:
        return f"{ORACLE_BANNER}-v1"

    def input_policy(self) -> AdapterInputPolicy:
        return AdapterInputPolicy(max_images=1, target_max_edge=None, cover_first=True)

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
        del test_id
        if not self._prepared:
            return AdapterClassifyResult(status="model_error", error_message="not prepared")
        t0 = time.perf_counter()
        if not ground_truth_slug:
            return AdapterClassifyResult(
                status="invalid_output",
                error_message="oracle requires ground_truth_slug",
            )
        by_slug = {c.slug: c for c in allowed_categories}
        cat = by_slug.get(ground_truth_slug)
        if cat is None:
            return AdapterClassifyResult(
                status="invalid_output",
                error_message=f"oracle GT slug not in catalog: {ground_truth_slug}",
            )
        used = image_paths[:1]
        elapsed = (time.perf_counter() - t0) * 1000
        return AdapterClassifyResult(
            status="success",
            candidates=[
                BenchCandidate(
                    category_id=cat.category_id,
                    category_slug=cat.slug,
                    category_name=cat.name,
                    hierarchy_path=cat.hierarchy_path,
                    confidence=1.0,
                )
            ],
            images_used=len(used),
            image_paths_used=list(used),
            latency_ms=elapsed,
            inference_ms=elapsed,
            raw_metadata={"adapter": ORACLE_BANNER},
        )

    def close(self) -> None:
        self._prepared = False
