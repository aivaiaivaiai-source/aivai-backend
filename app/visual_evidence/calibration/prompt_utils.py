"""Prompt metadata helpers — deterministic without model load."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROMPT_SET = PACKAGE_ROOT / "prompts" / "visual_evidence_prompts_v1.json"


def load_prompt_set(path: Path = DEFAULT_PROMPT_SET) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f"prompt set missing: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def compute_prompt_hash(path: Path = DEFAULT_PROMPT_SET) -> str:
    raw = path.read_text(encoding="utf-8")
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def load_prompt_metadata(path: Path = DEFAULT_PROMPT_SET) -> tuple[str, str]:
    raw = path.read_text(encoding="utf-8")
    data = json.loads(raw)
    version = str(data.get("prompt_set_version") or "")
    prompt_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
    return version, prompt_hash
