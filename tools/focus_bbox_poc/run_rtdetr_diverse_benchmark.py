"""Offline RT-DETR benchmark on 30–50 diverse real car photos.

Sources:
  - COCO val2017 (curated buckets: orientation, distance, multi, dark, cropped)
  - AiVai listing /media car photos (reachable only)

Metrics are computed ONLY for entries with car_present=true.

Run:
  python tools/focus_bbox_poc/run_rtdetr_diverse_benchmark.py

Does NOT touch production backend upload flow, DB, or mobile.
"""

from __future__ import annotations

import hashlib
import json
import statistics
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path

from PIL import Image, ImageStat
from transformers import pipeline

POC_DIR = Path(__file__).resolve().parent
import sys

sys.path.insert(0, str(POC_DIR))

from rtdetr_common import (
    MODEL_ID,
    MODEL_LICENSE,
    BboxNorm,
    DetectionRow,
    VEHICLE_LABELS,
    box_to_norm,
    classify_heuristic,
    classify_with_gt,
    coco_xywh_to_norm,
    draw_overlay,
    pick_primary,
)

API = "http://127.0.0.1:8000"
TARGET_COUNT = 45
COCO_ANNOTATIONS_URL = (
    "http://images.cocodataset.org/annotations/annotations_trainval2017.zip"
)
COCO_INSTANCES_URL = (
    "https://huggingface.co/datasets/merve/coco/resolve/main/annotations/instances_val2017.json"
)

ROOT = Path(__file__).resolve().parents[2]
POC = POC_DIR
OUT = POC / "output" / "diverse_benchmark"
MANIFEST_PATH = OUT / "manifest.json"
IMG_DIR = OUT / "images"
OVERLAY_DIR = OUT / "overlays"
CACHE = POC / ".poc_cache"
COCO_JSON = CACHE / "instances_val2017.json"

BUCKETS = [
    "vertical",
    "horizontal",
    "car_far",
    "car_close",
    "multi_car",
    "dark",
    "edge_crop",
    "listing",
]


@dataclass
class ManifestEntry:
    id: str
    source: str
    filename: str
    url: str
    car_present: bool
    tags: list[str]
    gt_cars: list[BboxNorm] | None = None
    listing_id: int | None = None


@dataclass
class ResultRow:
    id: str
    source: str
    filename: str
    car_present: bool
    tags: list[str]
    image_size: tuple[int, int]
    inference_ms: float
    verdict: str
    verdict_reason: str
    primary: DetectionRow | None
    vehicle_count: int
    top_labels: list[str]
    overlay_path: str


