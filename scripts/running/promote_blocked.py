#!/usr/bin/env python3
"""Retry archive promotion for previously blocked rows.

Reads a TSV with copy-error rows (default:
runs/validation/archive_promotion_execution_copy_errors_20260304.tsv),
retries copying each source trial dir from runs/archive into the
destination path recorded in the TSV, and writes a retry log.

Typical usage:
  sudo python3 scripts/promote_blocked.py
  sudo python3 scripts/promote_blocked.py --regenerate-manifest
"""

from __future__ import annotations

import argparse
import csv
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from official_runs import raw_runs_dir


PROJECT_ROOT = Path(__file__).resolve().parent.parent
OFFICIAL_ROOT = PROJECT_ROOT / "runs" / "official"
OFFICIAL_RAW_ROOT = raw_runs_dir(OFFICIAL_ROOT)
DEFAULT_INPUT = (
    PROJECT_ROOT
    / "runs"
    / "validation"
    / "archive_promotion_execution_copy_errors_20260304.tsv"
)
DEFAULT_LOG_JSON = (
    PROJECT_ROOT / "runs" / "validation" / "archive_promotion_retry_20260304.json"
)
DEFAULT_LOG_TSV = (
    PROJECT_ROOT / "runs" / "validation" / "archive_promotion_retry_20260304.tsv"
)
MANIFEST_SCRIPT = PROJECT_ROOT / "scripts" / "generate_manifest.py"


def mode_group_from_config(name: str) -> str | None:
    c = name.lower()
    if c.startswith("baseline"):
        return "baseline"
    if c == "mcp" or c.startswith("mcp-") or c.startswith("sourcegraph"):
        return "mcp"
    return None


def derive_destination(rel_path: str) -> Path:
    """Map archived rel_path to canonical runs/official destination path."""
    parts = rel_path.split("/")
    cfg_idx = None
    for i, p in enumerate(parts):
        if mode_group_from_config(p) is not None:
            cfg_idx = i
            break

    if cfg_idx is None:
        # Old promoted shape: run_dir/task_dir
        run_dir = parts[0]
        tail = parts[1:]
    else:
        # Container wrappers -> canonical run dir is segment before config dir
        run_dir = parts[cfg_idx - 1] if cfg_idx > 0 else parts[0]
        tail = parts[cfg_idx:]

    return OFFICIAL_RAW_ROOT / run_dir / Path(*tail)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--input-tsv",
        type=Path,
        default=DEFAULT_INPUT,
        help=f"Input TSV (default: {DEFAULT_INPUT})",
    )
    p.add_argument(
        "--log-json",
        type=Path,
        default=DEFAULT_LOG_JSON,
        help=f"Retry log JSON (default: {DEFAULT_LOG_JSON})",
    )
    p.add_argument(
        "--log-tsv",
        type=Path,
        default=DEFAULT_LOG_TSV,
        help=f"Retry log TSV (default: {DEFAULT_LOG_TSV})",
    )
    p.add_argument(
        "--regenerate-manifest",
        action="store_true",
        help="Run scripts/generate_manifest.py after retry pass.",
    )
    return p.parse_args()


def main() -> int:
    args = parse_args()
    if not args.input_tsv.is_file():
        print(f"ERROR: missing input TSV: {args.input_tsv}")
        return 2

    entries: list[dict] = []
    with args.input_tsv.open() as f:
        reader = csv.DictReader(f, delimiter="\t")
        required = {"rel_path", "task_name", "mode_group"}
        if not required.issubset(reader.fieldnames or set()):
            print(
                f"ERROR: {args.input_tsv} missing required columns: {sorted(required)}"
            )
            return 2
        for row in reader:
            entries.append(row)

    copied = 0
    skipped_missing = 0
    failed = 0
    retry_rows: list[dict] = []

    for row in entries:
        rel_path = row["rel_path"]
        src = PROJECT_ROOT / "runs" / "archive" / rel_path
        dst_raw = row.get("destination", "").strip()
        dst = Path(dst_raw) if dst_raw else derive_destination(rel_path)
        status = ""
        reason = ""
        err = ""

        if not src.exists():
            status = "skipped"
            reason = "source_missing"
            skipped_missing += 1
        else:
            try:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copytree(src, dst, dirs_exist_ok=True, symlinks=True)
                status = "copied"
                reason = "promoted"
                copied += 1
            except Exception as e:  # noqa: BLE001
                status = "failed"
                reason = "copy_error"
                err = f"{type(e).__name__}: {e}"
                failed += 1

        retry_rows.append(
            {
                "rel_path": rel_path,
                "task_name": row["task_name"],
                "mode_group": row["mode_group"],
                "source": str(src),
                "destination": str(dst),
                "status": status,
                "reason": reason,
                "error": err,
            }
        )

    args.log_tsv.parent.mkdir(parents=True, exist_ok=True)
    args.log_json.parent.mkdir(parents=True, exist_ok=True)

    with args.log_tsv.open("w", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(
            [
                "rel_path",
                "task_name",
                "mode_group",
                "source",
                "destination",
                "status",
                "reason",
                "error",
            ]
        )
        for r in retry_rows:
            w.writerow(
                [
                    r["rel_path"],
                    r["task_name"],
                    r["mode_group"],
                    r["source"],
                    r["destination"],
                    r["status"],
                    r["reason"],
                    r["error"],
                ]
            )

    manifest_rc = None
    if args.regenerate_manifest:
        manifest_rc = subprocess.run(
            ["python3", str(MANIFEST_SCRIPT)], cwd=str(PROJECT_ROOT)
        ).returncode

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "input_tsv": str(args.input_tsv),
        "input_rows": len(entries),
        "copied": copied,
        "skipped_source_missing": skipped_missing,
        "failed_copy_error": failed,
        "regenerate_manifest": bool(args.regenerate_manifest),
        "manifest_rc": manifest_rc,
        "log_tsv": str(args.log_tsv),
        "log_json": str(args.log_json),
        "rows": retry_rows,
    }
    args.log_json.write_text(json.dumps(payload, indent=2))

    print(f"input_rows={len(entries)} copied={copied} skipped_missing={skipped_missing} failed={failed}")
    if args.regenerate_manifest:
        print(f"manifest_rc={manifest_rc}")
    print(f"log_tsv={args.log_tsv}")
    print(f"log_json={args.log_json}")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
