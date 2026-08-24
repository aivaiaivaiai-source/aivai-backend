"""One-off POC benchmark: YOLOv8n ONNX on AiVai listing photos.

Not wired to production. Run from repo root:
  python tools/yolo_focus_bbox_poc_benchmark.py
"""

from __future__ import annotations

import json
import statistics
import time
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path

import cv2
import numpy as np
import onnxruntime as ort
import psutil

API = "http://127.0.0.1:8000"
MODEL_URL = "https://huggingface.co/Kalray/yolov8/resolve/main/yolov8n.onnx"
VEHICLE_CLASS_IDS = {2, 3, 5, 7}  # car, motorcycle, bus, truck

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "tools" / ".poc_cache"
MODEL_PATH = CACHE / "yolov8n.onnx"
IMAGES_DIR = CACHE / "listing_images"
REPORT_PATH = CACHE / "yolo_poc_report.json"


@dataclass
class Detection:
    class_id: int
    class_name: str
    confidence: float
    bbox_norm: tuple[float, float, float, float]  # x,y,w,h in 0..1
    area_ratio: float


@dataclass
class ImageResult:
    listing_id: int
    category: str
    url: str
    file: str
    inference_ms: float
    vehicle_hit: bool
    primary: Detection | None
    all_vehicle_count: int
    smartfit_useful: bool | None


CLASS_NAMES = [
    "person",
    "bicycle",
    "car",
    "motorcycle",
    "airplane",
    "bus",
    "train",
    "truck",
    "boat",
    "traffic light",
    "fire hydrant",
    "stop sign",
    "parking meter",
    "bench",
    "bird",
    "cat",
    "dog",
    "horse",
    "sheep",
    "cow",
    "elephant",
    "bear",
    "zebra",
    "giraffe",
    "backpack",
    "umbrella",
    "handbag",
    "tie",
    "suitcase",
    "frisbee",
    "skis",
    "snowboard",
    "sports ball",
    "kite",
    "baseball bat",
    "baseball glove",
    "skateboard",
    "surfboard",
    "tennis racket",
    "bottle",
    "wine glass",
    "cup",
    "fork",
    "knife",
    "spoon",
    "bowl",
    "banana",
    "apple",
    "sandwich",
    "orange",
    "broccoli",
    "carrot",
    "hot dog",
    "pizza",
    "donut",
    "cake",
    "chair",
    "couch",
    "potted plant",
    "bed",
    "dining table",
    "toilet",
    "tv",
    "laptop",
    "mouse",
    "remote",
    "keyboard",
    "cell phone",
    "microwave",
    "oven",
    "toaster",
    "sink",
    "refrigerator",
    "book",
    "clock",
    "vase",
    "scissors",
    "teddy bear",
    "hair drier",
    "toothbrush",
]


def fetch_json(url: str, token: str | None = None) -> dict:
    req = urllib.request.Request(url)
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())


def login() -> str:
    payload = json.dumps({"phone": "+79001234567"}).encode()
    req = urllib.request.Request(
        f"{API}/api/v1/auth/login",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = json.loads(resp.read().decode())
    return body["access_token"]


def ensure_model() -> None:
    CACHE.mkdir(parents=True, exist_ok=True)
    if MODEL_PATH.exists() and MODEL_PATH.stat().st_size > 1_000_000:
        return
    print(f"Downloading {MODEL_URL} ...")
    urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)


def collect_images(token: str, limit: int = 30) -> list[dict]:
    body = fetch_json(f"{API}/api/v1/listings/mine?limit=40", token)
    items = body.get("items") or body
    rows: list[dict] = []
    for listing in items:
        for img in listing.get("images") or []:
            if img.get("is_placeholder"):
                continue
            rows.append(
                {
                    "listing_id": listing["id"],
                    "category": (listing.get("category") or {}).get("slug", "?"),
                    "url": f"{API}{img['url']}",
                    "filename": Path(img["url"]).name,
                }
            )
            if len(rows) >= limit:
                return rows
    return rows


def download_images(rows: list[dict]) -> list[dict]:
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    out = []
    for row in rows:
        dest = IMAGES_DIR / row["filename"]
        if not dest.exists():
            try:
                urllib.request.urlretrieve(row["url"], dest)
            except Exception as exc:
                print(f"skip {row['filename']}: {exc}")
                continue
        row = dict(row)
        row["path"] = str(dest)
        out.append(row)
    return out


def nms(boxes: np.ndarray, scores: np.ndarray, iou_threshold: float = 0.45) -> list[int]:
    if len(boxes) == 0:
        return []
    x1 = boxes[:, 0]
    y1 = boxes[:, 1]
    x2 = boxes[:, 2]
    y2 = boxes[:, 3]
    areas = (x2 - x1) * (y2 - y1)
    order = scores.argsort()[::-1]
    keep: list[int] = []
    while order.size > 0:
        i = int(order[0])
        keep.append(i)
        if order.size == 1:
            break
        rest = order[1:]
        xx1 = np.maximum(x1[i], x1[rest])
        yy1 = np.maximum(y1[i], y1[rest])
        xx2 = np.minimum(x2[i], x2[rest])
        yy2 = np.minimum(y2[i], y2[rest])
        w = np.maximum(0.0, xx2 - xx1)
        h = np.maximum(0.0, yy2 - yy1)
        inter = w * h
        iou = inter / (areas[i] + areas[rest] - inter + 1e-6)
        order = rest[iou <= iou_threshold]
    return keep