def download_file(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 0:
        return
    print(f"download {url} -> {dest.name}")
    urllib.request.urlretrieve(url, dest)


def load_coco_instances() -> dict:
    if not COCO_JSON.exists():
        download_file(COCO_INSTANCES_URL, COCO_JSON)
    return json.loads(COCO_JSON.read_text(encoding="utf-8"))


def image_brightness(path: Path) -> float:
    img = Image.open(path).convert("L")
    return ImageStat.Stat(img).mean[0] / 255.0


def file_hash(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def build_coco_candidates(coco: dict) -> list[dict]:
    cat_id = next(c["id"] for c in coco["categories"] if c["name"] == "car")
    img_by_id = {img["id"]: img for img in coco["images"]}
    cars_by_image: dict[int, list[list[float]]] = {}
    for ann in coco["annotations"]:
        if ann["category_id"] != cat_id:
            continue
        cars_by_image.setdefault(ann["image_id"], []).append(ann["bbox"])

    candidates: list[dict] = []
    for image_id, boxes in cars_by_image.items():
        img = img_by_id[image_id]
        w, h = img["width"], img["height"]
        norm_boxes = [coco_xywh_to_norm(*b, w, h) for b in boxes]
        areas = [b.area_ratio for b in norm_boxes]
        largest = max(areas)
        count = len(boxes)
        touches_edge = any(
            b.left <= 0.01 or b.top <= 0.01 or b.right >= 0.99 or b.bottom >= 0.99
            for b in norm_boxes
        )
        tags: list[str] = []
        if h > w * 1.15:
            tags.append("vertical")
        elif w > h * 1.15:
            tags.append("horizontal")
        if largest < 0.06:
            tags.append("car_far")
        if largest > 0.22:
            tags.append("car_close")
        if count >= 3:
            tags.append("multi_car")
        if touches_edge:
            tags.append("edge_crop")

        candidates.append(
            {
                "id": f"coco_{image_id}",
                "source": "coco_val2017",
                "filename": img["file_name"],
                "url": f"http://images.cocodataset.org/val2017/{img['file_name']}",
                "car_present": True,
                "tags": tags,
                "gt_cars": norm_boxes,
                "score": largest,
                "car_count": count,
                "aspect": w / h,
            }
        )
    return candidates


def pick_diverse(candidates: list[dict], need: int) -> list[dict]:
    chosen: list[dict] = []
    chosen_ids: set[str] = set()
    bucket_targets = {
        "vertical": 6,
        "horizontal": 6,
        "car_far": 6,
        "car_close": 6,
        "multi_car": 6,
        "edge_crop": 5,
    }

    def try_add(item: dict, bucket: str | None = None) -> bool:
        if item["id"] in chosen_ids:
            return False
        chosen.append(item)
        chosen_ids.add(item["id"])
        if bucket and bucket not in item["tags"]:
            item["tags"] = [*item["tags"], bucket]
        return True

    by_bucket: dict[str, list[dict]] = {b: [] for b in bucket_targets}
    for c in candidates:
        for b in bucket_targets:
            if b in c["tags"]:
                by_bucket[b].append(c)

    for bucket, target in bucket_targets.items():
        pool = sorted(by_bucket[bucket], key=lambda x: (-x["car_count"], -x["score"]))
        for item in pool:
            if sum(1 for x in chosen if bucket in x["tags"]) >= target:
                break
            try_add(item)

    remaining = need - len(chosen)
    if remaining > 0:
        rest = [c for c in candidates if c["id"] not in chosen_ids]
        rest.sort(key=lambda x: (-len(x["tags"]), -x["score"]))
        for item in rest:
            if len(chosen) >= need:
                break
            try_add(item)

    return chosen[:need]


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


def collect_listing_car_photos(token: str) -> list[dict]:
    req = urllib.request.Request(
        f"{API}/api/v1/listings/mine?limit=100",
        headers={"Authorization": f"Bearer {token}"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = json.loads(resp.read().decode())

    rows: list[dict] = []
    seen_names: set[str] = set()
    for listing in body.get("items") or []:
        cat = (listing.get("category") or {}).get("slug", "?")
        if cat != "transport-car-sale":
            continue
        for img in listing.get("images") or []:
            if img.get("is_placeholder"):
                continue
            name = Path(img["url"]).name
            if name in seen_names:
                continue
            seen_names.add(name)
            rows.append(
                {
                    "listing_id": listing["id"],
                    "filename": name,
                    "url": f"{API}{img['url']}",
                }
            )
    return rows


def download_entry_image(entry: ManifestEntry) -> Path | None:
    dest = IMG_DIR / entry.filename
    if dest.exists() and dest.stat().st_size > 0:
        return dest
    try:
        urllib.request.urlretrieve(entry.url, dest)
        return dest
    except urllib.error.HTTPError as exc:
        print(f"skip {entry.id}: HTTP {exc.code}")
        return None


def build_manifest() -> list[ManifestEntry]:
    OUT.mkdir(parents=True, exist_ok=True)
    IMG_DIR.mkdir(parents=True, exist_ok=True)

    coco = load_coco_instances()
    candidates = build_coco_candidates(coco)
    picked = pick_diverse(candidates, need=max(35, TARGET_COUNT - 5))

    entries: list[ManifestEntry] = []
    for row in picked:
        entries.append(
            ManifestEntry(
                id=row["id"],
                source=row["source"],
                filename=row["filename"],
                url=row["url"],
                car_present=True,
                tags=sorted(set(row["tags"])),
                gt_cars=row["gt_cars"],
            )
        )

    listing_rows: list[dict] = []
    try:
        token = login()
        listing_rows = collect_listing_car_photos(token)
    except Exception as exc:
        print(f"listing API unavailable ({exc}); COCO-only manifest")

    known_car_filenames = {
        "397b7426-0e0a-4014-81cd-ec487fcaeabb.jpg",
        "60e6038a-053f-43a8-96c2-f02101271713.jpg",
        "5d4d1448-88c3-4f7e-8713-a7130760af74.jpg",
        "71c05d58-7045-4968-a868-ee3a06e00fe1.jpg",
        "506dbdc7-f45b-40ba-bd40-5dda832f39fe.jpg",
        "812d21cd-3cdc-4873-a95e-16ac02a60863.jpg",
        "77045449-1eaf-473d-a98c-9f04259864cd.jpg",
        "d4751be6-fbd1-40c1-8571-8f0999f61c2d.jpg",
        "569ea9ba-6e10-4261-a35f-31c05e2bbb23.jpg",
        "c2304556-8a7e-4f74-a8ac-93fc77b6e77c.jpg",
        "ed7cb0fa-991c-4142-85c6-68ad3a13547c.jpg",
        "db3273bf-9d1e-466a-a2c9-4a04cc162260.jpg",
        "2a49837b-39b1-482f-bb59-f60cd325575e.jpg",
    }

    seen_hashes: set[str] = set()
    for row in listing_rows:
        if row["filename"] not in known_car_filenames:
            continue
        tmp = ManifestEntry(
            id=f"listing_{row['listing_id']}_{row['filename']}",
            source="aivai_listing",
            filename=f"listing_{row['filename']}",
            url=row["url"],
            car_present=True,
            tags=["listing"],
            gt_cars=None,
            listing_id=row["listing_id"],
        )
        path = download_entry_image(tmp)
        if path is None:
            continue
        digest = file_hash(path)
        if digest in seen_hashes:
            path.unlink(missing_ok=True)
            continue
        seen_hashes.add(digest)
        w, h = Image.open(path).size
        tags = ["listing"]
        if h > w * 1.15:
            tags.append("vertical")
        elif w > h * 1.15:
            tags.append("horizontal")
        if ImageStat.Stat(Image.open(path).convert("L")).mean[0] / 255.0 < 0.35:
            tags.append("dark")
        tmp.tags = sorted(set(tags))
        entries.append(tmp)
        if len(entries) >= TARGET_COUNT:
            break

    if len(entries) < TARGET_COUNT:
        extra = [c for c in candidates if c["id"] not in {e.id for e in entries}]
        extra.sort(key=lambda x: (-len(x["tags"]), -x["score"]))
        for row in extra:
            if len(entries) >= TARGET_COUNT:
                break
            entries.append(
                ManifestEntry(
                    id=row["id"],
                    source=row["source"],
                    filename=row["filename"],
                    url=row["url"],
                    car_present=True,
                    tags=sorted(set(row["tags"])),
                    gt_cars=row["gt_cars"],
                )
            )

    while len(entries) < 30 and candidates:
        for row in candidates:
            if row["id"] not in {e.id for e in entries}:
                entries.append(
                    ManifestEntry(
                        id=row["id"],
                        source=row["source"],
                        filename=row["filename"],
                        url=row["url"],
                        car_present=True,
                        tags=sorted(set(row["tags"])),
                        gt_cars=row["gt_cars"],
                    )
                )
                break
        else:
            break

    manifest = entries[:TARGET_COUNT]
    payload = []
    for e in manifest:
        d = asdict(e)
        if e.gt_cars:
            d["gt_cars"] = [asdict(b) for b in e.gt_cars]
        payload.append(d)
    MANIFEST_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"manifest: {len(manifest)} entries -> {MANIFEST_PATH}")
    return manifest


def load_manifest() -> list[ManifestEntry]:
    if not MANIFEST_PATH.exists():
        return build_manifest()
    raw = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    entries: list[ManifestEntry] = []
    for row in raw:
        gt = None
        if row.get("gt_cars"):
            gt = [BboxNorm(**b) for b in row["gt_cars"]]
        entries.append(
            ManifestEntry(
                id=row["id"],
                source=row["source"],
                filename=row["filename"],
                url=row["url"],
                car_present=row.get("car_present", True),
                tags=row.get("tags") or [],
                gt_cars=gt,
                listing_id=row.get("listing_id"),
            )
        )
    return entries


def tag_dark_entries(entries: list[ManifestEntry]) -> None:
    for entry in entries:
        path = IMG_DIR / entry.filename
        if not path.exists():
            continue
        if image_brightness(path) < 0.32 and "dark" not in entry.tags:
            entry.tags.append("dark")
            entry.tags.sort()


def summarize(results: list[ResultRow]) -> dict:
    car_present = [r for r in results if r.car_present]
    counts = {
        "correct": sum(1 for r in car_present if r.verdict == "correct"),
        "miss": sum(1 for r in car_present if r.verdict == "miss"),
        "wrong": sum(1 for r in car_present if r.verdict == "wrong"),
    }
    total = len(car_present)
    by_tag: dict[str, dict[str, int]] = {}
    for r in car_present:
        for tag in r.tags:
            by_tag.setdefault(tag, {"correct": 0, "miss": 0, "wrong": 0})
            by_tag[tag][r.verdict] += 1
    return {
        "car_present_total": total,
        "verdicts": counts,
        "hit_rate_correct": counts["correct"] / total if total else 0.0,
        "wrong_rate": counts["wrong"] / total if total else 0.0,
        "by_tag": by_tag,
    }


def main() -> None:
    import sys

    rebuild = "--rebuild-manifest" in sys.argv
    if rebuild and MANIFEST_PATH.exists():
        MANIFEST_PATH.unlink()

    OUT.mkdir(parents=True, exist_ok=True)
    OVERLAY_DIR.mkdir(parents=True, exist_ok=True)
    IMG_DIR.mkdir(parents=True, exist_ok=True)

    manifest = build_manifest() if rebuild or not MANIFEST_PATH.exists() else load_manifest()

    print(f"Loading RT-DETR ({MODEL_ID}, {MODEL_LICENSE})...")
    t_load = time.perf_counter()
    detector = pipeline("object-detection", model=MODEL_ID, device="cpu")
    load_ms = (time.perf_counter() - t_load) * 1000
    print(f"model loaded in {load_ms:.0f} ms")

    results: list[ResultRow] = []
    latencies: list[float] = []
    processed = 0

    for entry in manifest:
        path = download_entry_image(entry)
        if path is None:
            continue
        tag_dark_entries([entry])
        image = Image.open(path).convert("RGB")
        w, h = image.size

        t0 = time.perf_counter()
        raw = detector(image, threshold=0.25)
        infer_ms = (time.perf_counter() - t0) * 1000
        latencies.append(infer_ms)
        processed += 1

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

        if entry.gt_cars:
            verdict, reason = classify_with_gt(detections, primary, entry.gt_cars)
        else:
            verdict, reason = classify_heuristic(detections, primary)

        overlay = draw_overlay(
            image,
            detections,
            primary,
            verdict,
            reason,
            tags=entry.tags,
            gt_boxes=entry.gt_cars,
        )
        overlay_path = OVERLAY_DIR / f"{entry.id}_{entry.filename}"
        overlay.save(overlay_path, quality=90)

        results.append(
            ResultRow(
                id=entry.id,
                source=entry.source,
                filename=entry.filename,
                car_present=entry.car_present,
                tags=entry.tags,
                image_size=(w, h),
                inference_ms=infer_ms,
                verdict=verdict,
                verdict_reason=reason,
                primary=primary,
                vehicle_count=sum(
                    1 for d in detections if d.label in VEHICLE_LABELS and d.score >= 0.25
                ),
                top_labels=[f"{d.label}:{d.score:.2f}" for d in detections[:5]],
                overlay_path=str(overlay_path.relative_to(ROOT)),
            )
        )

    metrics = summarize(results)
    summary = {
        "model": MODEL_ID,
        "license": MODEL_LICENSE,
        "manifest_entries": len(manifest),
        "processed": processed,
        "gate_target": "≥90–95% correct on car_present, ~0 wrong-object",
        **metrics,
        "latency_ms": {
            "mean": statistics.mean(latencies) if latencies else 0,
            "p50": statistics.median(latencies) if latencies else 0,
            "p95": sorted(latencies)[max(0, int(len(latencies) * 0.95) - 1)] if latencies else 0,
        },
        "model_load_ms": load_ms,
    }

    def ser_result(r: ResultRow) -> dict:
        d = asdict(r)
        if r.primary:
            d["primary"] = asdict(r.primary)
        return d

    report_json = OUT / "report.json"
    report_json.write_text(
        json.dumps({"summary": summary, "results": [ser_result(r) for r in results]}, indent=2),
        encoding="utf-8",
    )

    cp = metrics["car_present_total"]
    v = metrics["verdicts"]
    md = [
        "# RT-DETR diverse car benchmark (offline)",
        "",
        f"- Model: `{MODEL_ID}` ({MODEL_LICENSE})",
        f"- Processed: **{processed}** photos, all `car_present=true`",
        "",
        "## Gate metrics (car present only)",
        "",
        "| Verdict | Count | Share |",
        "|---------|------:|------:|",
        f"| ✅ correct | {v['correct']} | {v['correct']/cp:.1%} |" if cp else "",
        f"| ⚠️ miss | {v['miss']} | {v['miss']/cp:.1%} |" if cp else "",
        f"| ❌ wrong | {v['wrong']} | {v['wrong']/cp:.1%} |" if cp else "",
        "",
        f"- **Hit rate:** {metrics['hit_rate_correct']:.1%}",
        f"- **Wrong-object rate:** {metrics['wrong_rate']:.1%}",
        f"- Mean latency: **{summary['latency_ms']['mean']:.0f} ms**/photo",
        "",
        "## By tag",
        "",
    ]
    for tag, counts in sorted(metrics["by_tag"].items()):
        total = sum(counts.values())
        md.append(
            f"- **{tag}**: correct {counts['correct']}/{total}, "
            f"miss {counts['miss']}, wrong {counts['wrong']}"
        )
    md.extend(["", "## Per image", ""])
    for r in results:
        md.append(
            f"- `{r.id}` [{', '.join(r.tags)}] → **{r.verdict}** ({r.verdict_reason}) — `{r.overlay_path}`"
        )

    report_md = OUT / "report.md"
    report_md.write_text("\n".join(md), encoding="utf-8")

    print(json.dumps(summary, indent=2))
    print(f"JSON: {report_json}")
    print(f"MD:   {report_md}")
    print(f"Overlays: {OVERLAY_DIR}")


if __name__ == "__main__":
    main()
