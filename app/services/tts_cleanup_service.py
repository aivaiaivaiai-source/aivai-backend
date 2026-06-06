from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from pathlib import Path

from app.core.config import Settings, get_settings

logger = logging.getLogger(__name__)

DEFAULT_TTS_AUDIO_TTL_HOURS = 24


@dataclass(frozen=True)
class CleanupResult:
    deleted_count: int
    skipped_count: int
    ttl_hours: int
    error_count: int = 0


def resolve_tts_directory(settings: Settings | None = None) -> Path:
    cfg = settings or get_settings()
    return Path(cfg.MEDIA_ROOT).resolve() / "tts"


def cleanup_old_tts_files(
    ttl_hours: int,
    *,
    settings: Settings | None = None,
    tts_dir: Path | None = None,
) -> CleanupResult:
    """Delete .mp3 files in MEDIA_ROOT/tts older than ttl_hours; never touch other media."""
    if ttl_hours < 0:
        raise ValueError("ttl_hours must be non-negative")

    root = (tts_dir or resolve_tts_directory(settings)).resolve()
    if not root.is_dir():
        logger.info("tts_cleanup skipped reason=tts_dir_missing path=%s", root)
        return CleanupResult(deleted_count=0, skipped_count=0, ttl_hours=ttl_hours)

    cutoff = time.time() - (ttl_hours * 3600)
    deleted = 0
    skipped = 0
    errors = 0

    for entry in root.iterdir():
        if not entry.is_file():
            skipped += 1
            continue
        if entry.suffix.lower() != ".mp3":
            skipped += 1
            continue
        try:
            if not _is_under_tts_root(entry, root):
                skipped += 1
                continue
            mtime = entry.stat().st_mtime
            if mtime >= cutoff:
                skipped += 1
                continue
            entry.unlink()
            deleted += 1
        except OSError as exc:
            errors += 1
            logger.warning("tts_cleanup_delete_failed path=%s detail=%s", entry, exc)

    result = CleanupResult(
        deleted_count=deleted,
        skipped_count=skipped,
        ttl_hours=ttl_hours,
        error_count=errors,
    )
    logger.info(
        "tts_cleanup deleted=%d skipped=%d errors=%d ttl_hours=%d path=%s",
        result.deleted_count,
        result.skipped_count,
        result.error_count,
        result.ttl_hours,
        root,
    )
    return result


def _is_under_tts_root(path: Path, tts_root: Path) -> bool:
    try:
        path.resolve().relative_to(tts_root)
    except ValueError:
        return False
    return True
