#!/usr/bin/env bash
set -euo pipefail

# Monitor pytorch and swebench-base tmux sessions for SB run completion,
# then automatically start SF runs when each finishes.

POLL_INTERVAL=60
WORKDIR="/home/stephanie_jarmak/CodeContextBench"

PYTORCH_SB_SESSION="pytorch"
SWEBENCH_SB_SESSION="swebench-base"
TAC_SB_SESSION="tac-sb"

PYTORCH_SF_SESSION="pytorch-sf"
SWEBENCH_SF_SESSION="swebench-sf"
TAC_SF_SESSION="tac-sf"

PYTORCH_SF_CMD="cd ${WORKDIR} && ./configs/pytorch_3config.sh --full-only"
SWEBENCH_SF_CMD="cd ${WORKDIR} && ./configs/swebenchpro_3config.sh --full-only"
TAC_SF_CMD="cd ${WORKDIR} && ./configs/tac_3config.sh --full-only"

FINISH_MARKER="Benchmark Complete"

pytorch_sb_done=false
swebench_sb_done=false
tac_sb_done=false
pytorch_sf_started=false
swebench_sf_started=false
tac_sf_started=false

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"
}

# Check if a tmux session exists
session_exists() {
    tmux has-session -t "$1" 2>/dev/null
}

# Check if a tmux session's pane has finished (contains marker or session gone)
is_run_finished() {
    local session="$1"

    if ! session_exists "$session"; then
        log "Session '$session' no longer exists -- treating as finished."
        return 0
    fi

    # Capture the last 50 lines of the pane buffer and look for the marker
    local buffer
    buffer=$(tmux capture-pane -t "$session" -p -S -50 2>/dev/null || true)

    if echo "$buffer" | grep -qF "$FINISH_MARKER"; then
        log "Found '${FINISH_MARKER}' in session '$session'."
        return 0
    fi

    return 1
}

start_sf_run() {
    local session_name="$1"
    local cmd="$2"

    if session_exists "$session_name"; then
        log "WARNING: Session '$session_name' already exists. Skipping creation."
        return 1
    fi

    log "Creating tmux session '$session_name' and starting SF run..."
    tmux new-session -d -s "$session_name" -c "$WORKDIR"
    tmux send-keys -t "$session_name" "$cmd" Enter
    log "SF run started in session '$session_name'."
    return 0
}

# ------- Main loop -------

log "=========================================="
log "Monitor & Queue script started"
log "Watching: $PYTORCH_SB_SESSION, $SWEBENCH_SB_SESSION, $TAC_SB_SESSION"
log "Poll interval: ${POLL_INTERVAL}s"
log "=========================================="

while true; do
    # -- PyTorch SB --
    if [[ "$pytorch_sb_done" == false ]]; then
        if is_run_finished "$PYTORCH_SB_SESSION"; then
            pytorch_sb_done=true
            log "PyTorch SB run is DONE."
        else
            log "PyTorch SB still running..."
        fi
    fi

    # Start PyTorch SF once SB is done
    if [[ "$pytorch_sb_done" == true && "$pytorch_sf_started" == false ]]; then
        if start_sf_run "$PYTORCH_SF_SESSION" "$PYTORCH_SF_CMD"; then
            pytorch_sf_started=true
        else
            log "ERROR: Failed to start PyTorch SF. Will retry next cycle."
        fi
    fi

    # -- SWE-bench SB --
    if [[ "$swebench_sb_done" == false ]]; then
        if is_run_finished "$SWEBENCH_SB_SESSION"; then
            swebench_sb_done=true
            log "SWE-bench SB run is DONE."
        else
            log "SWE-bench SB still running..."
        fi
    fi

    # Start SWE-bench SF once SB is done
    if [[ "$swebench_sb_done" == true && "$swebench_sf_started" == false ]]; then
        if start_sf_run "$SWEBENCH_SF_SESSION" "$SWEBENCH_SF_CMD"; then
            swebench_sf_started=true
        else
            log "ERROR: Failed to start SWE-bench SF. Will retry next cycle."
        fi
    fi

    # -- TAC SB --
    if [[ "$tac_sb_done" == false ]]; then
        if is_run_finished "$TAC_SB_SESSION"; then
            tac_sb_done=true
            log "TAC SB run is DONE."
        else
            log "TAC SB still running..."
        fi
    fi

    # Start TAC SF once SB is done
    if [[ "$tac_sb_done" == true && "$tac_sf_started" == false ]]; then
        if start_sf_run "$TAC_SF_SESSION" "$TAC_SF_CMD"; then
            tac_sf_started=true
        else
            log "ERROR: Failed to start TAC SF. Will retry next cycle."
        fi
    fi

    # -- Check if all work is done --
    if [[ "$pytorch_sf_started" == true && "$swebench_sf_started" == true && "$tac_sf_started" == true ]]; then
        log "All SF runs have been launched. Monitor script finished."
        break
    fi

    sleep "$POLL_INTERVAL"
done

log "=========================================="
log "Monitor & Queue script exiting."
log "=========================================="
