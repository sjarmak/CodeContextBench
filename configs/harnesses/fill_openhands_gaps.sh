#!/bin/bash
# fill_openhands_gaps.sh
#
# One-command OpenHands gap detection and execution.
#
# Scans runs/staging/, runs/official/, and polecats/*/runs/ for completed OH
# trials, computes gaps against selected_benchmark_tasks.json x 2 configs
# (baseline-local-direct, mcp-remote-direct), and launches openhands_2config.sh
# for only the missing tasks/configs.
#
# Usage:
#   ./configs/harnesses/fill_openhands_gaps.sh [OPTIONS]
#
# Options:
#   --dry-run              Show gaps and write gap report; do NOT launch
#   --baseline-only        Only fill baseline-local-direct gaps
#   --full-only            Only fill mcp-remote-direct gaps
#   --gap-file PATH        Write gap report JSON to PATH (default: auto)
#   --model MODEL          Override model (passed to openhands_2config.sh)
#   --category CATEGORY    Category label for runs dir (default: staging)
#   --parallel N           Max parallel jobs (passed to openhands_2config.sh)
#
# Gap detection:
#   A task+config pair is "complete" when any trial for that task has a
#   verifier/validation_result.json with status "scored" (verifier ran).
#   Any other outcome (error, missing file) is treated as a gap.
#
# Resume support:
#   Re-run this script at any time; it re-scans results and only launches
#   what is still missing.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$REPO_ROOT"

SELECTION_FILE="$SCRIPT_DIR/selected_benchmark_tasks.json"

DRY_RUN=false
BASELINE_ONLY=false
FULL_ONLY=false
GAP_FILE=""
MODEL_ARG=""
CATEGORY_ARG=""
PARALLEL_ARG=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --baseline-only)
            if [ "$FULL_ONLY" = true ]; then
                echo "ERROR: --baseline-only and --full-only are mutually exclusive"
                exit 1
            fi
            BASELINE_ONLY=true
            shift
            ;;
        --full-only)
            if [ "$BASELINE_ONLY" = true ]; then
                echo "ERROR: --baseline-only and --full-only are mutually exclusive"
                exit 1
            fi
            FULL_ONLY=true
            shift
            ;;
        --gap-file)
            GAP_FILE="$2"
            shift 2
            ;;
        --model)
            MODEL_ARG="$2"
            shift 2
            ;;
        --category)
            CATEGORY_ARG="$2"
            shift 2
            ;;
        --parallel)
            PARALLEL_ARG="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--dry-run] [--baseline-only] [--full-only] [--gap-file PATH] [--model MODEL] [--category CAT] [--parallel N]"
            exit 1
            ;;
    esac
done

if [ ! -f "$SELECTION_FILE" ]; then
    echo "ERROR: selection file not found: $SELECTION_FILE"
    exit 1
fi

TIMESTAMP=$(date +%Y%m%d_%H%M%S)

if [ -z "$GAP_FILE" ]; then
    GAP_FILE="/tmp/oh_gaps_${TIMESTAMP}.json"
fi

echo "=============================================="
echo "OpenHands Gap Detector"
echo "=============================================="
echo "Selection file: $SELECTION_FILE"
echo "Gap file:       $GAP_FILE"
echo "Dry run:        $DRY_RUN"
echo "Baseline only:  $BASELINE_ONLY"
echo "Full only:      $FULL_ONLY"
echo ""