def detect_vehicles(session: ort.InferenceSession, image_path: str) -> tuple[list[Detection], float]:
    img = cv2.imread(image_path)
    if img is None:
        return [], 0.0
    h, w = img.shape[:2]
    inp = cv2.resize(img, (640, 640))
    inp = inp[:, :, ::-1].transpose(2, 0, 1).astype(np.float32) / 255.0
    inp = np.expand_dims(inp, 0)

    t0 = time.perf_counter()
    out = session.run(None, {session.get_inputs()[0].name: inp})[0]
    ms = (time.perf_counter() - t0) * 1000

    preds = np.squeeze(out).T  # N x 84
    boxes = preds[:, :4]
    scores = preds[:, 4:]
    class_ids = np.argmax(scores, axis=1)
    confidences = scores[np.arange(len(class_ids)), class_ids]

    mask = confidences >= 0.25
    boxes = boxes[mask]
    class_ids = class_ids[mask]
    confidences = confidences[mask]

    if len(boxes) == 0:
        return [], ms

    # xywh center -> xyxy pixel on original image
    scale_x = w / 640
    scale_y = h / 640
    xyxy = np.zeros_like(boxes)
    xyxy[:, 0] = (boxes[:, 0] - boxes[:, 2] / 2) * scale_x
    xyxy[:, 1] = (boxes[:, 1] - boxes[:, 3] / 2) * scale_y
    xyxy[:, 2] = (boxes[:, 0] + boxes[:, 2] / 2) * scale_x
    xyxy[:, 3] = (boxes[:, 1] + boxes[:, 3] / 2) * scale_y

    vehicle_idx = [i for i, cid in enumerate(class_ids) if int(cid) in VEHICLE_CLASS_IDS]
    if not vehicle_idx:
        return [], ms

    v_boxes = xyxy[vehicle_idx]
    v_scores = confidences[vehicle_idx]
    v_classes = class_ids[vehicle_idx]
    keep = nms(v_boxes, v_scores)
    detections: list[Detection] = []
    for i in keep:
        x1, y1, x2, y2 = v_boxes[i]
        x1 = max(0.0, min(w, x1))
        y1 = max(0.0, min(h, y1))
        x2 = max(0.0, min(w, x2))
        y2 = max(0.0, min(h, y2))
        bw = max(1.0, x2 - x1)
        bh = max(1.0, y2 - y1)
        cid = int(v_classes[i])
        detections.append(
            Detection(
                class_id=cid,
                class_name=CLASS_NAMES[cid] if cid < len(CLASS_NAMES) else str(cid),
                confidence=float(v_scores[i]),
                bbox_norm=(
                    float(x1 / w),
                    float(y1 / h),
                    float(bw / w),
                    float(bh / h),
                ),
                area_ratio=float((bw * bh) / (w * h)),
            )
        )
    return detections, ms


def pick_primary(detections: list[Detection]) -> Detection | None:
    if not detections:
        return None
    # Largest area, tie-break by confidence.
    return sorted(
        detections,
        key=lambda d: (d.area_ratio, d.confidence),
        reverse=True,
    )[0]


def main() -> None:
    process = psutil.Process()
    rss_before = process.memory_info().rss / (1024 * 1024)
    ensure_model()
    token = login()
    rows = collect_images(token, limit=30)
    if not rows:
        raise SystemExit("No listing images found on API")
    rows = download_images(rows)

    providers = ort.get_available_providers()
    session = ort.InferenceSession(str(MODEL_PATH), providers=providers)
    rss_after_model = process.memory_info().rss / (1024 * 1024)

    results: list[ImageResult] = []
    for row in rows:
        dets, ms = detect_vehicles(session, row["path"])
        primary = pick_primary(dets)
        hit = bool(primary is not None and primary.confidence >= 0.35)
        useful = None
        if primary is not None:
            useful = bool(primary.area_ratio < 0.55)
        results.append(
            ImageResult(
                listing_id=row["listing_id"],
                category=row["category"],
                url=row["url"],
                file=row["filename"],
                inference_ms=ms,
                vehicle_hit=hit,
                primary=primary,
                all_vehicle_count=len(dets),
                smartfit_useful=useful,
            )
        )

    rss_peak = process.memory_info().rss / (1024 * 1024)
    latencies = [r.inference_ms for r in results]
    hits = sum(1 for r in results if r.vehicle_hit)
    good_bbox = sum(
        1
        for r in results
        if r.primary and 0.08 <= r.primary.area_ratio <= 0.90
    )

    summary = {
        "model": "yolov8n.onnx (Ultralytics export, COCO)",
        "images": len(results),
        "categories": sorted({r.category for r in results}),
        "vehicle_hit_rate": hits / len(results),
        "good_bbox_rate": good_bbox / len(results),
        "smartfit_candidate_rate": sum(1 for r in results if r.smartfit_useful) / len(results),
        "latency_ms": {
            "p50": statistics.median(latencies),
            "p95": sorted(latencies)[max(0, int(len(latencies) * 0.95) - 1)],
            "mean": statistics.mean(latencies),
        },
        "memory_mb": {
            "rss_before": round(rss_before, 1),
            "rss_after_model_load": round(rss_after_model, 1),
            "rss_after_batch": round(rss_peak, 1),
            "model_delta_mb": round(rss_after_model - rss_before, 1),
        },
        "onnx_providers": providers,
        "cpu_count": psutil.cpu_count(logical=True),
    }

    payload = {
        "summary": summary,
        "results": [
            {
                **{k: v for k, v in asdict(r).items() if k != "primary"},
                "primary": asdict(r.primary) if r.primary else None,
            }
            for r in results
        ],
    }
    REPORT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    print(f"Report: {REPORT_PATH}")


if __name__ == "__main__":
    main()
