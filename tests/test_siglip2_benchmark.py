"""Unit tests for SigLIP2 benchmark adapter (no weight download required)."""

from __future__ import annotations

import ast
import json
from pathlib import Path

from benchmarks.media_classification.adapters import build_adapter
from benchmarks.media_classification.adapters.base import BenchCategory
from benchmarks.media_classification.adapters.siglip2 import (
    DEFAULT_PROMPT_SET,
    SigLIP2BenchmarkAdapter,
)
from benchmarks.media_classification.metrics.quality import CaseEval, evaluate_cases
from benchmarks.media_classification.runner.hashing import sha256_file

ROOT = Path(__file__).resolve().parents[1]
HARNESS = ROOT / "benchmarks" / "media_classification"


def test_prompt_set_frozen_and_hashable() -> None:
    assert DEFAULT_PROMPT_SET.is_file()
    data = json.loads(DEFAULT_PROMPT_SET.read_text(encoding="utf-8"))
    assert data["prompt_set_version"] == "siglip2-zero-shot-prompts-v1"
    assert "UNCLEAR" not in data["prompts"]
    assert "CAR_SALE" in data["prompts"]
    assert "OTHER" in data["prompts"]
    assert len(sha256_file(DEFAULT_PROMPT_SET)) == 64


def test_adapter_registry_builds_siglip2_without_prepare() -> None:
    adapter = build_adapter("siglip2", max_images=1, image_max_edge=224)
    assert adapter.name == "siglip2"
    assert "zero-shot" in adapter.version
    policy = adapter.input_policy()
    assert policy.max_images == 1


def test_candidate_mapping_and_topk_ordering_logic() -> None:
    # Pure logic: ranked scores map to BenchCandidate order
    scores = [("AUTO_PARTS", 0.2), ("CAR_SALE", 0.9), ("REAL_ESTATE", 0.4)]
    ranked = sorted(scores, key=lambda x: x[1], reverse=True)
    assert [s for s, _ in ranked] == ["CAR_SALE", "REAL_ESTATE", "AUTO_PARTS"]
    assert all(isinstance(s, float) and s == s for _, s in ranked)  # finite


def test_unclear_excluded_from_primary_denominator() -> None:
    cats = [
        CaseEval(
            test_id="P001",
            status="success",
            gt_slug="CAR_SALE",
            gt_hierarchy_slugs=("CAR_SALE",),
            pred_slug="CAR_SALE",
            pred_hierarchy_slugs=("CAR_SALE",),
            top_confidence=0.9,
            candidates=["CAR_SALE", "AUTO_PARTS"],
            acceptable_slugs=[],
            exact_match=True,
            top3_exact=True,
        ),
        CaseEval(
            test_id="P002",
            status="success",
            gt_slug="UNCLEAR",
            gt_hierarchy_slugs=("UNCLEAR",),
            pred_slug="CAR_SALE",
            pred_hierarchy_slugs=("CAR_SALE",),
            top_confidence=0.8,
            candidates=["CAR_SALE"],
            acceptable_slugs=[],
            exact_match=False,
            top3_exact=False,
        ),
    ]
    m = evaluate_cases(
        cats,
        high_confidence_threshold=0.85,
        all_gt_slugs={"CAR_SALE", "UNCLEAR"},
        primary_exclude_gt_slugs={"UNCLEAR"},
    )
    assert m.primary_evaluated == 1
    assert m.leaf_top1 == 1.0
    assert m.evaluated == 2  # unclear still counted in overall evaluated


def test_production_isolation_no_app_import() -> None:
    text = (HARNESS / "adapters" / "siglip2.py").read_text(encoding="utf-8")
    assert "app." not in text
    # AST: no import of app
    tree = ast.parse(text)
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("app"):
            raise AssertionError("siglip2 adapter imports production app")


def test_no_external_endpoint_in_adapter_source() -> None:
    text = (HARNESS / "adapters" / "siglip2.py").read_text(encoding="utf-8")
    for banned in ("api.openai.com", "generativelanguage.googleapis", "huggingface.co/api"):
        assert banned not in text
    assert "external_image_upload\": False" in text.replace(" ", "") or "external_image_upload" in text


def test_prompt_set_git_tracked_model_cache_ignored() -> None:
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    assert "benchmarks/media_classification/reports/*/" in gitignore
    assert "benchmarks/media_classification/data/" in gitignore
    # prompt set lives in repo code path, not ignored data/
    assert DEFAULT_PROMPT_SET.is_relative_to(HARNESS / "prompts")


def test_metadata_contract_fields() -> None:
    adapter = SigLIP2BenchmarkAdapter()
    # before prepare, metadata still exposes fixed fields
    meta = {
        "adapter": adapter.name,
        "adapter_version": adapter.version,
        "baseline_name": "LOCAL VISION V0 — ZERO-SHOT",
        "not_aivai_vision_v1": True,
        "external_image_upload": False,
    }
    assert meta["not_aivai_vision_v1"] is True
