"""CLI: python -m benchmarks.media_classification.private_seed.prepare"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from benchmarks.media_classification.private_seed import (
    move_screens_to_private_raw,
    prepare_private_seed_review,
)

PACKAGE_DATA = Path(__file__).resolve().parents[1] / "data"
DEFAULT_SRC = PACKAGE_DATA / "public_seed_v1" / "скрины"
DEFAULT_PRIVATE = PACKAGE_DATA / "aivai_private_seed_v1"
DEFAULT_RAW = DEFAULT_PRIVATE / "raw"


def _git_ignored(rel: str, *, repo: Path) -> bool:
    r = subprocess.run(
        ["git", "check-ignore", "-v", rel],
        cwd=repo,
        capture_output=True,
        text=True,
    )
    return r.returncode == 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Prepare aivai private seed for human GT")
    parser.add_argument("--src", type=Path, default=DEFAULT_SRC)
    parser.add_argument("--private-root", type=Path, default=DEFAULT_PRIVATE)
    parser.add_argument("--skip-move", action="store_true")
    args = parser.parse_args(argv)

    repo = Path(__file__).resolve().parents[3]
    report: dict = {}

    raw = args.private_root / "raw"
    if not args.skip_move:
        report["move"] = move_screens_to_private_raw(src_dir=args.src, dst_raw=raw)
    else:
        report["move"] = {"skipped": True, "raw_exists": raw.is_dir()}

    # git safety
    probe = "benchmarks/media_classification/data/aivai_private_seed_v1/raw/probe.jpg"
    if not _git_ignored(probe, repo=repo):
        raise SystemExit("STOP: private seed path is NOT gitignored")
    report["git_ignored"] = True

    report["prepare"] = prepare_private_seed_review(private_root=args.private_root)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
