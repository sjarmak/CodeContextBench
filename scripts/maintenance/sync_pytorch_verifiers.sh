#!/bin/bash
# Sync verify_diff.py and generate test.sh for all PyTorch diff-verified tasks.
#
# Usage:
#   bash scripts/sync_pytorch_verifiers.sh
#   bash scripts/sync_pytorch_verifiers.sh --dry-run

set -eo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
PYTORCH_DIR="$REPO_ROOT/benchmarks/ccb_pytorch"
SHARED_DIR="$PYTORCH_DIR/_shared"

DIFF_TASKS=(sgt-002 sgt-003 sgt-005 sgt-007 sgt-009 sgt-010 sgt-014 sgt-016 sgt-017 sgt-021 sgt-024)

DRY_RUN=false
if [[ "$1" == "--dry-run" ]]; then
    DRY_RUN=true
    echo "=== DRY RUN ==="
fi

# Verify shared files exist
if [[ ! -f "$SHARED_DIR/verify_diff.py" ]]; then
    echo "ERROR: $SHARED_DIR/verify_diff.py not found"
    exit 1
fi
if [[ ! -f "$SHARED_DIR/test.sh.template" ]]; then
    echo "ERROR: $SHARED_DIR/test.sh.template not found"
    exit 1
fi

for TASK_ID in "${DIFF_TASKS[@]}"; do
    TASK_DIR="$PYTORCH_DIR/$TASK_ID"
    TESTS_DIR="$TASK_DIR/tests"
    TOML_FILE="$TASK_DIR/task.toml"

    if [[ ! -f "$TOML_FILE" ]]; then
        echo "ERROR: $TOML_FILE not found, skipping $TASK_ID"
        continue
    fi

    # Extract pre_fix_rev from task.toml
    PRE_FIX_REV=$(grep -E '^pre_fix_rev' "$TOML_FILE" | head -1 | sed 's/.*= *"\(.*\)"/\1/')

    if [[ -z "$PRE_FIX_REV" ]]; then
        echo "ERROR: No pre_fix_rev in $TOML_FILE, skipping $TASK_ID"
        continue
    fi

    echo "$TASK_ID: pre_fix_rev=$PRE_FIX_REV"

    if $DRY_RUN; then
        echo "  Would copy verify_diff.py to $TESTS_DIR/"
        echo "  Would generate test.sh with PRE_FIX_REV=$PRE_FIX_REV"
        continue
    fi

    mkdir -p "$TESTS_DIR"

    # Copy verify_diff.py
    cp "$SHARED_DIR/verify_diff.py" "$TESTS_DIR/verify_diff.py"
    echo "  Copied verify_diff.py"

    # Generate test.sh from template
    sed "s/{PRE_FIX_REV}/$PRE_FIX_REV/g" "$SHARED_DIR/test.sh.template" > "$TESTS_DIR/test.sh"
    chmod +x "$TESTS_DIR/test.sh"
    echo "  Generated test.sh"
done

echo ""
echo "Done. ${#DIFF_TASKS[@]} tasks processed."
