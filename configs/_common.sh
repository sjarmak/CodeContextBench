#!/bin/bash
# Shared configuration and helpers for all benchmark scripts.
# Source this at the top of every *_3config.sh and run_selected_tasks.sh.

# ============================================
# AUTHENTICATION MODE
# ============================================
# Use Claude Max subscription instead of API key.
# The agent reads ~/.claude/.credentials.json for the OAuth access token.
export USE_SUBSCRIPTION=true

# ============================================
# TOKEN REFRESH
# ============================================
# Refresh the Claude OAuth access token if it expires within REFRESH_MARGIN seconds.
# Uses the refresh_token from ~/.claude/.credentials.json.
# The OAuth endpoint returns a new access_token AND a new refresh_token (single-use).
REFRESH_MARGIN=${REFRESH_MARGIN:-1800}  # default: 30 minutes

refresh_claude_token() {
    local creds_file="$HOME/.claude/.credentials.json"
    if [ ! -f "$creds_file" ]; then
        echo "WARNING: No credentials file at $creds_file"
        return 1
    fi

    python3 - "$creds_file" "$REFRESH_MARGIN" <<'PYEOF'
import json, sys, time, urllib.request, urllib.error

creds_file = sys.argv[1]
margin = int(sys.argv[2])

with open(creds_file) as f:
    creds = json.load(f)

oauth = creds.get("claudeAiOauth", {})
expires_at_ms = oauth.get("expiresAt", 0)
now_ms = int(time.time() * 1000)
remaining_s = (expires_at_ms - now_ms) / 1000

if remaining_s > margin:
    mins = int(remaining_s / 60)
    print(f"Token still valid ({mins} min remaining, threshold {margin // 60} min). No refresh needed.")
    sys.exit(0)

refresh_token = oauth.get("refreshToken")
if not refresh_token:
    print("ERROR: No refreshToken in credentials file", file=sys.stderr)
    sys.exit(1)

print(f"Token expires in {int(remaining_s / 60)} min — refreshing...")

# Official Claude Code CLI client ID
payload = json.dumps({
    "grant_type": "refresh_token",
    "refresh_token": refresh_token,
    "client_id": "9d1c250a-e61b-44d9-88ed-5944d1962f5e"
}).encode()

req = urllib.request.Request(
    "https://console.anthropic.com/api/oauth/token",
    data=payload,
    headers={"Content-Type": "application/json"},
    method="POST"
)

try:
    with urllib.request.urlopen(req, timeout=15) as resp:
        token_data = json.loads(resp.read())
except urllib.error.HTTPError as e:
    body = e.read().decode() if e.fp else ""
    print(f"ERROR: Token refresh failed: HTTP {e.code} — {body}", file=sys.stderr)
    sys.exit(1)

new_access = token_data.get("access_token")
new_refresh = token_data.get("refresh_token")
expires_in = token_data.get("expires_in", 28800)  # default 8h

if not new_access:
    print("ERROR: No access_token in refresh response", file=sys.stderr)
    sys.exit(1)

oauth["accessToken"] = new_access
if new_refresh:
    oauth["refreshToken"] = new_refresh
oauth["expiresAt"] = int(time.time() * 1000) + (expires_in * 1000)
creds["claudeAiOauth"] = oauth

with open(creds_file, "w") as f:
    json.dump(creds, f, indent=2)

new_mins = expires_in // 60
print(f"Token refreshed successfully. New token valid for {new_mins} min.")
PYEOF
}

# ============================================
# ENSURE FRESH TOKEN
# ============================================
# Call this after sourcing .env.local but before launching runs.
ensure_fresh_token() {
    if [ "$USE_SUBSCRIPTION" = "true" ]; then
        echo "Checking Claude subscription token..."
        refresh_claude_token || echo "WARNING: Token refresh failed — runs may fail if token expires"
    fi
}

# ============================================
# POST-TASK VALIDATION
# ============================================
# Accumulator for validation warnings across all batches in a run.
VALIDATION_LOG=""

