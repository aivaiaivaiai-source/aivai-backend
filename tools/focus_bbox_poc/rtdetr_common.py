"""Shared RT-DETR POC helpers (offline, Apache-2.0 model)."""

from __future__ import annotations

from dataclasses import dataclass

from PIL import Image, ImageDraw

MODEL_ID = "PekingU/rtdetr_r18vd_coco_o365"
MODEL_LICENSE = "Apache-2.0"

VEHICLE_LABELS = {"car", "truck", "bus", "motorcycle"}
MIN_PRIMARY_CONF = 0.35
MIN_ANY_VEHICLE_CONF = 0.25
GOOD_AREA_MIN = 0.05
GOOD_AREA_MAX = 0.85
IOU_CORRECT = 0.45
IOU_MISS = 0.15


@dataclass
class BboxNorm:
    left: float
    top: float
    width: float
    height: float

    @property
    def area_ratio(self) -> float:
        return self.width * self.height

    @property
    def right(self) -> float:
        return self.left + self.width

    @property
    def bottom(self) -> float:
        return self.top + self.height


@dataclass
class DetectionRow:
    label: str
    score: float
    bbox: BboxNorm


def box_to_norm(box: dict, w: int, h: int) -> BboxNorm:
    x1 = max(0.0, float(box["xmin"]))
    y1 = max(0.0, float(box["ymin"]))
    x2 = min(float(w), float(box["xmax"]))
    y2 = min(float(h), float(box["ymax"]))
    bw = max(1.0, x2 - x1)
    bh = max(1.0, y2 - y1)
    return BboxNorm(left=x1 / w, top=y1 / h, width=bw / w, height=bh / h)


def coco_xywh_to_norm(x: float, y: float, bw: float, bh: float, w: int, h: int) -> BboxNorm:
    return BboxNorm(left=x / w, top=y / h, width=bw / w, height=bh / h)


def iou(a: BboxNorm, b: BboxNorm) -> float:
    ix1 = max(a.left, b.left)
    iy1 = max(a.top, b.top)
    ix2 = min(a.right, b.right)
    iy2 = min(a.bottom, b.bottom)
    iw = max(0.0, ix2 - ix1)
    ih = max(0.0, iy2 - iy1)
    inter = iw * ih
    if inter <= 0:
        return 0.0
    union = a.area_ratio + b.area_ratio - inter
    return inter / union if union > 0 else 0.0


def pick_primary(detections: list[DetectionRow]) -> DetectionRow | None:
    def best(pool: list[DetectionRow]) -> DetectionRow | None:
        if not pool:
            return None
        return max(pool, key=lambda d: (d.bbox.area_ratio, d.score))

    cars = [d for d in detections if d.label == "car" and d.score >= MIN_PRIMARY_CONF]
    picked = best(cars)
    if picked is not None:
        return picked

    vehicles = [
        d for d in detections if d.label in VEHICLE_LABELS and d.score >= MIN_PRIMARY_CONF
    ]
    return best(vehicles)


def best_iou_with_gt(primary: DetectionRow, gt_boxes: list[BboxNorm]) -> float:
    if not gt_boxes:
        return 0.0
    return max(iou(primary.bbox, gt) for gt in gt_boxes)


def classify_heuristic(
    detections: list[DetectionRow],
    primary: DetectionRow | None,
) -> tuple[str, str]:
    vehicles_any = [
        d for d in detections if d.label in VEHICLE_LABELS and d.score >= MIN_ANY_VEHICLE_CONF
    ]
    if primary is None:
        if not vehicles_any:
            if detections and detections[0].score >= 0.45:
                return "miss", "нет vehicle; top=" + detections[0].label
            return "miss", "vehicle не найден"
        return "miss", f"vehicle ниже порога {MIN_PRIMARY_CONF}"

    if primary.label not in VEHICLE_LABELS:
        return "wrong", f"primary={primary.label} не vehicle"

    if not (GOOD_AREA_MIN <= primary.bbox.area_ratio <= GOOD_AREA_MAX):
        return (
            "wrong",
            f"bbox area={primary.bbox.area_ratio:.0%} вне {GOOD_AREA_MIN:.0%}–{GOOD_AREA_MAX:.0%}",
        )

    non_vehicle = [d for d in detections if d.label not in VEHICLE_LABELS and d.score >= 0.55]
    if non_vehicle and non_vehicle[0].score > primary.score + 0.15:
        return (
            "wrong",
            f"dominant non-vehicle {non_vehicle[0].label} ({non_vehicle[0].score:.2f})",
        )

    return "correct", f"{primary.label} conf={primary.score:.2f} area={primary.bbox.area_ratio:.0%}"


def classify_with_gt(
    detections: list[DetectionRow],
    primary: DetectionRow | None,
    gt_boxes: list[BboxNorm],
) -> tuple[str, str]:
    if primary is None:
        vehicles_any = [
            d for d in detections if d.label in VEHICLE_LABELS and d.score >= MIN_ANY_VEHICLE_CONF
        ]
        if vehicles_any:
            best = max(best_iou_with_gt(v, gt_boxes) for v in vehicles_any)
            if best >= IOU_CORRECT:
                return "miss", f"vehicle ниже primary порога; best_iou={best:.2f}"
        top = detections[0].label if detections else "none"
        return "miss", f"vehicle не найден; top={top}"

    if primary.label not in VEHICLE_LABELS:
        return "wrong", f"primary={primary.label} ({primary.score:.2f})"

    overlap = best_iou_with_gt(primary, gt_boxes)
    if overlap >= IOU_CORRECT:
        return (
            "correct",
            f"{primary.label} conf={primary.score:.2f} iou={overlap:.2f} area={primary.bbox.area_ratio:.0%}",
        )
    if overlap >= IOU_MISS:
        return "miss", f"weak overlap iou={overlap:.2f}"
    return "wrong", f"wrong vehicle iou={overlap:.2f}; top non-veh?"


def draw_overlay(
    image: Image.Image,
    detections: list[DetectionRow],
    primary: DetectionRow | None,
    verdict: str,
    reason: str,
    tags: list[str] | None = None,
    gt_boxes: list[BboxNorm] | None = None,
) -> Image.Image:
    canvas = image.copy()
    draw = ImageDraw.Draw(canvas)
    w, h = canvas.size

    if gt_boxes:
        for gt in gt_boxes:
            x1, y1 = gt.left * w, gt.top * h
            x2, y2 = x1 + gt.width * w, y1 + gt.height * h
            draw.rectangle([x1, y1, x2, y2], outline="#42A5F5", width=2)

    for det in detections:
        if det.score < 0.25:
            continue
        b = det.bbox
        x1, y1 = b.left * w, b.top * h
        x2, y2 = x1 + b.width * w, y1 + b.height * h
        is_primary = primary is not None and det is primary
        color = "#00E676" if is_primary else "#FFEB3B"
        width = 4 if is_primary else 2
        draw.rectangle([x1, y1, x2, y2], outline=color, width=width)
        label = f"{det.label} {det.score:.2f}"
        draw.rectangle([x1, max(0, y1 - 18), x1 + 8 * len(label), y1], fill=color)
        draw.text((x1 + 2, max(0, y1 - 16)), label, fill="#000000")

    tag_text = ", ".join(tags or [])
    banner = f"{verdict.upper()} — {reason}"
    if tag_text:
        banner = f"[{tag_text}] {banner}"
    draw.rectangle([0, 0, w, 28], fill="#000000CC")
    draw.text((8, 6), banner[:140], fill="#FFFFFF")
    return canvas