# ---------------------------------------------------------------------------
# Python: gap detection (runs once; __KEY=VALUE lines carry metadata out)
# ---------------------------------------------------------------------------
_py_out=$(python3 - "$SELECTION_FILE" "$REPO_ROOT" "$GAP_FILE" <<'PYEOF'
import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

selection_file = sys.argv[1]
repo_root = Path(sys.argv[2])
gap_file = sys.argv[3]

CONFIGS = ["baseline-local-direct", "mcp-remote-direct"]

# ---- Load active task list ------------------------------------------------
with open(selection_file) as f:
    sel_data = json.load(f)

active_tasks = [t for t in sel_data.get("tasks", []) if not t.get("excluded", False)]
task_by_id = {t["task_id"]: t for t in active_tasks}
print(f"Active tasks in selection: {len(active_tasks)}")

# ---- Extract task_id from a trial's config.json ---------------------------

def _extract_task_id(config_path):
    """Return task_id string or None."""
    try:
        with open(config_path) as f:
            cfg = json.load(f)
        path = cfg.get("task", {}).get("path", "").rstrip("/")
        if not path:
            return None
        basename = os.path.basename(path)
        # MCP temp dir: /tmp/mcp_{safe_task_id}_{8-hex}
        # safe_task_id == task_id.lower() for typical task IDs (only [-a-z0-9])
        if basename.startswith("mcp_"):
            inner = basename[4:]  # strip "mcp_"
            # inner = "{safe_task_id}_{8-hex}"
            parts = inner.rsplit("_", 1)
            if (len(parts) == 2
                    and len(parts[1]) == 8
                    and re.fullmatch(r"[0-9a-f]{8}", parts[1])):
                return parts[0]  # safe_task_id
            return inner  # fallback
        else:
            # Baseline: task path ends with task_id directory
            return basename
    except Exception:
        return None


def _is_valid_result(trial_dir):
    """True if trial has a scored validation_result.json."""
    vr_path = os.path.join(trial_dir, "verifier", "validation_result.json")
    if not os.path.isfile(vr_path):
        return False
    try:
        with open(vr_path) as f:
            vr = json.load(f)
        return vr.get("status") == "scored"
    except Exception:
        return False


# ---- Scan result locations ------------------------------------------------

# completed[config] = set of task_ids with valid results
completed = defaultdict(set)

def _scan_config_dir(config_dir, config_name):
    """
    Walk a config subdir (e.g. .../baseline-local-direct/) and collect
    completed task IDs.

    Harbor structure:
      config_dir/{harbor_run_dir}/trial_name/config.json
    """
    if not os.path.isdir(config_dir):
        return
    for run_entry in os.listdir(config_dir):
        run_path = os.path.join(config_dir, run_entry)
        if not os.path.isdir(run_path):
            continue
        for trial_entry in os.listdir(run_path):
            trial_path = os.path.join(run_path, trial_entry)
            if not os.path.isdir(trial_path):
                continue
            config_json = os.path.join(trial_path, "config.json")
            if not os.path.isfile(config_json):
                continue
            if not _is_valid_result(trial_path):
                continue
            task_id = _extract_task_id(config_json)
            if task_id and task_id.lower() in task_by_id:
                completed[config_name].add(task_id.lower())


def _scan_oh_run_dir(run_dir):
    """Scan a directory that may contain baseline/mcp config subdirs."""
    for config_name in CONFIGS:
        config_path = os.path.join(run_dir, config_name)
        if os.path.isdir(config_path):
            _scan_config_dir(config_path, config_name)


def _is_oh_run_dir(d):
    """Heuristic: directory has at least one known OH config subdir."""
    for config_name in CONFIGS:
        if os.path.isdir(os.path.join(d, config_name)):
            return True
    return False


scan_roots = []
for subdir in ("staging", "official"):
    p = repo_root / "runs" / subdir
    if p.is_dir():
        scan_roots.append(p)
# polecats/*/runs/
polecats_dir = repo_root / "polecats"
if polecats_dir.is_dir():
    for polecat_runs in polecats_dir.glob("*/runs"):
        if polecat_runs.is_dir():
            scan_roots.append(polecat_runs)

print(f"Scanning {len(scan_roots)} result root(s)...")
scanned_oh_runs = 0
for root in scan_roots:
    for entry in os.listdir(root):
        entry_path = os.path.join(root, entry)
        if not os.path.isdir(entry_path):
            continue
        if _is_oh_run_dir(entry_path):
            _scan_oh_run_dir(entry_path)
            scanned_oh_runs += 1

print(f"Scanned {scanned_oh_runs} OH run director(ies)")
for cfg in CONFIGS:
    print(f"  {cfg}: {len(completed[cfg])} completed tasks")
print()

# ---- Compute gaps ---------------------------------------------------------

gap_tasks = []
for task in active_tasks:
    tid = task["task_id"]
    needs = []
    for cfg in CONFIGS:
        if tid not in completed[cfg]:
            needs.append(cfg)
    if needs:
        gap_tasks.append({
            "task_id": tid,
            "benchmark": task.get("benchmark", ""),
            "task_dir": task.get("task_dir", ""),
            "needs": needs,
        })

total_needed = len(active_tasks) * len(CONFIGS)
total_done = sum(len(completed[cfg]) for cfg in CONFIGS)
total_gaps = sum(len(t["needs"]) for t in gap_tasks)

print(f"Coverage: {total_done}/{total_needed} task+config pairs complete")
print(f"Gaps:     {total_gaps} task+config pair(s) across {len(gap_tasks)} task(s)")
print()

for cfg in CONFIGS:
    needs_cfg = [t for t in gap_tasks if cfg in t["needs"]]
    print(f"  {cfg}: {len(needs_cfg)} task(s) missing")

# ---- Write gap report JSON ------------------------------------------------

import datetime
gap_report = {
    "generated_at": datetime.datetime.utcnow().isoformat() + "Z",
    "selection_file": str(selection_file),
    "total_active_tasks": len(active_tasks),
    "configs": CONFIGS,
    "completed": {cfg: sorted(completed[cfg]) for cfg in CONFIGS},
    "gaps": gap_tasks,
    "summary": {
        "total_task_config_pairs": total_needed,
        "completed_pairs": total_done,
        "gap_pairs": total_gaps,
        "gap_tasks": len(gap_tasks),
    },
}

with open(gap_file, "w") as f:
    json.dump(gap_report, f, indent=2)
print(f"\nGap report: {gap_file}")

# ---- Write subset JSONs for openhands_2config.sh --------------------------

baseline_gaps = [t for t in gap_tasks if "baseline-local-direct" in t["needs"]]
full_gaps     = [t for t in gap_tasks if "mcp-remote-direct" in t["needs"]]

def _make_subset(gap_list):
    return {"tasks": [task_by_id[g["task_id"]] for g in gap_list if g["task_id"] in task_by_id]}

stem = Path(gap_file).stem  # e.g. oh_gaps_20260318_224125
ts_part = stem.replace("oh_gaps_", "", 1)  # e.g. 20260318_224125
gap_dir = Path(gap_file).parent

baseline_subset = gap_dir / f"oh_gaps_baseline_{ts_part}.json"
full_subset     = gap_dir / f"oh_gaps_full_{ts_part}.json"

with open(baseline_subset, "w") as f:
    json.dump(_make_subset(baseline_gaps), f, indent=2)
with open(full_subset, "w") as f:
    json.dump(_make_subset(full_gaps), f, indent=2)

print(f"Baseline subset ({len(baseline_gaps)} tasks): {baseline_subset}")
print(f"Full/MCP subset ({len(full_gaps)} tasks): {full_subset}")

# Machine-readable metadata for the shell script (grep'd out of display)
print(f"__BASELINE_COUNT={len(baseline_gaps)}")
print(f"__FULL_COUNT={len(full_gaps)}")
print(f"__BASELINE_SUBSET={baseline_subset}")
print(f"__FULL_SUBSET={full_subset}")
PYEOF
)
_py_exit=$?

