#!/bin/bash
# OpenHands Harness 2-Config Runner
#
# Runs selected tasks across 2 configurations:
#   1. baseline-local-direct (BASELINE_MCP_TYPE=none)
#   2. mcp-remote-direct (BASELINE_MCP_TYPE=sourcegraph_full)
#
# Usage:
#   ./configs/openhands_2config.sh [OPTIONS]
#
# Options:
#   --baseline-only        Run only baseline (no MCP)
#   --full-only            Run only MCP-Full (sourcegraph_full)
#   --sequential           Run baseline then MCP sequentially (default: paired/parallel)
#   --model MODEL          Override model (default: anthropic/claude-sonnet-4-6)
#   --agent-path PATH      Override Harbor agent import path
#   --parallel N           Max parallel task subshells (default: 1)
#   --category CATEGORY    Run category label for jobs dir (default: staging)
#   --benchmark BENCH      Optional benchmark filter (e.g. csb_sdlc_feature, csb_sdlc_fix)
#   --task TASK_ID         Run only this task (further filters after --benchmark)
#   --subset FILENAME      Use subset JSON (relative to configs/, e.g. openhands_subset.json)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

# Agent code lives in-repo under agents/
export PYTHONPATH="$(pwd):${PYTHONPATH:-}"

# Shared helpers (validation/reporting and run helpers)
source "$SCRIPT_DIR/_common.sh"
load_credentials

# OpenHands needs ANTHROPIC_API_KEY in the environment for Harbor's model key resolver.
# When using OAuth subscription (no explicit API key), extract the access token.
if [ -z "${ANTHROPIC_API_KEY:-}" ] && [ "$USE_SUBSCRIPTION" = "true" ]; then
    _oauth_token=$(python3 -c "
import json, os
creds_file = os.path.expanduser('~/.claude/.credentials.json')
if os.path.exists(creds_file):
    creds = json.load(open(creds_file))
    token = creds.get('claudeAiOauth', {}).get('accessToken', '')
    if token:
        print(token)
" 2>/dev/null)
    if [ -n "$_oauth_token" ]; then
        export ANTHROPIC_API_KEY="$_oauth_token"
        echo "Injected OAuth access token as ANTHROPIC_API_KEY for OpenHands"
    else
        echo "WARNING: Could not extract OAuth token from ~/.claude/.credentials.json"
        echo "  OpenHands will fail unless ANTHROPIC_API_KEY is set"
    fi
    unset _oauth_token
fi

SELECTION_FILE="$SCRIPT_DIR/selected_benchmark_tasks.json"
OPENHANDS_ROUTING_POLICY="${OPENHANDS_ROUTING_POLICY:-$SCRIPT_DIR/openhands_daytona_routing.json}"
AGENT_PATH="${AGENT_PATH:-agents.harnesses.openhands:OpenHandsHarnessAgent}"
MODEL="${MODEL:-anthropic/claude-sonnet-4-6}"
CATEGORY="${CATEGORY:-staging}"
BENCHMARK_FILTER=""
TASK_FILTER=""
CONCURRENCY=2
TIMEOUT_MULTIPLIER=10
RUN_BASELINE=true
RUN_FULL=true
PAIRED_MODE=true  # Run baseline+MCP in parallel by default

while [[ $# -gt 0 ]]; do
    case $1 in
        --baseline-only)
            RUN_FULL=false
            PAIRED_MODE=false
            shift
            ;;
        --full-only)
            RUN_BASELINE=false
            PAIRED_MODE=false
            shift
            ;;
        --sequential)
            PAIRED_MODE=false
            shift
            ;;
        --model)
            MODEL="$2"
            shift 2
            ;;
        --agent-path)
            AGENT_PATH="$2"
            shift 2
            ;;
        --parallel)
            PARALLEL_JOBS="$2"
            shift 2
            ;;
        --category)
            CATEGORY="$2"
            shift 2
            ;;
        --benchmark)
            BENCHMARK_FILTER="$2"
            shift 2
            ;;
        --task)
            TASK_FILTER="$2"
            shift 2
            ;;
        --subset)
            SELECTION_FILE="$SCRIPT_DIR/$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

