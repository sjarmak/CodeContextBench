#!/bin/bash
# Validation Runner — One task per benchmark, baseline only
#
# Runs the first task from each of the 11 benchmarks to verify
# adapters, Docker images, and result collection are working.
#
# Usage:
#   bash configs/validate_one_per_benchmark.sh [--dry-run]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$SCRIPT_DIR/.."
cd "$REPO_ROOT"

# Agent module lives in the evals repo; add it to PYTHONPATH
AGENT_DIR="${AGENT_DIR:-$HOME/evals/custom_agents/agents/claudecode}"
export PYTHONPATH="${AGENT_DIR}:$(pwd):$PYTHONPATH"

DRY_RUN=false
if [ "${1:-}" = "--dry-run" ]; then
    DRY_RUN=true
fi

SELECTION_FILE="$REPO_ROOT/configs/selected_benchmark_tasks.json"
MODEL="${MODEL:-anthropic/claude-opus-4-5-20251101}"
AGENT_PATH="agents.claude_baseline_agent:BaselineClaudeCodeAgent"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
JOBS_DIR="runs/validation/smoke_${TIMESTAMP}"

# Load credentials
if [ -f ~/evals/.env.local ]; then
    source ~/evals/.env.local
fi

if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "ERROR: ANTHROPIC_API_KEY is not set"
    exit 1
fi

# Extract first task per benchmark
TASKS=$(python3 -c "
import json
sel = json.load(open('$SELECTION_FILE'))
seen = set()
for t in sel['tasks']:
    bm = t['benchmark']
    if bm not in seen:
        seen.add(bm)
        print(f'{bm}\tbenchmarks/{t[\"task_dir\"]}')
")

echo "=============================================="
echo "CodeContextBench Validation Run"
echo "=============================================="
echo "Mode:    baseline (no MCP)"
echo "Model:   $MODEL"
echo "Tasks:   1 per benchmark (11 total)"
echo "Output:  $JOBS_DIR"
echo ""
echo "Tasks:"
echo "$TASKS" | while IFS=$'\t' read -r bm path; do
    printf "  %-20s %s\n" "$bm" "$path"
done
echo ""

if [ "$DRY_RUN" = true ]; then
    echo "[DRY RUN] Verifying task directories..."
    FAIL=0
    echo "$TASKS" | while IFS=$'\t' read -r bm path; do
        if [ -d "$path" ] && [ -f "$path/task.toml" ]; then
            echo "  OK   $path"
        else
            echo "  FAIL $path"
            FAIL=1
        fi
    done
    exit $FAIL
fi

mkdir -p "$JOBS_DIR"

# Run each task
PASS=0
FAIL=0
ERRORS=""

echo "$TASKS" | while IFS=$'\t' read -r bm path; do
    abs_path="$REPO_ROOT/$path"
    echo ""
    echo "=============================="
    echo "[$bm] $path"
    echo "=============================="

    if [ ! -d "$abs_path" ]; then
        echo "SKIP: directory not found"
        FAIL=$((FAIL + 1))
        ERRORS="${ERRORS}\n  MISS: $bm ($path)"
        continue
    fi

    BASELINE_MCP_TYPE=none harbor run \
        --path "$abs_path" \
        --agent-import-path "$AGENT_PATH" \
        --model "$MODEL" \
        --jobs-dir "$JOBS_DIR/$bm" \
        -n 1 \
        --timeout-multiplier 10 \
        2>&1 | tee -a "$JOBS_DIR/${bm}.log" \
        && PASS=$((PASS + 1)) \
        || { FAIL=$((FAIL + 1)); ERRORS="${ERRORS}\n  FAIL: $bm ($path)"; }
done

echo ""
echo "=============================================="
echo "Validation Complete"
echo "=============================================="
echo "Results: $JOBS_DIR"
echo ""
echo "Check results:"
echo "  find $JOBS_DIR -name reward.txt -exec echo {} ';' -exec cat {} ';'"
