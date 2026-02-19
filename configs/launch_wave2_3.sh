#!/bin/bash
# Launch remaining SDLC suites: debug + build (concurrent), then fix.
# Waves 0-1 (test, understand, design, secure) already complete.
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

MODEL="anthropic/claude-sonnet-4-6"
LOG_DIR="runs/staging"
TS=$(date +%Y%m%d_%H%M%S)
MAIN_LOG="${LOG_DIR}/launch_wave2_3_${TS}.log"

# 2 accounts × 4 sessions = 8 total slots.
HALF=4
FULL=8

mkdir -p "$LOG_DIR"

log() { echo "[$(date +%H:%M:%S)] $*" | tee -a "$MAIN_LOG"; }

run_suite() {
    local suite=$1
    local parallel=$2
    shift 2
    local suite_log="${LOG_DIR}/${suite}_${TS}.log"
    log "  START $suite (parallel=$parallel) $*"
    "$SCRIPT_DIR/${suite}_2config.sh" --model "$MODEL" --parallel "$parallel" "$@" \
        > "$suite_log" 2>&1 || {
        log "  WARN  $suite exited with errors"
    }
    log "  DONE  $suite — see $suite_log"
}

log "=============================================="
log "Launching wave 2+3 — Model: $MODEL"
log "SKIP_ACCOUNTS=$SKIP_ACCOUNTS"
log "=============================================="

# ── Wave 2: debug + build (concurrent, 4 slots each) ──
log "Wave 2: debug + build"
run_suite debug $HALF &
run_suite build $HALF &
wait
log "Wave 2 complete"
log ""

# ── Wave 3: fix (full parallelism) ──
log "Wave 3: fix (full parallelism)"
run_suite fix $FULL
log "Wave 3 complete"
log ""

log "=============================================="
log "All remaining runs complete at $(date)"
log "=============================================="
