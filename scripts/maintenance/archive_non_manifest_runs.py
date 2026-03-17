#!/usr/bin/env python3
"""Archive non-manifest runs that are triage-excluded or structurally invalid."""

from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from official_runs import (
    detect_suite,
    load_manifest,
    load_prefix_map,
    read_triage,
    top_level_run_dirs,
    tracked_run_dirs_from_manifest,
)


def _append_archive_log(archive_dir: Path, entry: dict) -> None:
    log_path = archive_dir / "archive_log.jsonl"
    with open(log_path, "a") as f:
        f.write(json.dumps(entry) + "\n")


def _move_to_archive(run_dir: Path, archive_dir: Path) -> Path:
    archive_dir.mkdir(parents=True, exist_ok=True)
    dest = archive_dir / run_dir.name
    if dest.exists():
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        dest = archive_dir / f"{run_dir.name}__archived_{ts}"
    shutil.move(str(run_dir), str(dest))
    return dest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs-dir", default="./runs/official", help="Path to runs/official")
    parser.add_argument(
        "--include-structural-invalid",
        action="store_true",
        help="Also archive dirs with unknown prefix that are not in manifest (requires non-pending triage).",
    )
    parser.add_argument("--execute", action="store_true", help="Perform archive move (default: dry-run).")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args()

    runs_dir = Path(args.runs_dir)
    archive_dir = runs_dir / "archive"
    manifest = load_manifest(runs_dir / "MANIFEST.json")
    tracked = tracked_run_dirs_from_manifest(manifest)
    prefix_map = load_prefix_map(Path(__file__).resolve().parent.parent)

    candidates: list[tuple[Path, str]] = []
    skipped_pending: list[str] = []

    for run_dir in top_level_run_dirs(runs_dir):
        name = run_dir.name
        triage, triage_err = read_triage(run_dir)
        decision = triage.get("decision") if triage else None

        if decision == "pending" or triage_err in {"missing", "invalid_json", "invalid_type", "invalid_decision"}:
            skipped_pending.append(name)
            continue

        if decision == "include":
            continue

        if name in tracked:
            # Never archive tracked runs.
            continue

        if decision == "exclude":
            candidates.append((run_dir, "triage_exclude"))
            continue

        if args.include_structural_invalid:
            suite = detect_suite(name, prefix_map)
            if suite is None:
                candidates.append((run_dir, "structural_invalid_unknown_prefix"))

    if args.format == "json":
        payload = {
            "execute": args.execute,
            "candidates": [{"run_dir": p.name, "reason": reason} for p, reason in candidates],
            "skipped_pending": skipped_pending,
        }
        print(json.dumps(payload, indent=2))
    else:
        print(f"Candidates: {len(candidates)}")
        for p, reason in candidates:
            print(f"  - {p.name} ({reason})")
        if skipped_pending:
            print(f"Skipped pending/missing triage: {len(skipped_pending)}")

    if not args.execute:
        return 0

    for run_dir, reason in candidates:
        dest = _move_to_archive(run_dir, archive_dir)
        _append_archive_log(
            archive_dir,
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "source": str(run_dir),
                "destination": str(dest),
                "reason": reason,
            },
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

