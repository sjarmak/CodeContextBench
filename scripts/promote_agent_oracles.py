#!/usr/bin/env python3
"""Promote validated agent oracles to become canonical ground truth files.

Scans benchmarks/ for *_agent.json files, checks promotion gates
(dual-verification >= 80%, cross-validation F1 >= 0.6), and copies
agent oracles to become the canonical ground truth files.

Usage:
    # Dry run (preview what would be promoted)
    python3 scripts/promote_agent_oracles.py --dry-run

    # Promote with threshold checks
    python3 scripts/promote_agent_oracles.py

    # Force promote (skip threshold gates)
    python3 scripts/promote_agent_oracles.py --force

    # Promote specific suite
    python3 scripts/promote_agent_oracles.py --suite ccb_fix
"""

import argparse
import json
import logging
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, List

log = logging.getLogger("promote_agent_oracles")

# Promotion gates
DUAL_VERIFICATION_THRESHOLD = 0.80  # Require >= 80% dual-verified files
CROSS_VALIDATION_F1_THRESHOLD = 0.60  # Require >= 0.6 F1 from cross-validation


def find_project_root() -> Path:
    p = Path(__file__).resolve().parent
    while p != p.parent:
        if (p / "benchmarks").is_dir():
            return p
        p = p.parent
    return Path(__file__).resolve().parent.parent


def load_cross_validation_results(root: Path) -> Dict[str, float]:
    """Load per-task cross-validation F1 from summary.json."""
    cv_path = root / "results" / "cross_validation" / "summary.json"
    if not cv_path.exists():
        log.warning("No cross-validation results at %s", cv_path)
        return {}

    data = json.loads(cv_path.read_text())
    task_f1s = {}
    for entry in data.get("per_task", []):
        task_key = entry.get("task", "")
        f1 = entry.get("f1", 0)
        task_f1s[task_key] = f1
    return task_f1s


def discover_agent_oracles(
    root: Path, suite: str = ""
) -> List[Dict[str, Any]]:
    """Find all agent-generated oracle files in benchmarks/."""
    benchmarks = root / "benchmarks"
    results = []

    suites = []
    if suite:
        suites = [suite]
    else:
        for d in sorted(benchmarks.iterdir()):
            if d.is_dir() and d.name.startswith("ccb_"):
                suites.append(d.name)

    for s in suites:
        suite_dir = benchmarks / s
        if not suite_dir.is_dir():
            continue

        for task_dir in sorted(suite_dir.iterdir()):
            if not task_dir.is_dir():
                continue
            tests = task_dir / "tests"
            if not tests.is_dir():
                continue

            # Check for agent oracle
            is_mcp = s.startswith("ccb_mcp_")
            if is_mcp:
                agent_path = tests / "oracle_answer_agent.json"
                canonical_path = tests / "oracle_answer.json"
            else:
                agent_path = tests / "ground_truth_agent.json"
                canonical_path = tests / "ground_truth.json"

            if not agent_path.exists():
                continue

            # Read agent oracle for metadata
            try:
                data = json.loads(agent_path.read_text())
            except (json.JSONDecodeError, OSError) as e:
                log.warning("Error reading %s: %s", agent_path, e)
                continue

            metadata = data.get("_metadata", {})
            dual_v = metadata.get("dual_verification", {})

            results.append({
                "task_dir": task_dir,
                "suite": s,
                "task_name": task_dir.name,
                "task_key": f"{s}/{task_dir.name}",
                "agent_path": agent_path,
                "canonical_path": canonical_path,
                "canonical_exists": canonical_path.exists(),
                "is_mcp": is_mcp,
                "dual_verification": dual_v,
                "metadata": metadata,
            })

    return results


