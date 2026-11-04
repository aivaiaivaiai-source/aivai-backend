"""Pure focus-bbox selection rules (RT-DETR output → stored bbox)."""

from __future__ import annotations

from dataclasses import dataclass

VEHICLE_LABELS = frozenset({"car", "truck", "bus", "motorcycle"})
CAR_SALE_CATEGORY_SLUGS = frozenset({"transport-car-sale"})

MIN_PRIMARY_CONF = 0.35
MIN_ANY_VEHICLE_CONF = 0.25
GOOD_AREA_MIN = 0.05
GOOD_AREA_MAX = 0.85
DETECTION_THRESHOLD = 0.25


@dataclass(frozen=True)
class NormalizedBbox:
    left: float
    top: float
    width: float
    height: float

    @property
    def area_ratio(self) -> float:
        return self.width * self.height


@dataclass(frozen=True)
class RawDetection:
    label: str
    score: float
    bbox: NormalizedBbox


@dataclass(frozen=True)
class FocusBBoxResult:
    left: float
    top: float
    width: float
    height: float
    confidence: float


def box_to_norm(box: dict[str, float], width: int, height: int) -> NormalizedBbox:
    x1 = max(0.0, float(box["xmin"]))
    y1 = max(0.0, float(box["ymin"]))
    x2 = min(float(width), float(box["xmax"]))
    y2 = min(float(height), float(box["ymax"]))
    bw = max(1.0, x2 - x1)
    bh = max(1.0, y2 - y1)
    return NormalizedBbox(
        left=x1 / width,
        top=y1 / height,
        width=bw / width,
        height=bh / height,
    )


def pick_primary(detections: list[RawDetection]) -> RawDetection | None:
    def best(pool: list[RawDetection]) -> RawDetection | None:
        if not pool:
            return None
        return max(pool, key=lambda item: (item.bbox.area_ratio, item.score))

    cars = [
        item
        for item in detections
        if item.label == "car" and item.score >= MIN_PRIMARY_CONF
    ]
    picked = best(cars)
    if picked is not None:
        return picked

    vehicles = [
        item
        for item in detections
        if item.label in VEHICLE_LABELS and item.score >= MIN_PRIMARY_CONF
    ]
    return best(vehicles)


def focus_result_from_detections(
    detections: list[RawDetection],
    *,
    min_confidence: float = MIN_PRIMARY_CONF,
) -> FocusBBoxResult | None:
    primary = pick_primary(detections)
    if primary is None:
        return None
    if primary.score < min_confidence:
        return None
    if primary.label not in VEHICLE_LABELS:
        return None
    if not (GOOD_AREA_MIN <= primary.bbox.area_ratio <= GOOD_AREA_MAX):
        return None

    non_vehicle = [
        item
        for item in detections
        if item.label not in VEHICLE_LABELS and item.score >= 0.55
    ]
    if non_vehicle and non_vehicle[0].score > primary.score + 0.15:
        return None

    return FocusBBoxResult(
        left=primary.bbox.left,
        top=primary.bbox.top,
        width=primary.bbox.width,
        height=primary.bbox.height,
        confidence=primary.score,
    )