# Display human-readable lines, suppress __KEY=VALUE lines
echo "$_py_out" | grep -v "^__"

if [ "$_py_exit" -ne 0 ]; then
    echo "ERROR: Gap detection failed (exit $_py_exit). Check output above." >&2
    exit "$_py_exit"
fi

# Extract metadata from captured output (use sed to handle paths with '=')
_BASELINE_COUNT=$(echo "$_py_out" | grep "^__BASELINE_COUNT=" | sed 's/^__BASELINE_COUNT=//')
_FULL_COUNT=$(echo "$_py_out" | grep "^__FULL_COUNT=" | sed 's/^__FULL_COUNT=//')
_BASELINE_SUBSET=$(echo "$_py_out" | grep "^__BASELINE_SUBSET=" | sed 's/^__BASELINE_SUBSET=//')
_FULL_SUBSET=$(echo "$_py_out" | grep "^__FULL_SUBSET=" | sed 's/^__FULL_SUBSET=//')

echo ""
echo "Baseline gaps: ${_BASELINE_COUNT:-0} tasks"
echo "MCP-full gaps: ${_FULL_COUNT:-0} tasks"

if [ "${_BASELINE_COUNT:-0}" -eq 0 ] && [ "${_FULL_COUNT:-0}" -eq 0 ]; then
    echo ""
    echo "No gaps detected. Coverage is complete!"
    exit 0
