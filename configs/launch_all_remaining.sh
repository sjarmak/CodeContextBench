#!/bin/bash
# Launch all remaining work after VM spin-down + account3 rate limit kills.
#
# Phase 1: SG_full-only reruns (9 tasks that have BL done but SF missing)
# Phase 2: Paired reruns via suite 2config scripts for tasks missing BL
#          (build: 3 tasks, debug: 3 tasks, fix: all 25 tasks)
#
# All on account2 only (account1+3 exhausted).
# Broken dirs already cleaned with sudo rm before this script.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."
source configs/_common.sh

load_credentials
export SKIP_ACCOUNTS="${SKIP_ACCOUNTS:-}"
setup_multi_accounts

MODEL="anthropic/claude-sonnet-4-6"
AGENT_PATH="agents.claude_baseline_agent:BaselineClaudeCodeAgent"
BENCHMARK_DIR="benchmarks"
CONCURRENCY=2
TIMEOUT_MULTIPLIER=10
LOG_DIR="runs/staging"
TS=$(date +%Y%m%d_%H%M%S)
MAIN_LOG="${LOG_DIR}/launch_remaining_${TS}.log"

mkdir -p "$LOG_DIR"

log() { echo "[$(date +%H:%M:%S)] $*" | tee -a "$MAIN_LOG"; }

run_sgfull_task() {
    local suite=$1
    local task_id=$2
    local jobs_base=$3
    local task_path="${BENCHMARK_DIR}/${suite}/${task_id}"
    local jobs_subdir="${jobs_base}/sourcegraph_full"

    local sgonly="${task_path}/environment/Dockerfile.sg_only"
    if [ ! -f "$sgonly" ]; then
        log "ERROR: Missing Dockerfile.sg_only for $task_id"
        return 1
    fi

    local temp_task_dir
    temp_task_dir=$(mktemp -d "/tmp/rerun_${task_id}_XXXXXX")
    cp -a "${task_path}/." "${temp_task_dir}/"
    cp "${temp_task_dir}/environment/Dockerfile.sg_only" "${temp_task_dir}/environment/Dockerfile"

    local job_name="${suite}_${task_id}_sourcegraph_full"
    job_name="${job_name//[^[:alnum:]_.-]/-}"
    job_name=$(echo "$job_name" | tr '[:upper:]' '[:lower:]')

    log "Running SG_full: $task_id"

    BASELINE_MCP_TYPE=sourcegraph_full harbor run \
        --job-name "$job_name" \
        --path "$temp_task_dir" \
        --agent-import-path "$AGENT_PATH" \
        --model "$MODEL" \
        --jobs-dir "$jobs_subdir" \
        -n $CONCURRENCY \
        --timeout-multiplier $TIMEOUT_MULTIPLIER \
        2>&1 | tee "${jobs_subdir}/${task_id}_rerun.log" \
        || log "WARNING: $task_id SG_full failed (exit $?)"

    rm -rf "$temp_task_dir"
    log "Done: $task_id"
}

run_suite() {
    local suite=$1
    local parallel=$2
    shift 2
    local suite_log="${LOG_DIR}/${suite}_${TS}.log"
    log "  START $suite (parallel=$parallel) $*"
    "$SCRIPT_DIR/${suite}_2config.sh" --model "$MODEL" --parallel "$parallel" "$@" \
        > "$suite_log" 2>&1 || {
        log "  WARN  $suite exited with errors — see $suite_log"
    }
    log "  DONE  $suite — see $suite_log"
}

log "=============================================="
log "Post-VM-spindown recovery — all available accounts"
log "SKIP_ACCOUNTS=$SKIP_ACCOUNTS"
log "TS=$TS"
log "=============================================="

# ── Phase 1: SG_full-only reruns (parallel) ──
# These tasks have baseline completed but SG_full missing (rate-limited or VM-killed).
# Use fresh batch dirs to avoid "already exists" conflicts.
# Run all in parallel — they're independent tasks.
log ""
log "Phase 1: SG_full reruns for 10 tasks (BL done, SF missing) — parallel"

ensure_fresh_token_all

RERUN_BUILD="runs/staging/build_sonnet_rerun_${TS}"
RERUN_DEBUG="runs/staging/debug_sonnet_rerun_${TS}"
RERUN_TEST="runs/staging/test_sonnet_rerun_${TS}"
RERUN_FIX="runs/staging/fix_sonnet_rerun_${TS}"
mkdir -p "${RERUN_BUILD}/sourcegraph_full" "${RERUN_DEBUG}/sourcegraph_full" \
         "${RERUN_TEST}/sourcegraph_full" "${RERUN_FIX}/sourcegraph_full"

# Launch all SF reruns in parallel (background)
run_sgfull_task ccb_build flipt-dep-refactor-001 "$RERUN_BUILD" &
run_sgfull_task ccb_build k8s-noschedule-taint-feat-001 "$RERUN_BUILD" &
run_sgfull_task ccb_build python-http-class-naming-refac-001 "$RERUN_BUILD" &
run_sgfull_task ccb_build rust-subtype-relation-refac-001 "$RERUN_BUILD" &
run_sgfull_task ccb_debug prometheus-queue-reshard-debug-001 "$RERUN_DEBUG" &
run_sgfull_task ccb_debug qutebrowser-url-regression-prove-001 "$RERUN_DEBUG" &
run_sgfull_task ccb_test aspnetcore-code-review-001 "$RERUN_TEST" &
run_sgfull_task ccb_fix ansible-abc-imports-fix-001 "$RERUN_FIX" &
run_sgfull_task ccb_fix django-modelchoice-fk-fix-001 "$RERUN_FIX" &
# k8s-score-normalizer already running from previous launch (PID 122201)
wait
log "Phase 1 done"

log "Phase 1 complete (11 SF tasks)"
log ""

# ── Phase 2: Paired BL+SF reruns via suite 2config scripts ──
# These tasks are missing baseline (killed by VM spindown) and never had SF.
# The 2config scripts handle both configs in paired mode.
#
# build: bustub-hyperloglog, camel-fix-protocol, django-dep-refactor, kafka-batch-accumulator (4 tasks from 123558/133554)
# debug: envoy-duplicate-headers, flipt-cache-regression, teleport-ssh-regression (3 tasks from 123557/133554)
# fix: ansible-module-respawn, flipt-cockroachdb, flipt-ecr-auth, flipt-eval-latency (4 tasks from 123545)
#      + the rest of the fix suite that never ran (wave3 never started)
#
# Simplest approach: just rerun the full fix suite (25 tasks).
# For build and debug, only a few tasks are missing — but the 2config runner
# will create new batch dirs and all tasks will get fresh runs. Tasks that
# already have results in older batches will be superseded (latest-wins in MANIFEST).

log "=============================================="
log "Phase 2: Full fix suite (25 tasks, BL + SF)"
log "=============================================="

run_suite fix 4

log "Phase 2 complete"
log ""

# ── Phase 3: Targeted BL reruns for build + debug ──
# These need paired runs. Launching build and debug suites would rerun ALL tasks.
# Instead, run them via the suite 2config which will create a new batch.
# The duplicate completed tasks are harmless (MANIFEST uses latest-wins).

log "=============================================="
log "Phase 3: build + debug suites (paired, 4 slots each)"
log "=============================================="

run_suite build 4 &
run_suite debug 4 &
wait

log "Phase 3 complete"
log ""

log "=============================================="
log "All remaining work complete at $(date)"
log "=============================================="
