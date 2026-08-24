"""Offline RT-DETR POC for AiVai car listing photos.

License-safe: PekingU/rtdetr_r18vd_coco_o365 (Apache-2.0).
Does NOT touch production upload flow, DB, or mobile.

Run:
  python tools/focus_bbox_poc/run_rtdetr_car_poc.py

Outputs:
  tools/focus_bbox_poc/output/overlays/*.jpg
  tools/focus_bbox_poc/output/report.json
  tools/focus_bbox_poc/output/report.md
"""

from __future__ import annotations

import json
import statistics
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from transformers import pipeline

API = "http://127.0.0.1:8000"
MODEL_ID = "PekingU/rtdetr_r18vd_coco_o365"
MODEL_LICENSE = "Apache-2.0"

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "tools" / "focus_bbox_poc" / "output"
IMG_CACHE = OUT / "images"
OVERLAY_DIR = OUT / "overlays"

VEHICLE_LABELS = {"car", "truck", "bus", "motorcycle"}
MIN_PRIMARY_CONF = 0.35
MIN_ANY_VEHICLE_CONF = 0.25
GOOD_AREA_MIN = 0.08
GOOD_AREA_MAX = 0.80


@dataclass
class BboxNorm:
    left: float
    top: float
    width: float
    height: float
    area_ratio: float


@dataclass
class DetectionRow:
    label: str
    score: float
    bbox: BboxNorm


@dataclass
class ImageReport:
    listing_id: int
    category: str
    filename: str
    url: str
    image_size: tuple[int, int]
    inference_ms: float
    verdict: str  # correct | miss | wrong
    verdict_reason: str
    primary: DetectionRow | None
    vehicle_count: int
    top_labels: list[str]
    overlay_path: str


def login() -> str:
    payload = json.dumps({"phone": "+79001234567"}).encode()
    req = urllib.request.Request(
        f"{API}/api/v1/auth/login",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())["access_token"]


