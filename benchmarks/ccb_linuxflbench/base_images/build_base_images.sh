#!/bin/bash
# Build pre-built Linux kernel base images for ccb_linuxflbench tasks.
#
# Each image contains gcc:13, common tools, Claude Code CLI, and the Linux
# kernel source tree checked out at a specific commit. Building these up front
# avoids a ~10-minute git clone during every Harbor run.
#
# Usage:
#   ./benchmarks/ccb_linuxflbench/base_images/build_base_images.sh [VERSION_TAG...]
#
# Examples:
#   ./build_base_images.sh              # Build all base images
#   ./build_base_images.sh v5.6.7       # Build only one version
#
# Images are tagged as:  ccb-linux-base:<version_tag>
#   e.g. ccb-linux-base:v5.6.7, ccb-linux-base:v5.6-rc2

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOCKERFILE="$SCRIPT_DIR/Dockerfile.linux-base"

# ── Kernel version → commit mapping ──────────────────────
# To add a new kernel version:
#   1. Find the commit hash:
#        curl -s https://api.github.com/repos/gregkh/linux/git/ref/tags/v<VER> | jq .object.sha
#        (then dereference if annotated tag — see README.md)
#   2. Add an entry to this associative array
#   3. Run this script
#   4. Update the task Dockerfile to:  FROM ccb-linux-base:v<VER>
declare -A VERSIONS=(
    ["v5.6.7"]="55b2af1c23eb12663015998079992f79fdfa56c8"
    ["v5.6-rc2"]="11a48a5a18c63fd7621bb050228cebf13566e4d8"
    ["v4.1.15"]="07cc49f66973f49a391c91bf4b158fa0f2562ca8"
    ["v4.14.114"]="fa5941f45d7ed070118b7c209b7f2c3a034293bd"
    ["v3.7.6"]="07c4ee001f13f489364c37dcd4947670da26a489"
)

# If specific versions requested, filter to those
if [ $# -gt 0 ]; then
    REQUESTED=("$@")
else
    REQUESTED=("${!VERSIONS[@]}")
fi

echo "=============================================="
echo "Building ccb_linuxflbench base images"
echo "=============================================="
echo "Dockerfile: $DOCKERFILE"
echo "Versions:   ${REQUESTED[*]}"
echo ""

BUILT=0
FAILED=0

for ver in "${REQUESTED[@]}"; do
    commit="${VERSIONS[$ver]}"
    if [ -z "$commit" ]; then
        echo "ERROR: Unknown version '$ver'. Available: ${!VERSIONS[*]}"
        FAILED=$((FAILED + 1))
        continue
    fi

    tag="ccb-linux-base:${ver}"
    echo "── Building $tag (commit ${commit:0:12}...) ──"

    if docker build \
        --build-arg "KERNEL_COMMIT=${commit}" \
        --build-arg "KERNEL_VERSION_LABEL=${ver}" \
        -t "$tag" \
        -f "$DOCKERFILE" \
        "$SCRIPT_DIR" ; then
        echo "OK: $tag"
        BUILT=$((BUILT + 1))
    else
        echo "FAIL: $tag"
        FAILED=$((FAILED + 1))
    fi
    echo ""
done

echo "=============================================="
echo "Done: $BUILT built, $FAILED failed"
echo "=============================================="
echo ""
echo "List built images:"
echo "  docker images 'ccb-linux-base'"
