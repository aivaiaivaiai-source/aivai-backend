"""Benchmark ClassifierAdapter contract — framework-agnostic."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


@dataclass(frozen=True)
class BenchCategory:
    category_id: int
    slug: str
    name: str
    parent_id: int | None
    hierarchy_path: tuple[str, ...]  # root → leaf labels
    is_active: bool = True


@dataclass(frozen=True)
class BenchCandidate:
    category_id: int
    category_slug: str
    category_name: str
    hierarchy_path: tuple[str, ...]
    confidence: float

    def to_json(self) -> dict[str, Any]:
        return {
            "category_id": self.category_id,
            "category_slug": self.category_slug,
            "category_name": self.category_name,
            "hierarchy_path": list(self.hierarchy_path),
            "confidence": float(self.confidence),
        }


@dataclass
class AdapterInputPolicy:
    max_images: int = 3
    target_max_edge: int | None = None
    cover_first: bool = True
    batch_strategy: str = "sequential"


@dataclass
class AdapterClassifyResult:
    status: str  # success | no_match | timeout | model_error | invalid_output | skipped
    candidates: list[BenchCandidate] = field(default_factory=list)
    images_used: int = 0
    image_paths_used: list[str] = field(default_factory=list)
    latency_ms: float = 0.0
    preprocess_ms: float = 0.0
    inference_ms: float = 0.0
    error_message: str | None = None
    raw_metadata: dict[str, Any] = field(default_factory=dict)
    # Optional future cost hooks (N/A unless provider reports)
    input_tokens: int | None = None
    output_tokens: int | None = None
    image_tokens: int | None = None
    request_cost_usd: float | None = None
    provider_request_id: str | None = None
    # Optional resource hooks
    rss_mb: float | None = None
    peak_rss_mb: float | None = None
    cuda_allocated_mb: float | None = None
    cuda_reserved_mb: float | None = None
    cuda_peak_mb: float | None = None


@runtime_checkable
class ClassifierAdapter(Protocol):
    @property
    def name(self) -> str: ...

    @property
    def version(self) -> str: ...

    def input_policy(self) -> AdapterInputPolicy: ...

    def prepare(self) -> None: ...

    def classify(
        self,
        *,
        test_id: str,
        image_paths: list[str],
        allowed_categories: list[BenchCategory],
        ground_truth_slug: str | None = None,
    ) -> AdapterClassifyResult: ...

    def close(self) -> None: ...
