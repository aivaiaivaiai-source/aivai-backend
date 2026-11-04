"""Tests for Visual Evidence calibration policy (3C-2B)."""

from __future__ import annotations

from app.visual_evidence.calibration.decision_policy import (
    CalibrationConfig,
    apply_decision_policy,
    load_calibration_config,
)
from app.visual_evidence.calibration.prompt_utils import compute_prompt_hash, load_prompt_metadata


def test_prompt_hash_without_model_load() -> None:
    version, prompt_hash = load_prompt_metadata()
    assert version == "visual-evidence-prompts-v1"
    assert len(prompt_hash) == 16
    assert compute_prompt_hash() == prompt_hash


def test_calibration_config_loaded() -> None:
    cfg = load_calibration_config()
    assert cfg.calibration_version == "visual-evidence-calibration-v1"
    assert cfg.policy_family == "absolute_threshold"
    assert cfg.min_evidence_score == 0.01
    assert cfg.max_observations == 3


def test_absolute_threshold_accepts_expected_concept() -> None:
    cfg = CalibrationConfig(
        calibration_version="test",
        model_version="m",
        prompt_version="p",
        prompt_hash="h",
        policy_family="absolute_threshold",
        min_evidence_score=0.01,
        min_margin=0.0,
        max_observations=3,
        exclude_concepts=frozenset({"UNKNOWN_VISUAL"}),
        aggregation="max_score_per_concept",
    )
    scores = {
        "PASSENGER_CAR": 0.164,
        "TRUCK": 0.002,
        "UNKNOWN_VISUAL": 0.001,
    }
    decision = apply_decision_policy(scores, config=cfg)
    assert decision.no_match is False
    assert decision.accepted_concepts[0] == "PASSENGER_CAR"


def test_absolute_threshold_no_match_below_floor() -> None:
    cfg = load_calibration_config()
    scores = {"PASSENGER_CAR": 0.005, "TRUCK": 0.004}
    decision = apply_decision_policy(scores, config=cfg)
    assert decision.no_match is True
