from __future__ import annotations

from app.services.focus_bbox_detection import (
    FocusBBoxResult,
    NormalizedBbox,
    RawDetection,
    focus_result_from_detections,
    pick_primary,
)


def _det(label: str, score: float, area: float) -> RawDetection:
    side = area**0.5
    return RawDetection(
        label=label,
        score=score,
        bbox=NormalizedBbox(left=0.1, top=0.1, width=side, height=side),
    )


def test_pick_primary_prefers_car_over_larger_bus() -> None:
    detections = [
        _det("bus", 0.95, 0.40),
        _det("car", 0.90, 0.25),
    ]
    primary = pick_primary(detections)
    assert primary is not None
    assert primary.label == "car"


def test_focus_result_returns_null_for_low_confidence() -> None:
    detections = [_det("car", 0.20, 0.30)]
    assert focus_result_from_detections(detections) is None


def test_focus_result_returns_bbox_for_valid_car() -> None:
    detections = [_det("car", 0.96, 0.28)]
    result = focus_result_from_detections(detections)
    assert isinstance(result, FocusBBoxResult)
    assert result.confidence == 0.96
    assert 0.0 < result.width < 1.0


def test_focus_result_rejects_dominant_non_vehicle() -> None:
    detections = [
        _det("person", 0.94, 0.30),
        _det("car", 0.70, 0.20),
    ]
    assert focus_result_from_detections(detections) is None
