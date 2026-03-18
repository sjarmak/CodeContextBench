#!/usr/bin/env python3
"""Automated triage pipeline for CodeScaleBench run directories.

Classifies every task in a run directory into:
  Category A — Infrastructure failure (rerun to get signal)
  Category B — Setup failure (fix setup config/environment)
  Category C — Verifier failure (fix verifier logic or format)
  Category D — Agent quality failure (genuine agent limitation)
  pass       — Task succeeded (reward > 0)

Integrates status_fingerprints.py, failure_analysis.py, and
trace_quality_pipeline.py into a single entry point.

Usage:
    python3 scripts/evaluation/triage_run.py <run_dir>
    python3 scripts/evaluation/triage_run.py <run_dir> --rerun-subset
    python3 scripts/evaluation/triage_run.py <run_dir> --output triage.json
    python3 scripts/evaluation/triage_run.py <run_dir> --config baseline
    python3 scripts/evaluation/triage_run.py <run_dir> --verbose

Output JSON structure:
    {
      "generated_at": "<iso timestamp>",
      "run_dir": "<path>",
      "summary": {"A": 3, "B": 1, "C": 2, "D": 5, "pass": 12},
      "per_task": [
        {
          "task_name": "...",
          "config": "...",
          "category": "A",
          "category_name": "infra",
          "reason": "...",
          "action": "...",
          "reward": null,
          "fingerprint": {...} | null
        },
        ...
      ],
      "rerun_subset": ["task_a", "task_b"]  // Category A tasks
    }
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Path setup — allow running from anywhere in the project
# ---------------------------------------------------------------------------

_THIS_DIR = Path(__file__).resolve().parent
_SCRIPTS_DIR = _THIS_DIR.parent
sys.path.insert(0, str(_SCRIPTS_DIR))
sys.path.insert(0, str(_THIS_DIR))

# ---------------------------------------------------------------------------
# Import shared modules with graceful fallbacks
# ---------------------------------------------------------------------------

try:
    from analysis.status_fingerprints import fingerprint_error
except ImportError:
    try:
        from status_fingerprints import fingerprint_error
    except ImportError:
        def fingerprint_error(exception_info):  # type: ignore[misc]
            return None

try:
    from evaluation.trace_quality_pipeline import classify_validity, check_setup_quality
except ImportError:
    try:
        from trace_quality_pipeline import classify_validity, check_setup_quality  # type: ignore[assignment]
    except ImportError:
        classify_validity = None  # type: ignore[assignment]
        check_setup_quality = None  # type: ignore[assignment]

# ---------------------------------------------------------------------------
# Category definitions
# ---------------------------------------------------------------------------

CATEGORIES = {
    "A": {
        "name": "infra",
        "description": "Infrastructure failure — not an agent quality signal",
        "action": "Rerun the task; the failure is environmental.",
    },
    "B": {
        "name": "setup",
        "description": "Setup failure — agent ran in misconfigured environment",
        "action": "Fix setup (MCP config, Docker image, env vars) then rerun.",
    },
    "C": {
        "name": "verifier",
        "description": "Verifier failure — output format or reward script issue",
        "action": "Inspect verifier script; fix reward.txt format or scoring logic.",
    },
    "D": {
        "name": "agent_quality",
        "description": "Agent quality failure — agent ran correctly but failed the task",
        "action": "Analyze agent trajectory for context/reasoning gaps.",
    },
    "pass": {
        "name": "pass",
        "description": "Task succeeded",
        "action": "No action required.",
    },
}

# Stage1 reasons that map to Category A (infrastructure)
_INFRA_REASONS = frozenset({
    "auth_error",
    "rate_limited",
    "docker_build_failure",
    "no_result_json",
    "corrupt_result_json",
    "agent_never_ran",
    "batch_level_result",
})

# stage1 invalid reasons that map to Category B (setup / environment)
_SETUP_REASONS = frozenset({
    "environment_error",
})

# Fingerprint severities that are infra-class
_INFRA_SEVERITIES = frozenset({"infra", "api"})

# Fingerprint severities that are setup-class
_SETUP_SEVERITIES = frozenset({"setup", "mcp"})


# ---------------------------------------------------------------------------
# Lightweight fallbacks for classify_validity / check_setup_quality
# ---------------------------------------------------------------------------

def _extract_reward(data: dict) -> Optional[float]:
    verifier = data.get("verifier_result") or {}
    rewards = verifier.get("rewards") or {}
    for key in ("reward", "score"):
        if key in rewards:
            try:
                return float(rewards[key])
            except (TypeError, ValueError):
                continue
    return None


def _classify_validity_fallback(task_dir: Path) -> dict:
    """Minimal validity check when trace_quality_pipeline is unavailable."""
    result_path = task_dir / "result.json"
    if not result_path.is_file():
        return {
            "stage1_class": "invalid",
            "stage1_reason": "no_result_json",
            "reward": None,
            "exception_info": None,
        }
    try:
        data = json.loads(result_path.read_text())
    except (json.JSONDecodeError, OSError):
        return {
            "stage1_class": "invalid",
            "stage1_reason": "corrupt_result_json",
            "reward": None,
            "exception_info": None,
        }

    reward = _extract_reward(data)
    exception_info = data.get("exception_info")

    if exception_info is not None:
        fp = fingerprint_error(exception_info)
        if fp:
            sev = fp.get("severity", "")
            if sev in _INFRA_SEVERITIES:
                return {"stage1_class": "invalid", "stage1_reason": f"infra_other:{fp['fingerprint_id']}", "reward": reward, "exception_info": exception_info}
            if sev in _SETUP_SEVERITIES:
                return {"stage1_class": "invalid", "stage1_reason": "environment_error", "reward": reward, "exception_info": exception_info}
        return {"stage1_class": "invalid", "stage1_reason": "agent_never_ran", "reward": reward, "exception_info": exception_info}

    if reward is None:
        reward_txt = task_dir / "verifier" / "reward.txt"
        if not reward_txt.is_file():
            return {"stage1_class": "invalid", "stage1_reason": "verifier_crash", "reward": None, "exception_info": None}

    return {"stage1_class": "valid", "stage1_reason": None, "reward": reward, "exception_info": exception_info}


def _check_setup_quality_fallback(task_dir: Path, config_name: str) -> dict:
    """Stub when trace_quality_pipeline is unavailable."""
    return {"stage2_class": "valid_goodsetup", "stage2_reasons": []}


# ---------------------------------------------------------------------------
# Core classification logic
# ---------------------------------------------------------------------------

def _is_verifier_failure(task_dir: Path, exception_info, reward: Optional[float]) -> bool:
    """Detect verifier-class failures in an otherwise-valid trial."""
    # Explicit verifier exception fingerprint
    if exception_info is not None:
        fp = fingerprint_error(exception_info)
        if fp and fp.get("severity") == "verifier":
            return True
        if fp and fp.get("fingerprint_id") == "verifier_parse_error":
            return True

    # reward.txt missing or malformed
    reward_txt = task_dir / "verifier" / "reward.txt"
    if not reward_txt.is_file():
        # No reward.txt but task is "valid" → verifier didn't write output
        return True

    # reward.txt exists but reward is 0 — check if stdout has error clues
    test_stdout = task_dir / "verifier" / "test-stdout.txt"
    if test_stdout.is_file():
        try:
            txt = test_stdout.read_text(errors="replace")
            lower = txt.lower()
            if any(p in lower for p in [
                "traceback", "syntaxerror", "typeerror", "attributeerror",
                "verifier error", "reward.txt", "json.decoder", "parse error",
            ]):
                return True
        except OSError:
            pass

    return False


def classify_task(task_dir: Path, config_name: str) -> dict:
    """Classify a single trial directory into a triage category.

    Returns a dict with:
        category, category_name, reason, action, reward, fingerprint
    """
    # Choose implementations
    _cv = classify_validity if classify_validity is not None else _classify_validity_fallback
    _csq = check_setup_quality if check_setup_quality is not None else _check_setup_quality_fallback

    # Stage 1: validity
    stage1 = _cv(task_dir)
    stage1_class = stage1.get("stage1_class", "invalid")
    stage1_reason = stage1.get("stage1_reason", "unknown")
    reward = stage1.get("reward")
    exception_info = stage1.get("exception_info")

    # Compute fingerprint for invalid tasks
    fingerprint = None
    if exception_info is not None:
        fingerprint = fingerprint_error(exception_info)

    if stage1_class == "invalid":
        # Batch-level result.json — skip (not a trial)
        if stage1_reason == "batch_level_result":
            return {
                "category": "skip",
                "category_name": "skip",
                "reason": "batch_level_result",
                "action": "Skipped — batch-level result, not a trial.",
                "reward": reward,
                "fingerprint": fingerprint,
            }

        # Route infra vs setup vs verifier
        if stage1_reason in _INFRA_REASONS:
            return {
                "category": "A",
                "category_name": "infra",
                "reason": stage1_reason,
                "action": CATEGORIES["A"]["action"],
                "reward": reward,
                "fingerprint": fingerprint,
            }

        if stage1_reason in _SETUP_REASONS:
            return {
                "category": "B",
                "category_name": "setup",
                "reason": stage1_reason,
                "action": CATEGORIES["B"]["action"],
                "reward": reward,
                "fingerprint": fingerprint,
            }

        if stage1_reason == "verifier_crash":
            return {
                "category": "C",
                "category_name": "verifier",
                "reason": "verifier_crash",
                "action": CATEGORIES["C"]["action"],
                "reward": reward,
                "fingerprint": fingerprint,
            }

        # infra_other:* (fingerprinted infra failures)
        if stage1_reason and stage1_reason.startswith("infra_other:"):
            # Resolve sub-reason via fingerprint severity
            if fingerprint:
                sev = fingerprint.get("severity", "infra")
                if sev in _SETUP_SEVERITIES:
                    return {
                        "category": "B",
                        "category_name": "setup",
                        "reason": stage1_reason,
                        "action": CATEGORIES["B"]["action"],
                        "reward": reward,
                        "fingerprint": fingerprint,
                    }
            return {
                "category": "A",
                "category_name": "infra",
                "reason": stage1_reason,
                "action": CATEGORIES["A"]["action"],
                "reward": reward,
                "fingerprint": fingerprint,
            }

        # Fallback unknown invalid reason → treat as infra
        return {
            "category": "A",
            "category_name": "infra",
            "reason": stage1_reason or "unknown_invalid",
            "action": CATEGORIES["A"]["action"],
            "reward": reward,
            "fingerprint": fingerprint,
        }

    # Stage 1 valid — check stage 2 setup quality
    stage2 = _csq(task_dir, config_name)
    stage2_class = stage2.get("stage2_class", "valid_goodsetup")
    stage2_reasons = stage2.get("stage2_reasons", [])

    if stage2_class == "valid_badsetup":
        return {
            "category": "B",
            "category_name": "setup",
            "reason": "bad_setup: " + ", ".join(stage2_reasons),
            "action": CATEGORIES["B"]["action"],
            "reward": reward,
            "fingerprint": fingerprint,
        }

    # Good setup — check outcome
    if reward is not None and reward > 0:
        return {
            "category": "pass",
            "category_name": "pass",
            "reason": f"reward={reward}",
            "action": CATEGORIES["pass"]["action"],
            "reward": reward,
            "fingerprint": fingerprint,
        }

    # reward == 0 or None — classify C vs D
    if _is_verifier_failure(task_dir, exception_info, reward):
        return {
            "category": "C",
            "category_name": "verifier",
            "reason": "verifier_failure_detected",
            "action": CATEGORIES["C"]["action"],
            "reward": reward,
            "fingerprint": fingerprint,
        }

    return {
        "category": "D",
        "category_name": "agent_quality",
        "reason": f"reward={reward}, setup_ok, no_infra_failure",
        "action": CATEGORIES["D"]["action"],
        "reward": reward,
        "fingerprint": fingerprint,
    }


# ---------------------------------------------------------------------------
# Run directory scanning
# ---------------------------------------------------------------------------

_SKIP_NAMES = frozenset({
    "archive", "analysis", "browse.html", "MANIFEST.json",
    "flagged_tasks.json", "flag_reclassification_review.json",
    "triage.json",
})

_SKIP_PATTERNS = (
    "__broken_verifier", "validation_test", "__v1_hinted", "__aborted",
)


def _should_skip(name: str) -> bool:
    if name in _SKIP_NAMES:
        return True
    if name.startswith("."):
        return True
    return any(pat in name for pat in _SKIP_PATTERNS)


def _extract_task_name(dirname: str) -> str:
    """Strip Harbor random suffix from trial directory name."""
    # trial names: task_name__XXXXXXX or task_name_XXXXXXX
    parts = dirname.rsplit("__", 1)
    if len(parts) == 2 and len(parts[1]) <= 8 and parts[1].isalnum():
        return parts[0]
    return dirname


def _is_trial_result(result_path: Path) -> bool:
    """Return True if result.json is a trial-level result (has task_name or trial_name)."""
    try:
        data = json.loads(result_path.read_text())
    except (json.JSONDecodeError, OSError):
        return False
    return "task_name" in data or "trial_name" in data


def _iter_trials(config_dir: Path):
    """Yield (trial_dir, task_name) pairs from a config directory.

    Handles two Harbor layouts:
      Flat:    config_dir / trial_dir / result.json
      Nested:  config_dir / task_container / trial_dir / result.json
               (task_container may itself have a batch-level result.json)
    """
    if not config_dir.is_dir():
        return
    for entry in sorted(config_dir.iterdir()):
        if not entry.is_dir() or _should_skip(entry.name):
            continue
        sub_result = entry / "result.json"
        if sub_result.is_file():
            if _is_trial_result(sub_result):
                # Flat layout: entry IS the trial dir
                task_name = _extract_task_name(entry.name)
                yield entry, task_name
                continue
            # Batch-level result.json → descend into trial subdirs
        # Either no result.json or batch-level — look for nested trial dirs
        for trial_dir in sorted(entry.iterdir()):
            if not trial_dir.is_dir() or _should_skip(trial_dir.name):
                continue
            trial_result = trial_dir / "result.json"
            if trial_result.is_file():
                task_name = _extract_task_name(trial_dir.name)
                yield trial_dir, task_name


def _discover_configs(run_dir: Path, config_filter: Optional[str] = None) -> list[str]:
    """Return config subdirectory names in run_dir."""
    configs = []
    for child in sorted(run_dir.iterdir()):
        if not child.is_dir() or _should_skip(child.name):
            continue
        if config_filter and child.name != config_filter:
            continue
        configs.append(child.name)
    return configs


def scan_run_dir(
    run_dir: Path,
    config_filter: Optional[str] = None,
) -> list[dict]:
    """Scan a run directory and classify all trials.

    Returns list of classification records (one per trial).
    """
    if not run_dir.is_dir():
        raise ValueError(f"Run directory not found: {run_dir}")

    records = []
    configs = _discover_configs(run_dir, config_filter)

    if not configs:
        # run_dir might itself be a config dir — try scanning directly
        for trial_dir, task_name in _iter_trials(run_dir):
            result = classify_task(trial_dir, run_dir.name)
            if result["category"] == "skip":
                continue
            records.append({
                "task_name": task_name,
                "config": run_dir.name,
                "trial_dir": str(trial_dir),
                **result,
            })
        return records

    for config_name in configs:
        config_dir = run_dir / config_name
        for trial_dir, task_name in _iter_trials(config_dir):
            result = classify_task(trial_dir, config_name)
            if result["category"] == "skip":
                continue
            records.append({
                "task_name": task_name,
                "config": config_name,
                "trial_dir": str(trial_dir),
                **result,
            })

    return records


# ---------------------------------------------------------------------------
# Output assembly
# ---------------------------------------------------------------------------

def build_output(
    run_dir: Path,
    records: list[dict],
    include_rerun_subset: bool = True,
) -> dict:
    """Assemble the final triage JSON output."""
    summary: dict[str, int] = {}
    for rec in records:
        cat = rec["category"]
        summary[cat] = summary.get(cat, 0) + 1

    rerun_subset = []
    if include_rerun_subset:
        rerun_subset = [
            rec["task_name"]
            for rec in records
            if rec["category"] == "A"
        ]

    # Clean per-task records (remove trial_dir for cleaner output)
    per_task = []
    for rec in records:
        per_task.append({
            "task_name": rec["task_name"],
            "config": rec["config"],
            "category": rec["category"],
            "category_name": rec["category_name"],
            "reason": rec["reason"],
            "action": rec["action"],
            "reward": rec["reward"],
            "fingerprint": rec.get("fingerprint"),
        })

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "run_dir": str(run_dir),
        "summary": summary,
        "category_legend": {
            cat: {"name": v["name"], "description": v["description"]}
            for cat, v in CATEGORIES.items()
        },
        "per_task": per_task,
        "rerun_subset": rerun_subset,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Triage a run directory: classify every task into Category A/B/C/D "
            "and output an action plan."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Categories:
  A  infra         — Infrastructure failure. Rerun the task.
  B  setup         — Setup misconfiguration. Fix then rerun.
  C  verifier      — Verifier script failure. Fix the verifier.
  D  agent_quality — Agent failure. Genuine quality signal.
""",
    )
    parser.add_argument(
        "run_dir",
        type=Path,
        help="Path to the run directory to triage.",
    )
    parser.add_argument(
        "--config", "-c",
        default=None,
        metavar="NAME",
        help="Only triage tasks in this config subdirectory.",
    )
    parser.add_argument(
        "--output", "-o",
        default=None,
        metavar="FILE",
        help="Write JSON output to FILE (default: stdout).",
    )
    parser.add_argument(
        "--rerun-subset",
        action="store_true",
        default=True,
        help="Include list of Category A tasks recommended for rerun (default: on).",
    )
    parser.add_argument(
        "--no-rerun-subset",
        action="store_false",
        dest="rerun_subset",
        help="Omit rerun_subset from output.",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Print per-task classification to stderr.",
    )
    parser.add_argument(
        "--summary-only",
        action="store_true",
        help="Print only the summary table (no per-task JSON).",
    )
    return parser.parse_args()


