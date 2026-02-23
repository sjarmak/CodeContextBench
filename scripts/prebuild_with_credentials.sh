#!/bin/bash
# Pre-build task Docker images by injecting GitHub credentials for git clone.
# Docker build containers can't access the host's git credential store, so
# this script patches Dockerfiles on the fly to include a GitHub token.
#
# Usage: bash scripts/prebuild_with_credentials.sh [--suite ccb_build] [--task task-name]
#        Defaults to all SDLC suites.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJ_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
BENCHMARK_DIR="$PROJ_DIR/benchmarks"

# Parse args
SUITES=()
TASKS=()
FORCE=false
MAX_PARALLEL=4

while [[ $# -gt 0 ]]; do
    case $1 in
        --suite) SUITES+=("$2"); shift 2 ;;
        --task) TASKS+=("$2"); shift 2 ;;
        --force) FORCE=true; shift ;;
        --parallel) MAX_PARALLEL="$2"; shift 2 ;;
        *) echo "Unknown: $1"; exit 1 ;;
    esac
done

if [ ${#SUITES[@]} -eq 0 ]; then
    SUITES=(ccb_build ccb_debug ccb_design ccb_document ccb_fix ccb_secure ccb_test ccb_understand)
fi

# Extract GitHub PAT from .git-credentials
GH_TOKEN=""
if [ -f "$HOME/.git-credentials" ]; then
    GH_TOKEN=$(grep "^https://.*@github.com" "$HOME/.git-credentials" | head -1 | sed 's|https://[^:]*:\([^@]*\)@github.com.*|\1|')
fi

if [ -z "$GH_TOKEN" ]; then
    echo "ERROR: No GitHub token found in ~/.git-credentials"
    exit 1
fi
echo "GitHub token: ${#GH_TOKEN} chars"

# Counters
BUILT=0
SKIPPED=0
FAILED=0
ERRORS=()

build_task_image() {
    local task_dir="$1"
    local task_name=$(basename "$task_dir")
    local dockerfile="$task_dir/environment/Dockerfile"
    local image_name="hb__${task_name}"

    # Skip if image already exists (unless --force)
    if [ "$FORCE" = false ] && docker images -q "$image_name" 2>/dev/null | grep -q .; then
        echo "SKIP $image_name (cached)"
        ((SKIPPED++)) || true
        return 0
    fi

    # Skip if Dockerfile doesn't need GitHub access
    if ! grep -q "git clone.*github.com/sg-evals/" "$dockerfile" 2>/dev/null; then
        echo "SKIP $image_name (no sg-evals clone)"
        ((SKIPPED++)) || true
        return 0
    fi

    # Create temp directory with patched Dockerfile
    local tmpdir
    tmpdir=$(mktemp -d)

    # Copy entire environment directory
    cp -a "$task_dir/environment/." "$tmpdir/"

    # Patch Dockerfile: add ARG and inject token into clone URLs
    # Replace: git clone ... https://github.com/sg-evals/...
    # With: credential setup + git clone
    local patched="$tmpdir/Dockerfile"

    # Add ARG after the first FROM line
    sed -i '0,/^FROM /{/^FROM /a\ARG GITHUB_TOKEN
}' "$patched"

    # Replace sg-evals clone URLs to include token
    sed -i "s|https://github.com/sg-evals/|https://x-access-token:\${GITHUB_TOKEN}@github.com/sg-evals/|g" "$patched"

    echo "BUILD $image_name ..."
    local start=$SECONDS
    if docker build \
        --build-arg "GITHUB_TOKEN=$GH_TOKEN" \
        -f "$patched" \
        -t "$image_name" \
        "$tmpdir" \
        > "/tmp/prebuild_cred_${task_name}.log" 2>&1; then
        local elapsed=$(( SECONDS - start ))
        echo "OK   $image_name (${elapsed}s)"
        ((BUILT++)) || true
    else
        local elapsed=$(( SECONDS - start ))
        echo "ERR  $image_name (${elapsed}s) — see /tmp/prebuild_cred_${task_name}.log"
        ERRORS+=("$task_name")
        ((FAILED++)) || true
    fi

    rm -rf "$tmpdir"
}

build_sgonly_image() {
    local task_dir="$1"
    local task_name=$(basename "$task_dir")
    local sgonly="$task_dir/environment/Dockerfile.sg_only"
    local image_name="hb__sgonly_${task_name}"

    # Skip if image already exists
    if [ "$FORCE" = false ] && docker images -q "$image_name" 2>/dev/null | grep -q .; then
        return 0
    fi

    # Skip if no sg_only Dockerfile
    if [ ! -f "$sgonly" ]; then
        return 0
    fi

    # sg_only Dockerfiles shouldn't need GitHub access (they have empty workspace)
    # but some still clone repos. Patch them too if needed.
    local tmpdir
    tmpdir=$(mktemp -d)
    cp -a "$task_dir/environment/." "$tmpdir/"
    cp "$sgonly" "$tmpdir/Dockerfile"

    if grep -q "git clone.*github.com/sg-evals/" "$tmpdir/Dockerfile" 2>/dev/null; then
        sed -i '0,/^FROM /{/^FROM /a\ARG GITHUB_TOKEN
}' "$tmpdir/Dockerfile"
        sed -i "s|https://github.com/sg-evals/|https://x-access-token:\${GITHUB_TOKEN}@github.com/sg-evals/|g" "$tmpdir/Dockerfile"

        if docker build \
            --build-arg "GITHUB_TOKEN=$GH_TOKEN" \
            -f "$tmpdir/Dockerfile" \
            -t "$image_name" \
            "$tmpdir" \
            > "/tmp/prebuild_cred_sgonly_${task_name}.log" 2>&1; then
            echo "OK   $image_name (sg_only)"
        else
            echo "ERR  $image_name (sg_only)"
        fi
    else
        if docker build \
            -f "$tmpdir/Dockerfile" \
            -t "$image_name" \
            "$tmpdir" \
            > "/tmp/prebuild_cred_sgonly_${task_name}.log" 2>&1; then
            true
        else
            echo "ERR  $image_name (sg_only)"
        fi
    fi

    rm -rf "$tmpdir"
}

echo "=== Pre-building with GitHub credentials ==="
echo "Suites: ${SUITES[*]}"
echo "Max parallel: $MAX_PARALLEL"
echo ""

START=$SECONDS

for suite in "${SUITES[@]}"; do
    echo "--- $suite ---"
    for task_dir in "$BENCHMARK_DIR/$suite"/*/; do
        [ -d "$task_dir/environment" ] || continue
        task_name=$(basename "$task_dir")

        # Filter by task name if specified
        if [ ${#TASKS[@]} -gt 0 ]; then
            match=false
            for t in "${TASKS[@]}"; do
                if [ "$t" = "$task_name" ]; then match=true; break; fi
            done
            $match || continue
        fi

        # Build both baseline and sg_only images
        (
            build_task_image "$task_dir"
            build_sgonly_image "$task_dir"
        ) &

        # Limit concurrent builds
        while [ "$(jobs -rp | wc -l)" -ge "$MAX_PARALLEL" ]; do
            wait -n 2>/dev/null || true
        done
    done
done

wait

ELAPSED=$(( SECONDS - START ))
echo ""
echo "=== Pre-build complete in ${ELAPSED}s ==="
echo "Built: $BUILT  Skipped: $SKIPPED  Failed: $FAILED"
if [ ${#ERRORS[@]} -gt 0 ]; then
    echo "Failed tasks: ${ERRORS[*]}"
fi
