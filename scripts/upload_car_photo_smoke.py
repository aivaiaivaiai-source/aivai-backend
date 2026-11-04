"""One-off: upload car photo and print MediaRead JSON (integration smoke)."""

from __future__ import annotations

import json
import pathlib
import sys
import urllib.request

API = "http://127.0.0.1:8000"
PHONE = "+79001234567"
ROOT = pathlib.Path(__file__).resolve().parents[1]
CANDIDATES = [
    ROOT
    / "tools/focus_bbox_poc/output/diverse_benchmark/images/listing_397b7426-0e0a-4014-81cd-ec487fcaeabb.jpg",
    ROOT / "tools/focus_bbox_poc/output/diverse_benchmark/images/000000054967.jpg",
]


def _login() -> str:
    req = urllib.request.Request(
        f"{API}/api/v1/auth/login",
        data=json.dumps({"phone": PHONE}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())["access_token"]


def _find_car_listing(token: str) -> int:
    req = urllib.request.Request(
        f"{API}/api/v1/listings/mine?limit=20",
        headers={"Authorization": f"Bearer {token}"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        items = json.loads(resp.read()).get("items") or []
    for item in items:
        slug = (item.get("category") or {}).get("slug")
        if slug == "transport-car-sale":
            return int(item["id"])
    if not items:
        raise RuntimeError("No listings found for dev user")
    return int(items[0]["id"])


def _upload(token: str, listing_id: int, image_path: pathlib.Path) -> list[dict]:
    boundary = "----aivaiFocusBboxTest"
    image_bytes = image_path.read_bytes()
    parts = [
        f"--{boundary}\r\n".encode(),
        b'Content-Disposition: form-data; name="files"; filename="car_test.jpg"\r\n',
        b"Content-Type: image/jpeg\r\n\r\n",
        image_bytes,
        f"\r\n--{boundary}--\r\n".encode(),
    ]
    payload = b"".join(parts)
    req = urllib.request.Request(
        f"{API}/api/v1/listings/{listing_id}/media",
        data=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=600) as resp:
        return json.loads(resp.read())


def main() -> None:
    image_path = next((p for p in CANDIDATES if p.exists()), None)
    if image_path is None:
        raise SystemExit("No sample car image found")

    token = _login()
    listing_id = _find_car_listing(token)
    print(f"listing_id={listing_id} image={image_path.name}", file=sys.stderr)
    result = _upload(token, listing_id, image_path)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
