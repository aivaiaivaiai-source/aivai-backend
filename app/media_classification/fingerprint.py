"""Media-set fingerprint for stale classification detection."""

from __future__ import annotations

import hashlib
from collections.abc import Sequence


def media_set_fingerprint(ordered_media_ids: Sequence[int]) -> str:
    """
    Deterministic fingerprint of ordered media identity for one listing.

    Classification results bind to this revision; add/remove/reorder → new fp.
    """
    if not ordered_media_ids:
        return hashlib.sha256(b"empty").hexdigest()[:32]
    payload = ",".join(str(int(i)) for i in ordered_media_ids).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()[:32]
