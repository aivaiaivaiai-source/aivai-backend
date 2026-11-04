"""Intent fingerprint helpers for revision / stale resolver detection."""

from __future__ import annotations

import hashlib
import unicodedata


def normalize_intent_text(raw: str) -> str:
    """Trim only — preserve user wording and internal spacing."""
    return (raw or "").strip()


def intent_fingerprint(raw: str) -> str:
    """
    Deterministic fingerprint for intent revision.

    Uses trimmed Unicode text (case-sensitive) so edits invalidate stale results.
    """
    normalized = normalize_intent_text(raw)
    if not normalized:
        return hashlib.sha256(b"empty").hexdigest()[:32]
    payload = unicodedata.normalize("NFC", normalized).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()[:32]


def hybrid_resolver_input_fingerprint(
    *,
    media_set_fingerprint: str,
    intent_fingerprint: str,
    resolver_version: str,
    catalog_snapshot_hash: str = "",
) -> str:
    """Idempotency key for Category Resolver jobs (3C-3)."""
    media_fp = (media_set_fingerprint or "").strip() or "empty"
    intent_fp = (intent_fingerprint or "").strip() or "empty"
    version = (resolver_version or "").strip() or "v0"
    catalog_hash = (catalog_snapshot_hash or "").strip() or "empty"
    payload = f"{media_fp}|{intent_fp}|{catalog_hash}|{version}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()[:32]