if [ ! -f "$SELECTION_FILE" ]; then
    echo "ERROR: Task selection file not found at $SELECTION_FILE"
    exit 1
fi

if [ ! -f "$OPENHANDS_ROUTING_POLICY" ]; then
    echo "ERROR: OpenHands routing policy not found at $OPENHANDS_ROUTING_POLICY"
    exit 1
fi

readarray -t TASK_ROWS < <(python3 - "$SELECTION_FILE" "$BENCHMARK_FILTER" "$TASK_FILTER" <<'PYEOF'
import json
import sys

selection_file = sys.argv[1]
benchmark_filter = sys.argv[2]
task_filter = sys.argv[3] if len(sys.argv) > 3 else ""

data = json.load(open(selection_file))
for task in data.get("tasks", []):
    if task.get("excluded", False):
        continue
    if benchmark_filter and task.get("benchmark") != benchmark_filter:
        continue
    if task_filter and task.get("task_id") != task_filter:
        continue
    task_id = task["task_id"]
    task_dir = task["task_dir"]
    benchmark = task.get("benchmark", "")
    print(f"{task_id}\tbenchmarks/{task_dir}\t{benchmark}")
PYEOF
)

if [ ${#TASK_ROWS[@]} -eq 0 ]; then
    echo "ERROR: no tasks selected after filters"
    exit 1
fi

declare -A TASK_PATH_BY_ID
TASK_IDS=()
for row in "${TASK_ROWS[@]}"; do
    task_id=$(echo "$row" | cut -f1)
    task_path=$(echo "$row" | cut -f2)
    TASK_IDS+=("$task_id")
    TASK_PATH_BY_ID["$task_id"]="$task_path"
done

if [ -z "${PARALLEL_JOBS:-}" ] || [ "$PARALLEL_JOBS" -lt 1 ] 2>/dev/null; then
    PARALLEL_JOBS=0  # sentinel; setup_multi_accounts will auto-set
fi

# Multi-account support: rotate OAuth tokens across accounts.
# REAL_HOME must be set before setup_multi_accounts.
REAL_HOME="$HOME"
setup_multi_accounts

# In Daytona mode, override the session-based parallelism with sandbox-based cap.
# Daytona Tier 3 allows 125 concurrent sandboxes; paired mode uses 2 per task.
DAYTONA_PARALLEL_TASK_CAP="${DAYTONA_PARALLEL_TASK_CAP:-60}"
if [ "${HARBOR_ENV:-}" = "daytona" ]; then
    if [ "$DAYTONA_PARALLEL_TASK_CAP" -gt 124 ]; then
        DAYTONA_PARALLEL_TASK_CAP=124
    fi
    if [ "$PARALLEL_JOBS" -le 0 ] 2>/dev/null; then
        PARALLEL_JOBS=$DAYTONA_PARALLEL_TASK_CAP
    elif [ "$PARALLEL_JOBS" -gt "$DAYTONA_PARALLEL_TASK_CAP" ]; then
        PARALLEL_JOBS=$DAYTONA_PARALLEL_TASK_CAP
    fi
    echo "Parallel tasks set to $PARALLEL_JOBS (Daytona mode, cap=${DAYTONA_PARALLEL_TASK_CAP})"
fi

_model_lower=$(echo "$MODEL" | awk -F/ '{print $NF}' | tr '[:upper:]' '[:lower:]')
case "$_model_lower" in
    *gpt-5.3-codex*|*gpt53codex*) MODEL_SHORT="gpt53codex" ;;
    *gpt-5*|*gpt5*) MODEL_SHORT="gpt5" ;;
    *gpt-4o*|*gpt4o*) MODEL_SHORT="gpt4o" ;;
    *gpt-4*|*gpt4*) MODEL_SHORT="gpt4" ;;
    *sonnet-4-6*|*sonnet46*) MODEL_SHORT="sonnet46" ;;
    *sonnet-4-5*|*sonnet45*) MODEL_SHORT="sonnet45" ;;
    *opus-4-6*|*opus46*) MODEL_SHORT="opus46" ;;
    *haiku-4-5*|*haiku45*) MODEL_SHORT="haiku45" ;;
    *) MODEL_SHORT=$(echo "$_model_lower" | tr -d '-' | tr -d '_' | cut -c1-12) ;;
