from __future__ import annotations

from pathlib import Path

import pytest

from scripts import cleanup_tts_audio

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEPLOYMENT_DIR = PROJECT_ROOT / "docs" / "deployment"

DEPLOYMENT_FILES = [
    "tts-cleanup.md",
    "tts-cleanup-systemd.service.example",
    "tts-cleanup-systemd.timer.example",
    "tts-cleanup-cron.example",
    "tts-cleanup-k8s-cronjob.example.yaml",
    "tts-cleanup-docker-compose.override.example.yml",
]


@pytest.mark.parametrize("filename", DEPLOYMENT_FILES)
def test_deployment_docs_exist(filename: str) -> None:
    path = DEPLOYMENT_DIR / filename
    assert path.is_file(), f"missing deployment doc: {path}"


def test_main_doc_mentions_tts_scope_and_safety() -> None:
    text = (DEPLOYMENT_DIR / "tts-cleanup.md").read_text(encoding="utf-8")
    assert "MEDIA_ROOT/tts" in text or "media/tts" in text
    assert "listing images" in text.lower() or "listing image" in text.lower()
    assert "placeholder" in text.lower()
    assert "python -m scripts.cleanup_tts_audio" in text
    assert "TTS_AUDIO_TTL_HOURS" in text


def test_examples_reference_cleanup_command() -> None:
    for name in (
        "tts-cleanup-systemd.service.example",
        "tts-cleanup-cron.example",
        "tts-cleanup-k8s-cronjob.example.yaml",
        "tts-cleanup-docker-compose.override.example.yml",
    ):
        content = (DEPLOYMENT_DIR / name).read_text(encoding="utf-8")
        assert "scripts.cleanup_tts_audio" in content


def test_k8s_example_is_cronjob() -> None:
    content = (DEPLOYMENT_DIR / "tts-cleanup-k8s-cronjob.example.yaml").read_text(encoding="utf-8")
    assert "kind: CronJob" in content
    assert "schedule:" in content


def test_systemd_timer_runs_daily() -> None:
    content = (DEPLOYMENT_DIR / "tts-cleanup-systemd.timer.example").read_text(encoding="utf-8")
    assert "[Timer]" in content
    assert "OnCalendar=" in content


def test_cleanup_script_import_still_works() -> None:
    assert cleanup_tts_audio.main is not None
    assert callable(cleanup_tts_audio.main)
