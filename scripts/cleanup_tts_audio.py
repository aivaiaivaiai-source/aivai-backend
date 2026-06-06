#!/usr/bin/env python3
"""Remove expired TTS MP3 files from MEDIA_ROOT/tts.

Usage (from project root):
    python -m scripts.cleanup_tts_audio
    python -m scripts.cleanup_tts_audio --ttl-hours 24
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.config import get_settings
from app.services.tts_cleanup_service import cleanup_old_tts_files

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main(argv: list[str] | None = None) -> int:
    settings = get_settings()
    parser = argparse.ArgumentParser(description="Delete old TTS MP3 files under MEDIA_ROOT/tts")
    parser.add_argument(
        "--ttl-hours",
        type=int,
        default=settings.TTS_AUDIO_TTL_HOURS,
        help=f"Delete files older than this many hours (default: {settings.TTS_AUDIO_TTL_HOURS})",
    )
    args = parser.parse_args(argv)

    if args.ttl_hours < 0:
        parser.error("--ttl-hours must be non-negative")

    result = cleanup_old_tts_files(args.ttl_hours, settings=settings)
    logger.info(
        "tts_cleanup finished deleted=%d skipped=%d ttl_hours=%d",
        result.deleted_count,
        result.skipped_count,
        result.ttl_hours,
    )
    return 1 if result.error_count else 0


if __name__ == "__main__":
    raise SystemExit(main())
