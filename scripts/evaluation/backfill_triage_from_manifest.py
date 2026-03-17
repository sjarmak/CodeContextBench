#!/usr/bin/env python3
"""Backfill triage.json for current top-level runs using MANIFEST membership."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from official_runs import (
    load_manifest,
    read_triage,
    top_level_run_dirs,
    tracked_run_dirs_from_manifest,
)


def _triage_payload(decision: str, reason_code: str, reviewer: str) -> dict:
    return {
        "decision": decision,
        "reason_code": reason_code,
        "notes": "Backfilled from current MANIFEST membership.",
        "reviewed_at": datetime.now(timezone.utc).isoformat(),
        "reviewer": reviewer,
        "source": "bootstrap_manifest_backfill",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs-dir", default="./runs/official")
    parser.add_argument("--reviewer", default="system")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument(
        "--fill-untracked-as-exclude",
        action="store_true",
        help="Also write triage exclude for non-manifest top-level runs.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing triage.json files.",
    )
    args = parser.parse_args()

    runs_dir = Path(args.runs_dir)
    manifest = load_manifest(runs_dir / "MANIFEST.json")
    tracked = tracked_run_dirs_from_manifest(manifest)

    writes = []
    for run_dir in top_level_run_dirs(runs_dir):
        triage, triage_err = read_triage(run_dir)
        if triage is not None and triage_err is None and not args.overwrite:
            continue
        decision = None
        reason_code = None
        if run_dir.name in tracked:
            decision = "include"
            reason_code = "valid_official_backfill"
        elif args.fill_untracked_as_exclude:
            decision = "exclude"
            reason_code = "untracked_backfill"
        if decision is None:
            continue
        writes.append((run_dir / "triage.json", _triage_payload(decision, reason_code, args.reviewer)))

    print(f"Triages to write: {len(writes)}")
    for path, payload in writes:
        print(f"  - {path}: {payload['decision']} ({payload['reason_code']})")

    if not args.execute:
        return 0

    for path, payload in writes:
        path.write_text(json.dumps(payload, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

