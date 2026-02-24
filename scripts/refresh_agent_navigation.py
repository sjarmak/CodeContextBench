#!/usr/bin/env python3
"""Regenerate or verify agent-navigation artifacts with one command."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

COMMANDS = [
    [sys.executable, "scripts/sync_agent_guides.py"],
    [sys.executable, "scripts/generate_script_registry.py"],
    [sys.executable, "scripts/generate_script_index.py"],
    [sys.executable, "scripts/generate_start_here_by_task.py"],
]


def run(cmd: list[str], check_mode: bool) -> int:
    if check_mode:
        cmd = [*cmd, "--check"]
    print("$", " ".join(cmd))
    result = subprocess.run(cmd, cwd=ROOT)
    return result.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Fail if generated artifacts are stale")
    args = parser.parse_args()

    failures = 0
    for cmd in COMMANDS:
        failures += 1 if run(cmd, args.check) != 0 else 0

    if failures:
        print(f"Agent navigation refresh: FAILED ({failures} step(s))")
        return 1
    print("Agent navigation refresh: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
