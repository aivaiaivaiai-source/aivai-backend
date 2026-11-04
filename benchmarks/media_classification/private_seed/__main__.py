"""CLI: python -m benchmarks.media_classification.private_seed {prepare|label|reset-labels|freeze}"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from benchmarks.media_classification.private_seed import (
    move_screens_to_private_raw,
    prepare_private_seed_review,
)
from benchmarks.media_classification.private_seed.freeze import (
    DEFAULT_CATALOG,
    freeze_private_seed,
    is_frozen,
)
from benchmarks.media_classification.private_seed.labeling import (
    LabelingSession,
    load_and_validate_dataset,
    reset_human_labels,
)
from benchmarks.media_classification.private_seed.label_gui import run_labeling_gui

PACKAGE_DATA = Path(__file__).resolve().parents[1] / "data"
DEFAULT_PRIVATE = PACKAGE_DATA / "aivai_private_seed_v1"
DEFAULT_SRC = PACKAGE_DATA / "public_seed_v1" / "скрины"


def _git_ignored(rel: str, *, repo: Path) -> bool:
    r = subprocess.run(
        ["git", "check-ignore", "-v", rel],
        cwd=repo,
        capture_output=True,
        text=True,
    )
    return r.returncode == 0


def cmd_prepare(argv: list[str] | None = None) -> int:
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

    probe = "benchmarks/media_classification/data/aivai_private_seed_v1/raw/probe.jpg"
    if not _git_ignored(probe, repo=repo):
        raise SystemExit("STOP: private seed path is NOT gitignored")
    report["git_ignored"] = True
    report["prepare"] = prepare_private_seed_review(private_root=args.private_root)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


def cmd_label(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Offline human labeling helper for aivai private seed"
    )
    parser.add_argument("--private-root", type=Path, default=DEFAULT_PRIVATE)
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Validate dataset and print resume info without opening GUI",
    )
    args = parser.parse_args(argv)

    repo = Path(__file__).resolve().parents[3]
    probe = "benchmarks/media_classification/data/aivai_private_seed_v1/review/labels_to_review.csv"
    if not _git_ignored(probe, repo=repo):
        raise SystemExit("STOP: labels path is NOT gitignored")

    if is_frozen(args.private_root) and not args.validate_only:
        freeze_meta = {}
        fp = args.private_root / "freeze.json"
        if fp.is_file():
            freeze_meta = json.loads(fp.read_text(encoding="utf-8"))
        print(
            json.dumps(
                {
                    "status": "FROZEN",
                    "error": "dataset is frozen — label helper refuses writes",
                    "dataset_version": freeze_meta.get("dataset_version"),
                    "hint": "create aivai-private-seed-v2 for new labeling",
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 2

    load_and_validate_dataset(args.private_root)
    session = LabelingSession.open(args.private_root)
    prog = session.progress()
    resume_id = session.current_id

    if args.validate_only:
        print(
            json.dumps(
                {
                    "status": "ok",
                    "frozen": is_frozen(args.private_root),
                    "total": prog["total"],
                    "reviewed": prog["reviewed"],
                    "remaining": prog["remaining"],
                    "continue_from": resume_id,
                    "complete": prog["complete"],
                    "counts": prog["counts"],
                    "git_ignored": True,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    print(
        f"Reviewed: {prog['reviewed']} / {prog['total']}\n"
        f"Remaining: {prog['remaining']}\n"
        f"Continue from {resume_id}\n"
    )
    run_labeling_gui(session)
    return 0


def cmd_reset_labels(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Reset human labels to blank (11-class taxonomy); raw untouched"
    )
    parser.add_argument("--private-root", type=Path, default=DEFAULT_PRIVATE)
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Required to actually wipe labels",
    )
    args = parser.parse_args(argv)
    if not args.confirm:
        raise SystemExit("Refusing reset without --confirm")

    root = args.private_root
    if is_frozen(root) or (root / "freeze.json").exists():
        raise SystemExit("STOP: private dataset is frozen — refuse reset")
    for name in ("predictions.jsonl", "siglip_predictions.jsonl", "benchmark_run.json"):
        if (root / name).exists() or (root / "review" / name).exists():
            raise SystemExit(f"STOP: found model artifact {name} — refuse reset")

    result = reset_human_labels(private_root=root)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def cmd_freeze(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Freeze aivai-private-seed-v1 after 132/132 human GT"
    )
    parser.add_argument("--private-root", type=Path, default=DEFAULT_PRIVATE)
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing freeze (dangerous; default refuse)",
    )
    args = parser.parse_args(argv)

    repo = Path(__file__).resolve().parents[3]
    probe = "benchmarks/media_classification/data/aivai_private_seed_v1/freeze.json"
    if not _git_ignored(probe, repo=repo):
        raise SystemExit("STOP: private freeze path is NOT gitignored")

    result = freeze_private_seed(
        private_root=args.private_root,
        catalog_path=args.catalog,
        force=args.force,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in {"-h", "--help"}:
        print(
            "Usage: python -m benchmarks.media_classification.private_seed "
            "{prepare|label|reset-labels|freeze} ..."
        )
        return 0 if argv and argv[0] in {"-h", "--help"} else 2
    cmd = argv[0]
    rest = argv[1:]
    if cmd == "prepare":
        return cmd_prepare(rest)
    if cmd == "label":
        return cmd_label(rest)
    if cmd == "reset-labels":
        return cmd_reset_labels(rest)
    if cmd == "freeze":
        return cmd_freeze(rest)
    raise SystemExit(f"unknown command: {cmd}")


if __name__ == "__main__":
    raise SystemExit(main())
