#!/bin/bash
# Local Docker runner for sourcegraph validation tasks.
#
# Builds images using Docker BuildKit secrets for private repo auth,
# runs Claude Code Haiku agent, then verification.
#
# Prerequisites:
#   - gh CLI authenticated (gh auth status)
#   - Docker running locally
#   - Claude Code OAuth credentials at ~/.claude/.credentials.json
#
# Usage:
#   bash scripts/run_sg_local.sh [task_id ...]    # specific tasks
#   bash scripts/run_sg_local.sh                   # all 6 tasks

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TASKS_DIR="$REPO_ROOT/sourcegraph_tasks"
RUNS_DIR="$REPO_ROOT/runs/sg_validation"
RUN_ID="sg_local_haiku_bl_$(date +%Y%m%d_%H%M%S)"
RUN_DIR="$RUNS_DIR/$RUN_ID"

# Claude Code auth
OAUTH_CREDS_FILE="$HOME/.claude/.credentials.json"
if [ ! -f "$OAUTH_CREDS_FILE" ]; then
    echo "ERROR: No OAuth credentials at $OAUTH_CREDS_FILE"
    exit 1
fi

# Model config
MODEL="${MODEL:-claude-haiku-4-5-20251001}"
MAX_TURNS="${MAX_TURNS:-30}"

# Generate a .netrc file for Docker build (using gh credentials)
NETRC_FILE=$(mktemp)
trap 'rm -f "$NETRC_FILE"' EXIT
# gh's credential helper can provide tokens; extract from config
GH_TOKEN=$(grep 'oauth_token' ~/.config/gh/hosts.yml 2>/dev/null | head -1 | awk '{print $2}')
if [ -z "$GH_TOKEN" ]; then
    echo "ERROR: No GitHub token in ~/.config/gh/hosts.yml"
    echo "Run: gh auth login"
    exit 1
fi
# gh oauth tokens don't work for direct git clone; we need the credential helper approach
# Instead, use git credential fill to get a valid token
GIT_TOKEN=$(echo -e "protocol=https\nhost=github.com" | git credential fill 2>/dev/null | grep '^password=' | cut -d= -f2-)
if [ -z "$GIT_TOKEN" ]; then
    echo "WARNING: git credential fill returned no token, falling back to gh oauth_token"
    GIT_TOKEN="$GH_TOKEN"
fi
echo "machine github.com login x-access-token password $GIT_TOKEN" > "$NETRC_FILE"

# Verify token works
if ! git ls-remote --exit-code "https://x-access-token:${GIT_TOKEN}@github.com/sourcegraph/sourcegraph.git" HEAD >/dev/null 2>&1; then
    echo "WARNING: Token may not work for git clone. Build might fail."
    echo "Consider: gh auth refresh -s repo"
fi

