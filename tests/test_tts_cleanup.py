from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import pytest

from app.core.config import Settings
from app.services.tts_cleanup_service import cleanup_old_tts_files, resolve_tts_directory


def _touch(path: Path, *, age_hours: float) -> None:
    ts = time.time() - (age_hours * 3600)
    os.utime(path, (ts, ts))


@pytest.fixture
def media_layout(tmp_path: Path) -> tuple[Path, Path, Path]:
    media_root = tmp_path / "media"
    tts_dir = media_root / "tts"
    listings_dir = media_root / "listings"
    tts_dir.mkdir(parents=True)
    listings_dir.mkdir(parents=True)
    return media_root, tts_dir, listings_dir


def test_old_mp3_deleted(media_layout: tuple[Path, Path, Path]) -> None:
    _, tts_dir, _ = media_layout
    old_file = tts_dir / "old-clip.mp3"
    old_file.write_bytes(b"mp3")
    _touch(old_file, age_hours=48)

    result = cleanup_old_tts_files(24, tts_dir=tts_dir)
    assert result.deleted_count == 1
    assert not old_file.exists()


def test_fresh_mp3_not_deleted(media_layout: tuple[Path, Path, Path]) -> None:
    _, tts_dir, _ = media_layout
    fresh = tts_dir / "fresh.mp3"
    fresh.write_bytes(b"mp3")
    _touch(fresh, age_hours=1)

    result = cleanup_old_tts_files(24, tts_dir=tts_dir)
    assert result.deleted_count == 0
    assert result.skipped_count == 1
    assert fresh.exists()


def test_non_mp3_not_deleted(media_layout: tuple[Path, Path, Path]) -> None:
    _, tts_dir, _ = media_layout
    txt = tts_dir / "notes.txt"
    txt.write_text("x", encoding="utf-8")
    _touch(txt, age_hours=100)

    result = cleanup_old_tts_files(24, tts_dir=tts_dir)
    assert result.deleted_count == 0
    assert txt.exists()


def test_files_outside_tts_dir_not_touched(media_layout: tuple[Path, Path, Path]) -> None:
    media_root, tts_dir, listings_dir = media_layout
    outside = listings_dir / "photo.jpg"
    outside.write_bytes(b"jpeg")
    _touch(outside, age_hours=100)

    old_in_tts = tts_dir / "expired.mp3"
    old_in_tts.write_bytes(b"mp3")
    _touch(old_in_tts, age_hours=48)

    result = cleanup_old_tts_files(24, tts_dir=tts_dir)
    assert result.deleted_count == 1
    assert outside.exists()
    assert not old_in_tts.exists()


def test_cleanup_result_counts_correct(media_layout: tuple[Path, Path, Path]) -> None:
    _, tts_dir, _ = media_layout
    for name, age in (("a.mp3", 50), ("b.mp3", 50), ("c.mp3", 1)):
        path = tts_dir / name
        path.write_bytes(b"x")
        _touch(path, age_hours=age)
    (tts_dir / "readme.txt").write_text("x", encoding="utf-8")

    result = cleanup_old_tts_files(24, tts_dir=tts_dir)
    assert result.deleted_count == 2
    assert result.skipped_count == 2
    assert result.ttl_hours == 24


def test_resolve_tts_directory_uses_media_root(tmp_path: Path) -> None:
    settings = Settings(MEDIA_ROOT=str(tmp_path / "custom_media"))
    assert resolve_tts_directory(settings) == (tmp_path / "custom_media" / "tts").resolve()


def test_cli_imports_and_runs_dry_safe(media_layout: tuple[Path, Path, Path], monkeypatch: pytest.MonkeyPatch) -> None:
    media_root, tts_dir, _ = media_layout
    settings = Settings(MEDIA_ROOT=str(media_root), TTS_AUDIO_TTL_HOURS=24)

    from scripts import cleanup_tts_audio

    monkeypatch.setattr(cleanup_tts_audio, "get_settings", lambda: settings)

    fresh = tts_dir / "keep.mp3"
    fresh.write_bytes(b"1")
    _touch(fresh, age_hours=1)

    code = cleanup_tts_audio.main(["--ttl-hours", "24"])
    assert code == 0
    assert fresh.exists()


def test_missing_tts_dir_returns_zero_deleted(tmp_path: Path) -> None:
    missing = tmp_path / "no-tts"
    result = cleanup_old_tts_files(24, tts_dir=missing)
    assert result.deleted_count == 0
    assert result.skipped_count == 0