esac

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
JOBS_BASE="runs/${CATEGORY}/openhands_${MODEL_SHORT}_${TIMESTAMP}"
mkdir -p "$JOBS_BASE"

readarray -t DAYTONA_SKIP_FROM_PREFIXES < <(python3 - "$OPENHANDS_ROUTING_POLICY" <<'PYEOF'
import json
import sys

policy = json.load(open(sys.argv[1]))
for prefix in policy.get("skip_daytona_from_prefixes", []):
    if isinstance(prefix, str) and prefix:
        print(prefix)
PYEOF
)

readarray -t LOCAL_DOCKER_ROUTE_RULES < <(python3 - "$OPENHANDS_ROUTING_POLICY" <<'PYEOF'
import json
import sys

policy = json.load(open(sys.argv[1]))
for config_name, config_rules in (policy.get("local_docker_by_config") or {}).items():
    if not isinstance(config_rules, dict):
        continue
    for repo in config_rules.get("repos", []):
        if isinstance(repo, str) and repo:
            print(f"{config_name}\t{repo}")
PYEOF
)

_task_uses_daytona_blocked_image() {
    local task_path="$1"
    if [ ! -d "$task_path/environment" ]; then
        return 1
    fi
    local prefix
    local files=(
        "$task_path/environment/Dockerfile"
        "$task_path/environment/Dockerfile.sg_only"
        "$task_path/environment/Dockerfile.artifact_only"
    )
    for prefix in "${DAYTONA_SKIP_FROM_PREFIXES[@]}"; do
        [ -n "$prefix" ] || continue
        if rg -F -q "$prefix" "${files[@]}" 2>/dev/null; then
            return 0
        fi
    done
    return 1
}

_task_repo_id() {
    python3 - "$1/task.toml" <<'PYEOF'
import pathlib
import re
import sys

try:
    import tomllib
except ImportError:  # Python 3.10
    tomllib = None

task_toml = pathlib.Path(sys.argv[1])
if not task_toml.is_file():
    sys.exit(0)

try:
    content = task_toml.read_text()
except Exception:
    sys.exit(0)

if tomllib is not None:
    try:
        data = tomllib.loads(content)
    except Exception:
        data = {}
    repo = data.get("repo")
    if isinstance(repo, str):
        print(repo)
        sys.exit(0)

match = re.search(r'(?m)^repo\\s*=\\s*[\"\']([^\"\']+)[\"\']\\s*$', content)
if match:
    print(match.group(1))
PYEOF
}