validate_and_report() {
    local jobs_dir=$1
    local mode=$2
    echo "Validating task results in $jobs_dir..."
    local _val_output
    _val_output=$(python3 "$(dirname "${BASH_SOURCE[0]}")/../scripts/validate_task_run.py" \
        --jobs-dir "$jobs_dir" --config "$mode" 2>&1) || true
    echo "$_val_output"
    VALIDATION_LOG+="$_val_output"$'\n'
}

# ============================================
# PARALLEL EXECUTION
# ============================================
# Number of concurrent task subshells. Set via --parallel N or PARALLEL_JOBS env var.
# Default is auto-detected after setup_multi_accounts (= SESSIONS_PER_ACCOUNT * num_accounts).
# Set to 0 here as sentinel; resolved in setup_multi_accounts.
PARALLEL_JOBS=${PARALLEL_JOBS:-0}

# Max concurrent sessions per Max-plan account before hitting rate limits.
# Based on empirical testing: ~4 concurrent Claude Code sessions per Max account.
SESSIONS_PER_ACCOUNT=${SESSIONS_PER_ACCOUNT:-4}

# ============================================
# MULTI-ACCOUNT SUPPORT
# ============================================
# Array of HOME directories for credential isolation.
# Each entry contains .claude/.credentials.json.
# Only Max-plan accounts are included (regular accounts are too rate-limited).
CLAUDE_HOMES=()
REAL_HOME="$HOME"

# List of account directory names to SKIP (e.g., non-Max-plan accounts).
# Override via SKIP_ACCOUNTS env var (space-separated).
# Default: skip account2 (regular plan, not Max — too rate-limited for parallel runs).
SKIP_ACCOUNTS="${SKIP_ACCOUNTS:-account2}"

