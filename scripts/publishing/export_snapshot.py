#!/usr/bin/env python3
"""Export a snapshot for public publishing.

Resolves symlinks, sanitizes traces, validates no secrets, and writes
to docs/official_results/{snapshot_id}/.

Usage:
    python3 scripts/publishing/export_snapshot.py runs/snapshots/csb-v1-mixed371--haiku45--030326
    python3 scripts/publishing/export_snapshot.py runs/snapshots/csb-v1-mixed371--haiku45--030326 --dry-run
"""
import argparse
import json
import re
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

# Patterns that indicate secrets (same as pre-commit hook)
SECRET_PATTERNS = [
    re.compile(r"sk-ant-api\w{2}-[\w-]{40,}"),       # Anthropic API key
    re.compile(r"ghp_[A-Za-z0-9]{36,}"),              # GitHub PAT
    re.compile(r"sgp_[a-f0-9]{16}_[a-f0-9]{40}"),     # Sourcegraph token
    re.compile(r"dtn_[a-f0-9]{64}"),                   # Daytona API key
    re.compile(r"sk-proj-[\w-]{40,}"),                 # OpenAI key
    re.compile(r"AIzaSy[\w-]{33}"),                    # Google API key
    re.compile(r"lsv2_pt_[a-f0-9]{32}_[a-f0-9]{10}"), # LangSmith key
    re.compile(r"accessToken\":\"[a-f0-9]{64}"),       # Augment session token
]

# Path patterns to sanitize (replace with placeholder)
PATH_SANITIZE = [
    (re.compile(r"/home/\w+/"), "/home/user/"),
    (re.compile(r"/home/\w+"), "/home/user"),
    (re.compile(r"account\d+"), "accountN"),
    (re.compile(r"\.claude-homes/account\d+"), ".claude-homes/accountN"),
]


def sanitize_text(text: str) -> tuple[str, list[str]]:
    """Sanitize text, returning (clean_text, list_of_findings)."""
    findings = []
    for pattern in SECRET_PATTERNS:
        matches = pattern.findall(text)
        if matches:
            findings.extend(f"SECRET: {m[:20]}..." for m in matches)
            text = pattern.sub("[REDACTED]", text)

    for pattern, replacement in PATH_SANITIZE:
        text = pattern.sub(replacement, text)

    return text, findings


def export_snapshot(snap_dir: Path, dry_run: bool = False) -> int:
    manifest = json.load(open(snap_dir / "SNAPSHOT.json"))
    snap_id = manifest["snapshot_id"]
    out_dir = snap_dir / "export"

    print(f"Exporting: {snap_id}")
    print(f"  Source: {snap_dir}")
    print(f"  Target: {out_dir}")

    if out_dir.exists() and not dry_run:
        print(f"  WARNING: Target exists, removing...")
        shutil.rmtree(out_dir)

    # Collect files to export
    files_to_copy = []
    total_findings = []

    # SNAPSHOT.json
    files_to_copy.append((snap_dir / "SNAPSHOT.json", out_dir / "SNAPSHOT.json"))

    # browse.html
    if (snap_dir / "browse.html").exists():
        files_to_copy.append((snap_dir / "browse.html", out_dir / "browse.html"))

    # Summary JSONs
    for f in (snap_dir / "summary").glob("*.json"):
        files_to_copy.append((f, out_dir / "summary" / f.name))

    # Traces: resolve symlinks and copy actual files
    traces_dir = snap_dir / "traces"
    trace_count = 0
    for config_dir in sorted(traces_dir.iterdir()):
        if not config_dir.is_dir():
            continue
        config_name = config_dir.name
        for task_link in sorted(config_dir.iterdir()):
            if not task_link.is_dir():
                continue
            task_id = task_link.name
            resolved = task_link.resolve() if task_link.is_symlink() else task_link

            if not resolved.exists():
                print(f"  SKIP: broken symlink traces/{config_name}/{task_id}")
                continue

            # Copy key files only (not full agent logs)
            target_base = out_dir / "traces" / config_name / task_id
            for rel_path in [
                "result.json",
                "task_metrics.json",
                "verifier/reward.txt",
                "agent/trajectory.json",
                "agent/instruction.txt",
            ]:
                src = resolved / rel_path
                if src.exists():
                    files_to_copy.append((src, target_base / rel_path))
            trace_count += 1

    print(f"  Traces: {trace_count} tasks")
    print(f"  Files to copy: {len(files_to_copy)}")

    # Scan for secrets
    print("  Scanning for secrets...")
    secret_count = 0
    for src, dst in files_to_copy:
        if src.suffix in (".json", ".txt", ".html"):
            try:
                text = src.read_text(errors="replace")
                _, findings = sanitize_text(text)
                if findings:
                    secret_count += len(findings)
                    total_findings.extend(f"{src.name}: {f}" for f in findings)
            except Exception:
                pass

    if total_findings:
        print(f"  FOUND {secret_count} secrets (will be redacted):")
        for f in total_findings[:10]:
            print(f"    {f}")
        if len(total_findings) > 10:
            print(f"    ... and {len(total_findings) - 10} more")

    if dry_run:
        print(f"\n  [DRY RUN] Would copy {len(files_to_copy)} files to {out_dir}")
        return 0

    # Copy and sanitize
    copied = 0
    for src, dst in files_to_copy:
        dst.parent.mkdir(parents=True, exist_ok=True)
        if src.suffix in (".json", ".txt", ".html"):
            text = src.read_text(errors="replace")
            clean, _ = sanitize_text(text)
            dst.write_text(clean)
        else:
            shutil.copy2(src, dst)
        copied += 1

    print(f"  Exported {copied} files to {out_dir}")
    return 0


def main():
    parser = argparse.ArgumentParser(description="Export snapshot for public publishing")
    parser.add_argument("snapshot", help="Path to snapshot directory")
    parser.add_argument("--dry-run", action="store_true", help="Preview without copying")
    args = parser.parse_args()

    snap_dir = Path(args.snapshot)
    if not (snap_dir / "SNAPSHOT.json").exists():
        print(f"ERROR: {snap_dir} is not a valid snapshot (no SNAPSHOT.json)")
        sys.exit(1)

    sys.exit(export_snapshot(snap_dir, args.dry_run))


if __name__ == "__main__":
    main()