def collect_car_images(token: str, limit: int = 50) -> list[dict]:
    req = urllib.request.Request(
        f"{API}/api/v1/listings/mine?limit=100",
        headers={"Authorization": f"Bearer {token}"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = json.loads(resp.read().decode())
    rows: list[dict] = []
    seen: set[str] = set()
    for listing in body.get("items") or []:
        cat = (listing.get("category") or {}).get("slug", "?")
        if cat != "transport-car-sale":
            continue
        for img in listing.get("images") or []:
            if img.get("is_placeholder"):
                continue
            name = Path(img["url"]).name
            if name in seen:
                continue
            seen.add(name)
            rows.append(
                {
                    "listing_id": listing["id"],
                    "category": cat,
                    "filename": name,
                    "url": f"{API}{img['url']}",
                }
            )
            if len(rows) >= limit:
                return rows
    return rows


def download_image(row: dict) -> Path | None:
    dest = IMG_CACHE / row["filename"]
    if dest.exists() and dest.stat().st_size > 0:
        return dest
    try:
        urllib.request.urlretrieve(row["url"], dest)
        return dest
    except urllib.error.HTTPError as exc:
        print(f"skip missing {row['filename']}: HTTP {exc.code}")
        return None


def box_to_norm(box: dict, w: int, h: int) -> BboxNorm:
    x1 = max(0.0, float(box["xmin"]))
    y1 = max(0.0, float(box["ymin"]))
    x2 = min(float(w), float(box["xmax"]))
    y2 = min(float(h), float(box["ymax"]))
    bw = max(1.0, x2 - x1)
    bh = max(1.0, y2 - y1)
    return BboxNorm(
        left=x1 / w,
        top=y1 / h,
        width=bw / w,
        height=bh / h,
        area_ratio=(bw * bh) / (w * h),
    )


def pick_primary(detections: list[DetectionRow]) -> DetectionRow | None:
    vehicles = [
        d
        for d in detections
        if d.label in VEHICLE_LABELS and d.score >= MIN_PRIMARY_CONF
    ]
    if not vehicles:
        return None
    return max(vehicles, key=lambda d: (d.bbox.area_ratio, d.score))


def classify(
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

    if not (GOOD_AREA_MIN <= primary.bbox.area_ratio <= GOOD_AREA_MAX):
        return (
            "wrong",
            f"vehicle bbox area={primary.bbox.area_ratio:.0%} вне {GOOD_AREA_MIN:.0%}–{GOOD_AREA_MAX:.0%}",
        )

    non_vehicle = [d for d in detections if d.label not in VEHICLE_LABELS and d.score >= 0.55]
    if non_vehicle and non_vehicle[0].score > primary.score + 0.15:
        return (
            "wrong",
            f"dominant non-vehicle {non_vehicle[0].label} ({non_vehicle[0].score:.2f})",
        )

    return "correct", f"{primary.label} conf={primary.score:.2f} area={primary.bbox.area_ratio:.0%}"


def draw_overlay(
    image: Image.Image,
    detections: list[DetectionRow],
    primary: DetectionRow | None,
    verdict: str,
    reason: str,
) -> Image.Image:
    canvas = image.copy()
    draw = ImageDraw.Draw(canvas)
    w, h = canvas.size

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

    banner = f"{verdict.upper()} — {reason}"
    draw.rectangle([0, 0, w, 28], fill="#000000CC")
    draw.text((8, 6), banner[:120], fill="#FFFFFF")
    return canvas


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    IMG_CACHE.mkdir(parents=True, exist_ok=True)
    OVERLAY_DIR.mkdir(parents=True, exist_ok=True)

    token = login()
    manifest = collect_car_images(token, limit=50)
    print(f"manifest unique car images: {len(manifest)}")

    print(f"Loading RT-DETR ({MODEL_ID}, {MODEL_LICENSE})...")
    t_load = time.perf_counter()
    detector = pipeline("object-detection", model=MODEL_ID, device="cpu")
    load_ms = (time.perf_counter() - t_load) * 1000
    print(f"model loaded in {load_ms:.0f} ms")

    reports: list[ImageReport] = []
    latencies: list[float] = []
    downloaded = 0

    for row in manifest:
        path = download_image(row)
        if path is None:
            continue
        downloaded += 1
        image = Image.open(path).convert("RGB")
        w, h = image.size

        t0 = time.perf_counter()
        raw = detector(image, threshold=0.25)
        infer_ms = (time.perf_counter() - t0) * 1000
        latencies.append(infer_ms)

        detections = [
            DetectionRow(
                label=str(r["label"]),
                score=float(r["score"]),
                bbox=box_to_norm(r["box"], w, h),
            )
            for r in raw
        ]
        detections.sort(key=lambda d: d.score, reverse=True)
        primary = pick_primary(detections)
        verdict, reason = classify(detections, primary)

        overlay = draw_overlay(image, detections, primary, verdict, reason)
        overlay_path = OVERLAY_DIR / f"{row['listing_id']}_{row['filename']}"
        overlay.save(overlay_path, quality=92)

        reports.append(
            ImageReport(
                listing_id=row["listing_id"],
                category=row["category"],
                filename=row["filename"],
                url=row["url"],
                image_size=(w, h),
                inference_ms=infer_ms,
                verdict=verdict,
                verdict_reason=reason,
                primary=primary,
                vehicle_count=sum(1 for d in detections if d.label in VEHICLE_LABELS and d.score >= 0.25),
                top_labels=[f"{d.label}:{d.score:.2f}" for d in detections[:5]],
                overlay_path=str(overlay_path.relative_to(ROOT)),
            )
        )

    counts = {
        "correct": sum(1 for r in reports if r.verdict == "correct"),
        "miss": sum(1 for r in reports if r.verdict == "miss"),
        "wrong": sum(1 for r in reports if r.verdict == "wrong"),
    }
    total = len(reports)

    summary = {
        "model": MODEL_ID,
        "license": MODEL_LICENSE,
        "category_filter": "transport-car-sale",
        "manifest_unique": len(manifest),
        "downloaded_and_processed": downloaded,
        "note": "Only reachable /media files; stale DB refs skipped.",
        "verdicts": counts,
        "hit_rate_correct": counts["correct"] / total if total else 0.0,
        "latency_ms": {
            "mean": statistics.mean(latencies) if latencies else 0,
            "p50": statistics.median(latencies) if latencies else 0,
            "p95": sorted(latencies)[max(0, int(len(latencies) * 0.95) - 1)] if latencies else 0,
        },
        "model_load_ms": load_ms,
    }

    def serialize_report(r: ImageReport) -> dict:
        d = asdict(r)
        if r.primary:
            d["primary"] = asdict(r.primary)
        return d

    payload = {"summary": summary, "results": [serialize_report(r) for r in reports]}
    report_json = OUT / "report.json"
    report_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    md_lines = [
        "# RT-DETR car POC (offline)",
        "",
        f"- Model: `{MODEL_ID}` ({MODEL_LICENSE})",
        f"- Processed: **{total}** reachable car photos (manifest {len(manifest)})",
        "",
        "## Verdicts (auto rules)",
        "",
        f"| Verdict | Count | Share |",
        f"|---------|------:|------:|",
        f"| ✅ correct | {counts['correct']} | {counts['correct']/total:.0%} |" if total else "",
        f"| ⚠️ miss | {counts['miss']} | {counts['miss']/total:.0%} |" if total else "",
        f"| ❌ wrong | {counts['wrong']} | {counts['wrong']/total:.0%} |" if total else "",
        "",
        f"- Mean latency: **{summary['latency_ms']['mean']:.0f} ms**/photo",
        "",
        "## Overlays",
        "",
        "See `tools/focus_bbox_poc/output/overlays/` — green = primary vehicle bbox.",
        "",
        "## Per image",
        "",
    ]
    for r in reports:
        md_lines.append(
            f"- listing **{r.listing_id}** `{r.filename}` → **{r.verdict}** ({r.verdict_reason}) — `{r.overlay_path}`"
        )

    report_md = OUT / "report.md"
    report_md.write_text("\n".join(md_lines), encoding="utf-8")

    print(json.dumps(summary, indent=2))
    print(f"JSON: {report_json}")
    print(f"MD:   {report_md}")
    print(f"Overlays: {OVERLAY_DIR}")


if __name__ == "__main__":
    main()
