"""Versioned Visual Evidence decision policy (post-inference, CPU-only)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

CALIBRATION_DIR = Path(__file__).resolve().parent
DEFAULT_CALIBRATION_PATH = CALIBRATION_DIR / "visual_evidence_calibration_v1.json"

EXCLUDED_FROM_OBSERVATIONS = frozenset({"UNKNOWN_VISUAL"})


@dataclass(frozen=True)
class PolicyDecision:
    accepted_concepts: tuple[str, ...]
    evidence_scores: tuple[float, ...]
    no_match: bool
    policy_family: str
    notes: str = ""


@dataclass(frozen=True)
class CalibrationConfig:
    calibration_version: str
    model_version: str
    prompt_version: str
    prompt_hash: str
    policy_family: str
    min_evidence_score: float
    min_margin: float
    max_observations: int
    exclude_concepts: frozenset[str]
    aggregation: str
    dataset_version: str | None = None
    mapping_version: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CalibrationConfig:
        policy = data.get("policy") or {}
        return cls(
            calibration_version=str(data["calibration_version"]),
            model_version=str(data["model_version"]),
            prompt_version=str(data["prompt_version"]),
            prompt_hash=str(data.get("prompt_hash") or ""),
            policy_family=str(policy.get("family") or "absolute_threshold"),
            min_evidence_score=float(policy.get("min_evidence_score", 0.0)),
            min_margin=float(policy.get("min_margin", 0.0)),
            max_observations=int(policy.get("max_observations", 3)),
            exclude_concepts=frozenset(policy.get("exclude_concepts") or ["UNKNOWN_VISUAL"]),
            aggregation=str(data.get("aggregation") or "max_score_per_concept"),
            dataset_version=data.get("dataset_version"),
            mapping_version=data.get("mapping_version"),
        )


def load_calibration_config(path: Path = DEFAULT_CALIBRATION_PATH) -> CalibrationConfig:
    data = json.loads(path.read_text(encoding="utf-8"))
    return CalibrationConfig.from_dict(data)


def rank_scores(scores: dict[str, float]) -> list[tuple[str, float]]:
    return sorted(scores.items(), key=lambda kv: kv[1], reverse=True)


def apply_decision_policy(
    scores: dict[str, float],
    *,
    config: CalibrationConfig,
) -> PolicyDecision:
    """Apply frozen calibration policy to raw per-concept evidence_scores."""
    ranked = [
        (concept, score)
        for concept, score in rank_scores(scores)
        if concept not in config.exclude_concepts and score > 0.0
    ]
    if not ranked:
        return PolicyDecision((), (), True, config.policy_family, notes="empty_scores")

    family = config.policy_family
    accepted: list[tuple[str, float]] = []

    if family == "absolute_threshold":
        for concept, score in ranked:
            if score >= config.min_evidence_score:
                accepted.append((concept, score))
            if len(accepted) >= config.max_observations:
                break
    elif family in ("top1_margin", "margin_oriented"):
        top1_concept, top1_score = ranked[0]
        top2_score = ranked[1][1] if len(ranked) > 1 else 0.0
        margin = top1_score - top2_score
        if top1_score >= config.min_evidence_score and margin >= config.min_margin:
            accepted.append((top1_concept, top1_score))
        # Also accept additional ranks if they pass absolute floor and pairwise margin
        for i in range(1, min(len(ranked), config.max_observations)):
            concept, score = ranked[i]
            prev_score = ranked[i - 1][1]
            if score >= config.min_evidence_score and (prev_score - score) >= config.min_margin:
                accepted.append((concept, score))
    elif family == "per_concept_threshold":
        thresholds: dict[str, float] = {}
        # Loaded externally; fallback to global min
        for concept, score in ranked:
            floor = thresholds.get(concept, config.min_evidence_score)
            if score >= floor:
                accepted.append((concept, score))
            if len(accepted) >= config.max_observations:
                break
    else:
        raise ValueError(f"unknown policy family: {family}")

    if not accepted:
        return PolicyDecision(
            (),
            (),
            True,
            family,
            notes=f"no_concept_passed family={family}",
        )

    return PolicyDecision(
        tuple(c for c, _ in accepted),
        tuple(s for _, s in accepted),
        False,
        family,
    )


def aggregate_multi_image_scores(
    per_image: list[dict[str, float]],
    *,
    config: CalibrationConfig,
) -> dict[str, float]:
    """Max-score aggregation across inspected images (production-equivalent)."""
    del config  # reserved for future aggregation variants
    merged: dict[str, float] = {}
    for scores in per_image:
        for concept, score in scores.items():
            prev = merged.get(concept, 0.0)
            if score > prev:
                merged[concept] = score
    return merged
