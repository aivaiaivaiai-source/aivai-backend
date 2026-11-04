"""Stable hashing helpers for reproducibility."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_json(obj: Any) -> str:
    payload = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return sha256_bytes(payload.encode("utf-8"))


def dataset_hash(manifest_path: Path, catalog_path: Path) -> str:
    """Hash of manifest contents + catalog contents (not absolute paths)."""
    man = manifest_path.read_bytes()
    cat = catalog_path.read_bytes()
    return sha256_bytes(man + b"\n" + cat)