fi

if [ "$DRY_RUN" = true ]; then
    echo ""
    echo "Dry run — not launching. Gap report: $GAP_FILE"
    exit 0
fi

# ---------------------------------------------------------------------------
# Copy subset files into configs/harnesses/ so openhands_2config.sh can
# reference them with --subset (relative to its SCRIPT_DIR).
# Cleanup registered via trap so files are removed even on error/interrupt.
# ---------------------------------------------------------------------------

_BASELINE_SUBSET_NAME="oh_gaps_baseline_${TIMESTAMP}.json"
_FULL_SUBSET_NAME="oh_gaps_full_${TIMESTAMP}.json"
_HARNESS_BASELINE="$SCRIPT_DIR/$_BASELINE_SUBSET_NAME"
_HARNESS_FULL="$SCRIPT_DIR/$_FULL_SUBSET_NAME"

_cleanup_harness_subsets() {
    rm -f "$_HARNESS_BASELINE" "$_HARNESS_FULL"
}
trap _cleanup_harness_subsets EXIT

if [ "${_BASELINE_COUNT:-0}" -gt 0 ] && [ -f "$_BASELINE_SUBSET" ]; then
    cp "$_BASELINE_SUBSET" "$_HARNESS_BASELINE"
fi
if [ "${_FULL_COUNT:-0}" -gt 0 ] && [ -f "$_FULL_SUBSET" ]; then
    cp "$_FULL_SUBSET" "$_HARNESS_FULL"
fi

# ---------------------------------------------------------------------------
# Launch openhands_2config.sh for each config that has gaps
# ---------------------------------------------------------------------------

_OH_SCRIPT="$SCRIPT_DIR/openhands_2config.sh"

_common_args=()
[ -n "$MODEL_ARG" ]    && _common_args+=(--model "$MODEL_ARG")
[ -n "$CATEGORY_ARG" ] && _common_args+=(--category "$CATEGORY_ARG")
[ -n "$PARALLEL_ARG" ] && _common_args+=(--parallel "$PARALLEL_ARG")

_launch_baseline() {
    echo ""
    echo "=============================================="
    echo "Launching baseline-local-direct gap fill (${_BASELINE_COUNT} tasks)"
    echo "=============================================="
    "$_OH_SCRIPT" --baseline-only --subset "$_BASELINE_SUBSET_NAME" "${_common_args[@]}"
}

_launch_full() {
    echo ""
    echo "=============================================="
    echo "Launching mcp-remote-direct gap fill (${_FULL_COUNT} tasks)"
    echo "=============================================="
    "$_OH_SCRIPT" --full-only --subset "$_FULL_SUBSET_NAME" "${_common_args[@]}"
}

if [ "$BASELINE_ONLY" = true ]; then
    if [ "${_BASELINE_COUNT:-0}" -gt 0 ]; then
        _launch_baseline
    else
        echo "No baseline gaps to fill."
    fi
elif [ "$FULL_ONLY" = true ]; then
    if [ "${_FULL_COUNT:-0}" -gt 0 ]; then
        _launch_full
    else
        echo "No MCP-full gaps to fill."
    fi
else
    # Default: fill both configs (separate runs so --baseline-only/--full-only work)
    [ "${_BASELINE_COUNT:-0}" -gt 0 ] && _launch_baseline
    [ "${_FULL_COUNT:-0}" -gt 0 ] && _launch_full
fi

echo ""
echo "Gap fill complete. Report: $GAP_FILE"