_task_requires_local_docker_for_config() {
    local config_name="$1"
    local task_path="$2"
    local repo
    repo=$(_task_repo_id "$task_path")
    local rule
    local rule_config
    local rule_repo
    for rule in "${LOCAL_DOCKER_ROUTE_RULES[@]}"; do
        rule_config=${rule%%$'\t'*}
        rule_repo=${rule#*$'\t'}
        if [ "$rule_config" = "$config_name" ] && [ "$rule_repo" = "$repo" ]; then
            return 0
        fi
    done
    return 1
}

_make_lowercase_mcp_temp_dir() {
    python3 - "$1" <<'PYEOF'
import pathlib
import re
import sys
import uuid

task_id = sys.argv[1].lower()
safe_task_id = re.sub(r"[^a-z0-9._-]+", "_", task_id).strip("_") or "task"
temp_dir = pathlib.Path("/tmp") / f"mcp_{safe_task_id}_{uuid.uuid4().hex[:8]}"
temp_dir.mkdir()
print(temp_dir)
PYEOF
}

echo "=============================================="
echo "OpenHands 2-Config Runner"
echo "=============================================="
echo "Model: $MODEL"
echo "Agent path: $AGENT_PATH"
echo "Selection: $SELECTION_FILE"
echo "Routing policy: $OPENHANDS_ROUTING_POLICY"
echo "Benchmark filter: ${BENCHMARK_FILTER:-<all selected benchmarks>}"
echo "Task count: ${#TASK_IDS[@]}"
echo "Parallel jobs: $PARALLEL_JOBS"
echo "Jobs directory: $JOBS_BASE"
echo "Environment: ${HARBOR_ENV:-local-docker}"
echo "Run baseline: $RUN_BASELINE"
echo "Run MCP-Full: $RUN_FULL"
echo "Paired mode: $PAIRED_MODE"
echo "ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY:+set (${#ANTHROPIC_API_KEY} chars)}"
echo "Memory override: ${DAYTONA_OVERRIDE_MEMORY:-<none>} MB"
echo "Storage override: ${DAYTONA_OVERRIDE_STORAGE:-<none>} MB"
echo ""

if [ "${HARBOR_ENV:-}" = "daytona" ]; then
    clear_daytona_cost_guard_ready
    _cost_guard_cmd=(
        python3 "$REPO_ROOT/scripts/daytona_cost_guard.py" preflight
        --selection-file "$SELECTION_FILE"
        --parallel-tasks "$PARALLEL_JOBS"
        --concurrency "$CONCURRENCY"
        --policy "$DAYTONA_COST_POLICY"
        --routing-policy "$OPENHANDS_ROUTING_POLICY"
    )
    [ -n "$BENCHMARK_FILTER" ] && _cost_guard_cmd+=(--benchmark "$BENCHMARK_FILTER")
    [ -n "$TASK_FILTER" ] && _cost_guard_cmd+=(--task-id "$TASK_FILTER")
    [ "$RUN_BASELINE" = true ] && _cost_guard_cmd+=(--config "baseline-local-direct")
    [ "$RUN_FULL" = true ] && _cost_guard_cmd+=(--config "mcp-remote-direct")
    "${_cost_guard_cmd[@]}" || exit 1
    mark_daytona_cost_guard_ready
fi

_launch_config_label="baseline-local-direct + mcp-remote-direct"
if [ "$RUN_BASELINE" = true ] && [ "$RUN_FULL" = false ]; then
    _launch_config_label="baseline-local-direct"
elif [ "$RUN_BASELINE" = false ] && [ "$RUN_FULL" = true ]; then
    _launch_config_label="mcp-remote-direct"
fi
confirm_launch "OpenHands 2-config run" "$_launch_config_label" "${#TASK_IDS[@]}"

_openhands_run_single() {
    local task_id=$1
    local _task_home=$2
    local config=${3:-baseline-local-direct}
    local mcp_type=${4:-none}
    local jobs_base=${5:-$JOBS_BASE}
    local jobs_subdir="${jobs_base}/${config}"
    local task_path="${TASK_PATH_BY_ID[$task_id]}"

    # Extract ANTHROPIC_API_KEY from this account's OAuth credentials.
    # run_tasks_parallel sets HOME=$_task_home, so we read that account's token.
    if [ "$USE_SUBSCRIPTION" = "true" ]; then
        local _acct_token
        _acct_token=$(python3 -c "
import json, os
creds_file = os.path.join('${_task_home}', '.claude', '.credentials.json')
if os.path.exists(creds_file):
    creds = json.load(open(creds_file))
    token = creds.get('claudeAiOauth', {}).get('accessToken', '')
    if token: print(token)
" 2>/dev/null)
        if [ -n "$_acct_token" ]; then
            export ANTHROPIC_API_KEY="$_acct_token"
        fi
    fi

    case "$mcp_type" in
        none|sourcegraph_full)
            ;;
        *)
            echo "ERROR: unsupported MCP mode for openhands rollout: $mcp_type"
            return 1
            ;;
    esac

    mkdir -p "$jobs_subdir"

    if [ ! -d "$task_path" ]; then
        echo "ERROR: Task directory not found: $task_path"
        return 1
    fi

    if [ "${HARBOR_ENV:-}" = "daytona" ] && _task_uses_daytona_blocked_image "$task_path"; then
        echo "SKIP: $task_id ($config) uses jefzda/sweap-images and is Daytona-incompatible"
        return 0
    fi

    local _task_harbor_env="${HARBOR_ENV:-}"
    if [ "$_task_harbor_env" = "daytona" ] \
        && _task_requires_local_docker_for_config "$config" "$task_path"; then
        _task_harbor_env=""
        echo "  [local-docker] Routing task off Daytona for $config: $task_id"
    fi

    # For MCP configs, swap in Dockerfile.sg_only (truncated source, agent uses MCP)
    local _run_path="$task_path"
    if [ "$mcp_type" = "sourcegraph_full" ]; then
        local _df_sgonly="${task_path}/environment/Dockerfile.sg_only"
        if [ -f "$_df_sgonly" ]; then
            local _mcp_temp_dir
            _mcp_temp_dir=$(_make_lowercase_mcp_temp_dir "$task_id")
            cp -a "${task_path}/." "${_mcp_temp_dir}/"
            cp "${_mcp_temp_dir}/environment/Dockerfile.sg_only" "${_mcp_temp_dir}/environment/Dockerfile"
            _run_path="$_mcp_temp_dir"
            echo "  [sg_only] Using truncated Dockerfile for MCP config: $task_id"
        else
            echo "  WARNING: No Dockerfile.sg_only for $task_id — MCP will have local source access"
        fi
    fi

    echo "Running task: $task_id ($config)"
    local -a _task_override_args=()
    if [ "$_task_harbor_env" = "daytona" ]; then
        [ -n "${DAYTONA_OVERRIDE_MEMORY:-}" ] && _task_override_args+=(--override-memory-mb "$DAYTONA_OVERRIDE_MEMORY")
        [ -n "${DAYTONA_OVERRIDE_STORAGE:-}" ] && _task_override_args+=(--override-storage-mb "$DAYTONA_OVERRIDE_STORAGE")
    fi

    DAYTONA_LABEL_RUN_ID="$(basename "$JOBS_BASE")" \
    DAYTONA_LABEL_BENCHMARK="$(basename "$(dirname "$task_path")")" \
    DAYTONA_LABEL_TASK_ID="$task_id" \
    DAYTONA_LABEL_CONFIG="$config" \
    DAYTONA_LABEL_CATEGORY="$CATEGORY" \
    TASK_SOURCE_DIR="$_run_path" \
    HARBOR_ENV="$_task_harbor_env" \
    BASELINE_MCP_TYPE="$mcp_type" harbor_run_guarded \
        --path "$_run_path" \
        --agent-import-path "$AGENT_PATH" \
        --model "$MODEL" \
        --jobs-dir "$jobs_subdir" \
        -n "$CONCURRENCY" \
        --timeout-multiplier "$TIMEOUT_MULTIPLIER" \
        ${_task_harbor_env:+--env "$_task_harbor_env"} \
        "${_task_override_args[@]}" \
        2>&1 | tee "${jobs_subdir}/${task_id}.log" \
        || echo "WARNING: Task $task_id ($config) failed"
}

