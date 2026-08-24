"""Verify v2 feed variant after FEED_ASPECT fix (listing 60 / photo 77 original)."""

from __future__ import annotations

import hashlib
import json
import struct
import sys
import time
import urllib.error
import urllib.request
import uuid
from io import BytesIO

from PIL import Image

API = "http://192.168.1.15:8000"
PHONE = "+79001234567"
SOURCE_LISTING = 60
SOURCE_MEDIA = 77


def _req(method: str, path: str, token: str | None = None, data: dict | bytes | None = None, headers: dict | None = None):
    h = {"Accept": "application/json"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    if headers:
        h.update(headers)
    body = None
    if isinstance(data, dict):
        body = json.dumps(data).encode()
        h.setdefault("Content-Type", "application/json")
    elif isinstance(data, bytes):
        body = data
    req = urllib.request.Request(f"{API}{path}", data=body, headers=h, method=method)
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            raw = resp.read()
            if not raw:
                return resp.status, None
            return resp.status, json.loads(raw)
    except urllib.error.HTTPError as e:
        err = e.read().decode(errors="replace")
        raise RuntimeError(f"{method} {path} -> {e.code}: {err}") from e


def _login() -> str:
    _, data = _req("POST", "/api/v1/auth/login", data={"phone": PHONE})
    return data["access_token"]


def _jpeg_dims(url: str) -> tuple[int, int]:
    full = url if url.startswith("http") else f"{API}{url}"
    data = urllib.request.urlopen(full, timeout=60).read()
    img = Image.open(BytesIO(data))
    return img.size


def main() -> None:
    token = _login()

    # Download same original as listing 60 / photo 77
    _, listing = _req("GET", f"/api/v1/listings/{SOURCE_LISTING}", token)
    src = next(i for i in listing["images"] if i["id"] == SOURCE_MEDIA)
    orig_url = src["variants"]["original"]
    orig_bytes = urllib.request.urlopen(f"{API}{orig_url}", timeout=60).read()
    print(f"original bytes={len(orig_bytes)} sha256={hashlib.sha256(orig_bytes).hexdigest()[:16]}")

    # Create draft listing
    _, created = _req(
        "POST",
        "/api/v1/listings",
        token,
        {
            "title": "feed-aspect-fix-verify",
            "description": "feed aspect v2 verify",
            "price": "100000",
            "currency": "KGS",
            "category_id": 681,
            "fields": {"city": "Бишкек"},
        },
    )
    listing_id = created["id"]
    print(f"created listing_id={listing_id}")

    client_upload_id = str(uuid.uuid4())
    content_type = "image/jpeg"
    content_sha256 = hashlib.sha256(orig_bytes).hexdigest()

    _, init = _req(
        "POST",
        f"/api/v1/listings/{listing_id}/media/uploads",
        token,
        {
            "client_upload_id": client_upload_id,
            "order": 0,
            "content_type": content_type,
            "content_length": len(orig_bytes),
            "content_sha256": content_sha256,
        },
    )
    media_id = init["media_id"]
    print(f"initiated media_id={media_id} pipeline={init.get('pipeline_version')}")

    _req(
        "PUT",
        f"/api/v1/listings/{listing_id}/media/{media_id}/upload",
        token,
        data=orig_bytes,
        headers={"Content-Type": content_type},
    )
    _, complete = _req(
        "POST",
        f"/api/v1/listings/{listing_id}/media/{media_id}/complete",
        token,
    )
    print(f"complete lifecycle={complete.get('lifecycle_status')}")

    # Poll until ready
    for i in range(90):
        _, item = _req("GET", f"/api/v1/listings/{listing_id}", token)
        photo = item["images"][0]
        status = photo.get("lifecycle_status")
        if status == "ready":
            break
        if status == "failed":
            raise RuntimeError(f"media failed: {photo.get('error_code')}")
        time.sleep(1)
    else:
        raise RuntimeError("timeout waiting for media ready")

    photo = item["images"][0]
    feed_url = photo["variants"]["feed"]
    display_url = photo["variants"]["display"]
    fw, fh = _jpeg_dims(feed_url)
    dw, dh = _jpeg_dims(display_url)

    print(json.dumps({
        "listing_id": listing_id,
        "media_id": photo["id"],
        "pipeline_version": photo.get("pipeline_version"),
        "feed_url": feed_url,
        "feed_size": [fw, fh],
        "feed_aspect": round(fw / fh, 6),
        "display_size": [dw, dh],
        "display_aspect": round(dw / dh, 6),
        "legacy_v1_feed_still_exists": "/v1/feed.jpg" in src["variants"]["feed"],
    }, indent=2, ensure_ascii=False))

    # Activate for feed visibility
    _req("PATCH", f"/api/v1/listings/{listing_id}/status", token, {"status": "active"})
    print(f"activated listing {listing_id}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        raise