# Detect all accounts under ~/.claude-homes/accountN/ (N=1,2,3,...).
# Skips accounts listed in SKIP_ACCOUNTS.
# Falls back to $HOME if no account directories are found.
# Auto-sets PARALLEL_JOBS = SESSIONS_PER_ACCOUNT * num_accounts when not explicitly set.
setup_multi_accounts() {
    CLAUDE_HOMES=()

    # Check for explicit account directories: account1, account2, ...
    local account_num=1
    while true; do
        local account_name="account$account_num"
        local account_home="$REAL_HOME/.claude-homes/$account_name"
        if [ -f "$account_home/.claude/.credentials.json" ]; then
            # Check skip list
            if [[ " $SKIP_ACCOUNTS " == *" $account_name "* ]]; then
                echo "  Skipping $account_name (in SKIP_ACCOUNTS)"
            else
                CLAUDE_HOMES+=("$account_home")
            fi
            account_num=$((account_num + 1))
        else
            break
        fi
    done

    # Fallback: if no account dirs found, use $HOME
    if [ ${#CLAUDE_HOMES[@]} -eq 0 ]; then
        CLAUDE_HOMES=("$HOME")
        echo "Single-account mode (using \$HOME)"
    else
        echo "Multi-account mode: ${#CLAUDE_HOMES[@]} accounts active"
        for i in "${!CLAUDE_HOMES[@]}"; do
            echo "  slot $((i+1)): ${CLAUDE_HOMES[$i]}"
        done
    fi

    # Auto-set PARALLEL_JOBS = sessions_per_account * num_accounts
    if [ "$PARALLEL_JOBS" -eq 0 ]; then
        PARALLEL_JOBS=$(( SESSIONS_PER_ACCOUNT * ${#CLAUDE_HOMES[@]} ))
        echo "Parallel jobs auto-set to $PARALLEL_JOBS ($SESSIONS_PER_ACCOUNT sessions x ${#CLAUDE_HOMES[@]} accounts)"
    fi
}

# Backward-compatible alias
setup_dual_accounts() { setup_multi_accounts; }

# Refresh tokens for all registered accounts.
ensure_fresh_token_all() {
    for home_dir in "${CLAUDE_HOMES[@]}"; do
        echo "Refreshing token for HOME=$home_dir ..."
        HOME="$home_dir" ensure_fresh_token
    done
    # Restore real HOME
    export HOME="$REAL_HOME"
}

# ============================================
# PARALLEL TASK RUNNER
# ============================================
# run_tasks_parallel: Run an array of task commands in parallel with job limiting.
#
# Usage:
#   run_tasks_parallel <task_id_array_name> <command_builder_function>
#
# The command_builder_function is called as:
#   command_builder_function <task_id> <account_home>
# and should execute the harbor run for that task (in the current shell).
#
# This function manages:
#   - Job concurrency limiting (PARALLEL_JOBS)
#   - Round-robin account distribution (CLAUDE_HOMES)
#   - PID tracking and exit code collection
#
# Returns 0 if all tasks succeeded, 1 if any failed.
run_tasks_parallel() {
    local -n _task_ids=$1
    local cmd_fn=$2
    local pids=()
    local task_for_pid=()
    local failed=0
    local account_idx=0
    local num_accounts=${#CLAUDE_HOMES[@]}

    echo "Parallel execution: ${#_task_ids[@]} tasks, max $PARALLEL_JOBS concurrent, $num_accounts account(s)"

    for task_id in "${_task_ids[@]}"; do
        # Wait if at PARALLEL_JOBS limit
        while [ ${#pids[@]} -ge $PARALLEL_JOBS ]; do
            # Wait for any one child to finish
            local done_pid=""
            for i in "${!pids[@]}"; do
                if ! kill -0 "${pids[$i]}" 2>/dev/null; then
                    done_pid="${pids[$i]}"
                    wait "$done_pid" 2>/dev/null || {
                        echo "WARNING: Task ${task_for_pid[$i]} (PID $done_pid) exited with error"
                        failed=1
                    }
                    unset 'pids[i]'
                    unset 'task_for_pid[i]'
                    # Re-index arrays
                    pids=("${pids[@]}")
                    task_for_pid=("${task_for_pid[@]}")
                    break
                fi
            done
            # If no PID finished yet, sleep briefly and re-check
            if [ -z "$done_pid" ]; then
                sleep 2
            fi
        done

        local task_home="${CLAUDE_HOMES[$account_idx]}"
        account_idx=$(( (account_idx + 1) % num_accounts ))

        (
            export HOME="$task_home"
            $cmd_fn "$task_id" "$task_home"
        ) &
        pids+=($!)
        task_for_pid+=("$task_id")
        echo "  Launched task $task_id (PID $!, account HOME=$task_home)"
    done

    # Wait for remaining tasks
    for i in "${!pids[@]}"; do
        wait "${pids[$i]}" 2>/dev/null || {
            echo "WARNING: Task ${task_for_pid[$i]} (PID ${pids[$i]}) exited with error"
            failed=1
        }
    done

    # Restore real HOME
    export HOME="$REAL_HOME"
    return $failed
}

print_validation_summary() {
    local run_dir="${1:-}"
    if [ -z "$VALIDATION_LOG" ]; then
        return
    fi
    echo ""
    echo "=============================================="
    echo "Validation Summary"
    echo "=============================================="
    echo "$VALIDATION_LOG"

    # Aggregate all config-level flagged_tasks.json into a run-level file
    if [ -n "$run_dir" ] && [ -d "$run_dir" ]; then
        python3 -c "
import json, glob, os, sys
run_dir = sys.argv[1]
all_flags = []
configs_seen = []
tasks_checked = 0
for fp in sorted(glob.glob(os.path.join(run_dir, '*/flagged_tasks.json'))):
    with open(fp) as f:
        data = json.load(f)
    configs_seen.append(data.get('config', ''))
    tasks_checked += data.get('tasks_checked', 0)
    all_flags.extend(data.get('flags', []))
if not configs_seen:
    sys.exit(0)
summary = {
    'configs': configs_seen,
    'tasks_checked': tasks_checked,
    'total_flags': len(all_flags),
    'critical_count': sum(1 for f in all_flags if f['severity'] == 'CRITICAL'),
    'warning_count': sum(1 for f in all_flags if f['severity'] == 'WARNING'),
    'info_count': sum(1 for f in all_flags if f['severity'] == 'INFO'),
    'flags': all_flags,
}
out = os.path.join(run_dir, 'flagged_tasks.json')
with open(out, 'w') as f:
    json.dump(summary, f, indent=2)
print(f'Run-level summary: {out}')
" "$run_dir" 2>&1 || true
    fi
}