run_mode() {
    local mode=$1
    local mcp_type=$2

    jobs_subdir="${JOBS_BASE}/${mode}"
    mkdir -p "$jobs_subdir"

    _mode_dispatch() {
        _openhands_run_single "$1" "$2" "$mode" "$mcp_type" "$JOBS_BASE"
    }

    run_tasks_parallel TASK_IDS _mode_dispatch || true
    validate_and_report "$jobs_subdir" "$mode"
}

if [ "$PAIRED_MODE" = true ] && [ "$RUN_BASELINE" = true ] && [ "$RUN_FULL" = true ]; then
    # Run baseline + MCP simultaneously per task (interleaved, not sequential)
    export FULL_CONFIG="mcp-remote-direct"
    run_paired_configs TASK_IDS _openhands_run_single "$JOBS_BASE"
    validate_and_report "${JOBS_BASE}/baseline-local-direct" "baseline-local-direct"
    validate_and_report "${JOBS_BASE}/mcp-remote-direct" "mcp-remote-direct"
else
    # Sequential mode (--baseline-only, --full-only, or --sequential)
    if [ "$RUN_BASELINE" = true ]; then
        run_mode "baseline-local-direct" "none"
    fi
    if [ "$RUN_FULL" = true ]; then
        run_mode "mcp-remote-direct" "sourcegraph_full"
    fi
fi

print_validation_summary "$JOBS_BASE"

echo ""
echo "Done. Results: $JOBS_BASE"