# Tasks to run
if [ $# -gt 0 ]; then
    TASKS=("$@")
else
    TASKS=(
        ccx-sgauth-301
        ccx-sgcompletion-302
        ccx-sgencrypt-305
        sg-deepsearch-anchor-fix-001
        sg-deepsearch-imgbomb-fix-001
        sg-gitlab-ratelimit-fix-001
    )
fi

mkdir -p "$RUN_DIR"

echo "=============================================="
echo "SG Validation: Local Docker Runner"
echo "=============================================="
echo "  Tasks:  ${#TASKS[@]}"
echo "  Model:  $MODEL"
echo "  RunID:  $RUN_ID"
echo "  Output: $RUN_DIR"
echo "=============================================="
echo ""

run_task() {
    local TASK_ID="$1"
    local TASK_DIR="$TASKS_DIR/$TASK_ID"
    local RESULT_DIR="$RUN_DIR/$TASK_ID"
    local IMAGE_NAME="sg-val-${TASK_ID}"
    local CONTAINER_NAME="sg-run-${TASK_ID}-$$"

    mkdir -p "$RESULT_DIR"

    echo ""
    echo ">>> [$TASK_ID] Starting..."
    local START_TIME=$(date +%s)

    # --- Phase 1: Build image with BuildKit secret ---
    echo ">>> [$TASK_ID] Building Docker image..."

    # Create modified Dockerfile using BuildKit secrets
    local TMP_DF=$(mktemp)
    local ORIG_DF="$TASK_DIR/environment/Dockerfile"

    # Add syntax directive and secret mount to git network operations
    cat > "$TMP_DF" << 'HEADER'
# syntax=docker/dockerfile:1
HEADER
    # Mount .netrc secret on any RUN that does git clone or git init+fetch
    sed -e 's|^RUN git clone https://github.com/sourcegraph|RUN --mount=type=secret,id=netrc,target=/root/.netrc git clone https://github.com/sourcegraph|' \
        -e 's|^RUN git init /workspace|RUN --mount=type=secret,id=netrc,target=/root/.netrc git init /workspace|' \
        "$ORIG_DF" >> "$TMP_DF"

    DOCKER_BUILDKIT=1 docker build \
        --secret "id=netrc,src=$NETRC_FILE" \
        -t "$IMAGE_NAME" \
        -f "$TMP_DF" \
        "$TASK_DIR/environment" \
        > "$RESULT_DIR/build.log" 2>&1
    local BUILD_RC=$?
    rm -f "$TMP_DF"

    if [ $BUILD_RC -ne 0 ]; then
        echo ">>> [$TASK_ID] BUILD FAILED (exit $BUILD_RC)"
        tail -20 "$RESULT_DIR/build.log"
        echo "$TASK_ID,build_failed,N/A,0" >> "$RUN_DIR/summary.csv"
        return 1
    fi
    echo ">>> [$TASK_ID] Image built successfully"

    # --- Phase 2: Run agent + verification ---
    echo ">>> [$TASK_ID] Running agent ($MODEL, max_turns=$MAX_TURNS)..."

    local INSTRUCTION
    INSTRUCTION=$(cat "$TASK_DIR/instruction.md")

    # Write instruction to a temp file (avoids shell quoting issues)
    local INSTR_FILE=$(mktemp)
    cat "$TASK_DIR/instruction.md" > "$INSTR_FILE"

    docker run --rm --name "$CONTAINER_NAME" \
        -v "$OAUTH_CREDS_FILE:/tmp/claude_creds.json:ro" \
        -v "$TASK_DIR/tests:/tests_src:ro" \
        -v "$INSTR_FILE:/tmp/task_instruction.md:ro" \
        -v "$NETRC_FILE:/tmp/netrc:ro" \
        -e "DEBIAN_FRONTEND=noninteractive" \
        --memory=8g \
        --cpus=2 \
        "$IMAGE_NAME" \
        bash -c '
            set -e

            # Install Node.js
            curl -fsSL https://nodejs.org/dist/v22.14.0/node-v22.14.0-linux-x64.tar.gz \
                | tar -xz -C /usr/local --strip-components=1 2>/dev/null
            echo "Node: $(node --version)"

            # Install Claude Code
            npm install -g @anthropic-ai/claude-code@latest 2>&1 | tail -3
            echo "Claude: $(claude --version 2>&1 || echo unknown)"

            # Setup user & dirs
            useradd -m -s /bin/bash claude 2>/dev/null || true
            mkdir -p /home/claude/.claude /logs/agent /logs/verifier /tests

            # Propagate git auth for private Go deps at test time
            if [ -f /tmp/netrc ]; then
                cp /tmp/netrc /root/.netrc
                chmod 600 /root/.netrc
                cp /tmp/netrc /home/claude/.netrc 2>/dev/null || true
            fi
            cp /tmp/claude_creds.json /home/claude/.claude/.credentials.json
            cp -r /tests_src/* /tests/ 2>/dev/null || true
            chmod +x /tests/*.sh 2>/dev/null || true
            # Copy instruction to claude-accessible location
            cp /tmp/task_instruction.md /home/claude/task_instruction.md
            chown -R claude:claude /home/claude /workspace /logs /tests

            # Run agent
            echo "=== AGENT START ==="
            su - claude -c "
                export PATH=/usr/local/bin:/usr/bin:/bin:\$PATH
                export HOME=/home/claude
                export CLAUDE_CODE_MAX_OUTPUT_TOKENS=128000
                cd /workspace
                claude --dangerously-skip-permissions \
                    --max-turns '"$MAX_TURNS"' \
                    --output-format json \
                    --model '"$MODEL"' \
                    -p \"\$(cat /home/claude/task_instruction.md)\" \
                    2>/tmp/claude_stderr.log || true
            " 2>&1 | tee /logs/agent/output.json || true
            echo "=== AGENT END ==="

            # Run verification
            echo "=== VERIFY START ==="
            cd /workspace
            bash /tests/test.sh 2>&1 || true
            echo "=== VERIFY END ==="

            # Output reward
            echo "=== REWARD ==="
            cat /logs/verifier/reward.txt 2>/dev/null || echo "0.0"
        ' > "$RESULT_DIR/run_output.txt" 2>&1 || true

    rm -f "$INSTR_FILE"

    local END_TIME=$(date +%s)
    local ELAPSED=$((END_TIME - START_TIME))

    # Extract reward
    local REWARD
    REWARD=$(grep -A1 '=== REWARD ===' "$RESULT_DIR/run_output.txt" | tail -1 | tr -d '[:space:]')
    if [ -z "$REWARD" ] || [ "$REWARD" = "NO_REWARD" ]; then
        REWARD="0.0"
    fi

    # Validate reward is a number
    if ! echo "$REWARD" | python3 -c "import sys; float(sys.stdin.read().strip())" 2>/dev/null; then
        REWARD="0.0"
    fi

    echo ">>> [$TASK_ID] Done in ${ELAPSED}s — Reward: $REWARD"

    # Save result
    python3 -c "
import json
result = {
    'task_id': '$TASK_ID',
    'status': 'completed',
    'reward': float('$REWARD'),
    'model': '$MODEL',
    'config': 'baseline-local-direct',
    'elapsed_sec': $ELAPSED,
    'run_id': '$RUN_ID'
}
print(json.dumps(result, indent=2))
" > "$RESULT_DIR/result.json"

    echo "$TASK_ID,completed,$REWARD,$ELAPSED" >> "$RUN_DIR/summary.csv"
}

# Header for summary CSV
echo "task_id,status,reward,elapsed_sec" > "$RUN_DIR/summary.csv"

# Run tasks sequentially (each needs significant resources)
for task in "${TASKS[@]}"; do
    run_task "$task" || true
done

# Print summary
echo ""
echo "=============================================="
echo "RUN SUMMARY: $RUN_ID"
echo "=============================================="
printf "%-40s %-12s %-8s %-10s\n" "Task" "Status" "Reward" "Time(s)"
printf "%-40s %-12s %-8s %-10s\n" "$(printf '%0.s-' {1..40})" "$(printf '%0.s-' {1..12})" "$(printf '%0.s-' {1..8})" "$(printf '%0.s-' {1..10})"
tail -n +2 "$RUN_DIR/summary.csv" | while IFS=, read -r tid status reward elapsed; do
    printf "%-40s %-12s %-8s %-10s\n" "$tid" "$status" "$reward" "$elapsed"
done
echo ""
echo "Results: $RUN_DIR"
