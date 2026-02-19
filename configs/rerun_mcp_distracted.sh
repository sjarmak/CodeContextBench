#!/bin/bash
# Targeted rerun of 36 MCP-distracted tasks (SG_full reward < baseline - 0.10).
#
# Root causes:
#   (a) 6 code review tasks — Dockerfile.sg_only bug (defect injection missing)
#   (b) 11 doc-gen/understand/debug tasks — genuine mild distraction
#   (c) 19 tasks with SG_full=0.0 — likely infra failures (rate limits) + navprove bugs
#
# The V4 preamble now includes "Local File Editing" guidance to reduce over-reading.
# This rerun tests whether the preamble fix improves SG_full scores.
#
# Usage:
#   ./configs/rerun_mcp_distracted.sh                  # all 36 tasks
#   ./configs/rerun_mcp_distracted.sh --suite build     # only build suite
#   ./configs/rerun_mcp_distracted.sh --full-only       # SG_full only (skip baseline)

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Parse args
SUITE_FILTER=""
EXTRA_ARGS=()
while [[ $# -gt 0 ]]; do
    case $1 in
        --suite) SUITE_FILTER="$2"; shift 2 ;;
        *) EXTRA_ARGS+=("$1"); shift ;;
    esac
done

run_suite() {
    local suite=$1
    shift
    local tasks=("$@")

    if [ -n "$SUITE_FILTER" ] && [ "$SUITE_FILTER" != "$suite" ]; then
        return
    fi

    echo ""
    echo "=========================================="
    echo "Rerunning $suite: ${#tasks[@]} distracted tasks"
    echo "=========================================="

    local task_flags=""
    for t in "${tasks[@]}"; do
        task_flags="$task_flags --task $t"
    done

    "$SCRIPT_DIR/${suite}_2config.sh" $task_flags "${EXTRA_ARGS[@]}"
}

# ── build (3 tasks) ──
run_suite build \
    flipt-dep-refactor-001 \
    rust-subtype-relation-refac-001 \
    flink-pricing-window-feat-001

# ── debug (5 tasks) ──
run_suite debug \
    envoy-duplicate-headers-debug-001 \
    istio-xds-destrul-debug-001 \
    qutebrowser-download-regression-prove-001 \
    qutebrowser-bookmark-regression-prove-001 \
    qutebrowser-tab-regression-prove-001

# ── design (4 tasks) ──
run_suite design \
    django-pre-validate-signal-design-001 \
    k8s-dra-allocation-impact-001 \
    camel-routing-arch-001 \
    kafka-flink-streaming-arch-001 \
    flipt-protobuf-metadata-design-001

# ── document (5 tasks) ──
run_suite document \
    k8s-controller-mgr-doc-gen-001 \
    k8s-applyconfig-doc-gen-001 \
    envoy-migration-doc-gen-001 \
    k8s-clientgo-doc-gen-001 \
    k8s-fairqueuing-doc-gen-001

# ── fix (1 task) ──
run_suite fix \
    django-modelchoice-fk-fix-001

# ── secure (5 tasks) ──
run_suite secure \
    django-policy-enforcement-001 \
    curl-cve-triage-001 \
    django-sensitive-file-exclusion-001 \
    grpcurl-transitive-vuln-001 \
    flipt-degraded-context-fix-001 \
    django-cross-team-boundary-001

# ── test (7 tasks) ──
run_suite test \
    terraform-code-review-001 \
    kafka-security-review-001 \
    vscode-code-review-001 \
    ghost-code-review-001 \
    envoy-code-review-001 \
    curl-security-review-001 \
    pandas-groupby-perf-001 \
    test-unitgen-py-001

# ── understand (2 tasks) ──
run_suite understand \
    kafka-message-lifecycle-qa-001 \
    terraform-state-backend-handoff-001 \
    cilium-ebpf-fault-qa-001

echo ""
echo "=========================================="
echo "MCP distraction rerun complete"
echo "=========================================="