def _print_summary(summary: dict, records: list[dict]) -> None:
    total = sum(summary.values())
    print(f"\nTriage summary ({total} tasks):")
    print(f"  {'Cat':<6} {'Count':>6}  {'%':>5}  Description")
    print(f"  {'-'*6} {'-'*6}  {'-'*5}  {'-'*40}")
    for cat in ["A", "B", "C", "D", "pass"]:
        count = summary.get(cat, 0)
        if count == 0:
            continue
        pct = count / total * 100 if total else 0
        desc = CATEGORIES.get(cat, {}).get("description", cat)
        print(f"  {cat:<6} {count:>6}  {pct:>4.0f}%  {desc}")
    print()


def main() -> int:
    args = parse_args()
    run_dir = args.run_dir.resolve()

    if not run_dir.exists():
        print(f"ERROR: run_dir does not exist: {run_dir}", file=sys.stderr)
        return 1

    records = scan_run_dir(run_dir, config_filter=args.config)

    if not records:
        print(f"WARNING: No trial results found in {run_dir}", file=sys.stderr)

    if args.verbose:
        for rec in records:
            cat = rec["category"]
            print(f"  [{cat}] {rec['config']}/{rec['task_name']}: {rec['reason']}", file=sys.stderr)

    output = build_output(run_dir, records, include_rerun_subset=args.rerun_subset)

    if args.summary_only:
        _print_summary(output["summary"], records)
        return 0

    json_str = json.dumps(output, indent=2)

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json_str + "\n")
        print(f"Wrote triage for {len(records)} tasks to {out_path}")
        _print_summary(output["summary"], records)
    else:
        print(json_str)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
