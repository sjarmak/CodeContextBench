#!/usr/bin/env python3
"""Repo health gate: run required checks to keep tree clean and reduce drift.

Runs docs consistency, selection file validity, and (unless --quick) full task
preflight static checks. Exit 0 only if all required checks pass.

Usage:
    python3 scripts/repo_health.py           # Full health
    python3 scripts/repo_health.py --quick    # Docs + selection file only
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CONTRACT_PATH = REPO_ROOT / "configs" / "repo_health.json"


def load_contract() -> dict:
    """Load repo_health.json; return defaults if missing."""
    if CONTRACT_PATH.is_file():
        with open(CONTRACT_PATH) as f:
            return json.load(f)
    return {
        "checks": {
            "docs_consistency": {"script": "scripts/docs_consistency_check.py", "required": True},
            "task_preflight_static": {"script": "scripts/validate_tasks_preflight.py", "args": ["--all"], "required": True},
            "selection_file": {"script": None, "required": True},
        },
        "quick_checks": ["docs_consistency", "selection_file"],
    }


def check_selection_file(repo_root: Path) -> int:
    """Verify selected_benchmark_tasks.json exists and is valid JSON. Return 0 on success."""
    path = repo_root / "configs" / "selected_benchmark_tasks.json"
    if not path.is_file():
        print("  selection_file: FAILED (file not found)")
        return 1
    try:
        with open(path) as f:
            json.load(f)
    except json.JSONDecodeError as e:
        print(f"  selection_file: FAILED (invalid JSON: {e})")
        return 1
    print("  selection_file: OK")
    return 0


def check_launch_policy(repo_root: Path) -> int:
    """Reject raw Harbor launches and launcher scripts that bypass configs/_common.sh."""
    configs_dir = repo_root / "configs"
    raw_harbor_offenders: list[str] = []
    common_offenders: list[str] = []
    raw_harbor_pattern = re.compile(r"(^|[^\w])harbor run([^\w]|$)")
    source_common_pattern = re.compile(r"source\s+.*_common\.sh")
    helper_markers = (
        "harbor_run_guarded",
        "run_tasks_parallel",
        "run_paired_configs",
        "setup_multi_accounts",
        "setup_dual_accounts",
        "ensure_fresh_token_all",
        "preflight_rate_limits",
        "account_readiness_preflight",
        "confirm_launch",
        "load_credentials",
        "enforce_subscription_mode",
    )
    delegate_patterns = (
        re.compile(r"exec\s+.*configs/.*\.sh"),
        re.compile(r"(bash|sh)\s+.*configs/.*\.sh"),
        re.compile(r"exec\s+\"\$SCRIPT_DIR/.*\.sh\""),
        re.compile(r"(bash|sh)\s+\"\$SCRIPT_DIR/.*\.sh\""),
    )

    for script_path in sorted(configs_dir.glob("*.sh")):
        if script_path.name == "_common.sh":
            continue
        text = script_path.read_text()
        lines = text.splitlines()
        sources_common = bool(source_common_pattern.search(text))
        uses_shared_helper = any(marker in text for marker in helper_markers)
        delegates_only = any(pattern.search(text) for pattern in delegate_patterns)

        if uses_shared_helper and not sources_common:
            common_offenders.append(f"{script_path.relative_to(repo_root)}")
        elif not sources_common and not delegates_only and script_path.name not in {"build_2config.sh"}:
            if script_path.name.startswith("run_") and "harbor" not in text:
                # Pure orchestration wrappers that only call other config scripts are allowed.
                pass

        for lineno, raw_line in enumerate(lines, start=1):
            stripped = raw_line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if stripped.startswith("echo ") or stripped.startswith('echo"') or stripped.startswith("printf "):
                continue
            if raw_harbor_pattern.search(raw_line):
                raw_harbor_offenders.append(f"{script_path.relative_to(repo_root)}:{lineno}")

    if raw_harbor_offenders or common_offenders:
        print("  launch_policy: FAILED")
        if raw_harbor_offenders:
            print("    Raw `harbor run` is not allowed in configs/*.sh outside configs/_common.sh.")
            for offender in raw_harbor_offenders[:15]:
                print(f"    {offender}")
        if common_offenders:
            print("    Launcher scripts that use shared run helpers must source configs/_common.sh.")
            for offender in common_offenders[:15]:
                print(f"    {offender}")
        return 1

    print("  launch_policy: OK")
    return 0


def run_script_check(name: str, script: str, args: list[str], repo_root: Path) -> int:
    """Run a script; return its exit code."""
    cmd = [sys.executable, str(repo_root / script)] + (args or [])
    result = subprocess.run(cmd, cwd=repo_root, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  {name}: FAILED")
        if result.stdout:
            for line in result.stdout.strip().splitlines()[:15]:
                print(f"    {line}")
        if result.stderr:
            for line in result.stderr.strip().splitlines()[:5]:
                print(f"    stderr: {line}")
    else:
        print(f"  {name}: OK")
    return result.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Only run quick checks (docs_consistency, selection_file)",
    )
    parser.add_argument(
        "--contract",
        type=Path,
        default=CONTRACT_PATH,
        help="Path to repo_health.json",
    )
    args = parser.parse_args()

    contract = load_contract()
    checks = contract.get("checks") or {}
    quick_list = contract.get("quick_checks") or ["docs_consistency", "selection_file"]

    to_run = quick_list if args.quick else list(checks.keys())
    failures: list[str] = []

    print("Repo health gate")
    print("-" * 40)

    for name in to_run:
        spec = checks.get(name)
        if not spec:
            continue
        required = spec.get("required", True)

        if name == "selection_file":
            code = check_selection_file(REPO_ROOT)
        elif name == "launch_policy":
            code = check_launch_policy(REPO_ROOT)
        elif spec.get("script"):
            script = spec["script"]
            script_args = spec.get("args") or []
            code = run_script_check(name, script, script_args, REPO_ROOT)
        else:
            continue

        if code != 0 and required:
            failures.append(name)

    print("-" * 40)
    if failures:
        print(f"FAILED: {', '.join(failures)}")
        return 1
    print("All required checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