def check_promotion_gates(
    entry: Dict[str, Any],
    cv_f1s: Dict[str, float],
    force: bool = False,
) -> Dict[str, Any]:
    """Check if an agent oracle passes promotion gates.

    Returns dict with gate results and overall pass/fail.
    """
    gates = {}

    # Gate 1: Dual verification >= 80%
    dv = entry.get("dual_verification", {})
    n_total = dv.get("n_total", 0)
    n_dual = dv.get("n_dual_verified", 0)
    if n_total > 0:
        dv_rate = n_dual / n_total
    else:
        dv_rate = 0.0  # No verification data = fail gate
    gates["dual_verification"] = {
        "value": round(dv_rate, 4),
        "threshold": DUAL_VERIFICATION_THRESHOLD,
        "passed": dv_rate >= DUAL_VERIFICATION_THRESHOLD or force,
        "detail": f"{n_dual}/{n_total} files dual-verified",
    }

    # Gate 2: Cross-validation F1 >= 0.6
    cv_f1 = cv_f1s.get(entry["task_key"], -1)
    if cv_f1 >= 0:
        cv_passed = cv_f1 >= CROSS_VALIDATION_F1_THRESHOLD
    else:
        # No cross-validation data available — pass by default
        cv_passed = True
    gates["cross_validation_f1"] = {
        "value": round(cv_f1, 4) if cv_f1 >= 0 else None,
        "threshold": CROSS_VALIDATION_F1_THRESHOLD,
        "passed": cv_passed or force,
        "detail": f"F1={cv_f1:.4f}" if cv_f1 >= 0 else "no data (skipped)",
    }

    all_passed = all(g["passed"] for g in gates.values())
    return {"passed": all_passed, "gates": gates}


def promote_oracle(
    entry: Dict[str, Any],
    dry_run: bool = False,
) -> bool:
    """Copy agent oracle to canonical path, backing up original."""
    agent_path = entry["agent_path"]
    canonical_path = entry["canonical_path"]

    if dry_run:
        action = "OVERWRITE" if canonical_path.exists() else "CREATE"
        log.info("  [DRY-RUN] Would %s %s", action, canonical_path)
        return True

    # Backup existing canonical
    if canonical_path.exists():
        bak = canonical_path.with_suffix(".json.bak")
        shutil.copy2(str(canonical_path), str(bak))
        log.info("  Backed up: %s -> %s", canonical_path.name, bak.name)

    # Copy agent oracle -> canonical
    shutil.copy2(str(agent_path), str(canonical_path))
    log.info("  Promoted: %s -> %s", agent_path.name, canonical_path.name)
    return True


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Promote validated agent oracles to canonical ground truth"
    )
    parser.add_argument(
        "--suite", type=str, default="",
        help="Only promote oracles in this suite",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Preview what would be promoted without writing",
    )
    parser.add_argument(
        "--force", action="store_true",
        help="Override threshold gates and promote all agent oracles",
    )
    parser.add_argument(
        "--verbose", action="store_true",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    root = find_project_root()

    # Discover agent oracles
    entries = discover_agent_oracles(root, suite=args.suite)
    if not entries:
        log.info("No agent oracles found.")
        return 0

    log.info("Found %d agent oracles", len(entries))

    # Load cross-validation results
    cv_f1s = load_cross_validation_results(root)
    if cv_f1s:
        log.info("Loaded cross-validation F1 for %d tasks", len(cv_f1s))

    # Check gates and promote
    promoted = 0
    skipped = 0
    failed_gates = []

    for entry in entries:
        task_key = entry["task_key"]
        gate_result = check_promotion_gates(entry, cv_f1s, force=args.force)

        if not gate_result["passed"]:
            skipped += 1
            failed_reason = "; ".join(
                f"{k}: {v['detail']}"
                for k, v in gate_result["gates"].items()
                if not v["passed"]
            )
            failed_gates.append({"task": task_key, "reason": failed_reason})
            log.info("[SKIP] %s — %s", task_key, failed_reason)
            continue

        log.info("[PROMOTE] %s", task_key)
        if promote_oracle(entry, dry_run=args.dry_run):
            promoted += 1

    # Summary
    print(f"\n{'=' * 60}")
    print("Oracle Promotion Summary")
    print(f"{'=' * 60}")
    print(f"Total agent oracles: {len(entries)}")
    print(f"Promoted: {promoted}")
    print(f"Skipped (failed gates): {skipped}")
    if args.dry_run:
        print("\n** DRY RUN — no files were written **")
    if args.force:
        print("\n** FORCE MODE — all threshold gates were overridden **")

    if failed_gates:
        print(f"\nFailed gate details:")
        for fg in failed_gates[:20]:
            print(f"  {fg['task']}: {fg['reason']}")

    if promoted > 0 and not args.dry_run:
        print(
            "\nReminder: run `python3 scripts/hydrate_task_specs.py` "
            "to update task_spec.json files from promoted oracles."
        )
    print(f"{'=' * 60}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
