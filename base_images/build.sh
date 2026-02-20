#!/bin/bash
# Build all CCB base images for Docker layer caching.
# Run this ONCE before a benchmark batch. Subsequent task builds
# will reuse these cached layers instead of re-cloning repos.
#
# Usage: ./base_images/build.sh [--parallel]

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Enable BuildKit
export DOCKER_BUILDKIT=1

PARALLEL=false
if [ "${1:-}" = "--parallel" ]; then
    PARALLEL=true
fi

build_image() {
    local dockerfile="$1"
    local tag="$2"

    # Skip if image already exists and is recent (< 7 days old)
    local image_age
    image_age=$(docker inspect --format='{{.Created}}' "$tag" 2>/dev/null || echo "")
    if [ -n "$image_age" ]; then
        local age_seconds
        age_seconds=$(( $(date +%s) - $(date -d "$image_age" +%s 2>/dev/null || echo 0) ))
        if [ "$age_seconds" -lt 604800 ]; then
            echo "SKIP $tag (exists, ${age_seconds}s old)"
            return 0
        fi
    fi

    echo "BUILD $tag ..."
    local start_time=$SECONDS
    docker build -f "$dockerfile" -t "$tag" "$SCRIPT_DIR" 2>&1 | tail -5
    local elapsed=$(( SECONDS - start_time ))
    echo "DONE  $tag (${elapsed}s)"
}

echo "=== Building CCB base images ==="
echo ""

IMAGES=(
    "Dockerfile.django-674eda1c    ccb-repo-django-674eda1c"
    "Dockerfile.django-9e7cc2b6    ccb-repo-django-9e7cc2b6"
    "Dockerfile.flipt-3d5a345f     ccb-repo-flipt-3d5a345f"
    "Dockerfile.k8s-11602f08       ccb-repo-k8s-11602f08"
    "Dockerfile.k8s-8c9c67c0       ccb-repo-k8s-8c9c67c0"
    "Dockerfile.kafka-0753c489     ccb-repo-kafka-0753c489"
    "Dockerfile.kafka-e678b4b      ccb-repo-kafka-e678b4b"
    "Dockerfile.flink-0cc95fcc     ccb-repo-flink-0cc95fcc"
    "Dockerfile.camel-1006f047     ccb-repo-camel-1006f047"
    "Dockerfile.postgres-5a461dc4  ccb-repo-postgres-5a461dc4"
    "Dockerfile.strata-66225ca9    ccb-repo-strata-66225ca9"
    "Dockerfile.curl-09e25b9d      ccb-repo-curl-09e25b9d"
    "Dockerfile.envoy-1d0ba73a     ccb-repo-envoy-1d0ba73a"
    "Dockerfile.envoy-d7809ba2     ccb-repo-envoy-d7809ba2"
)

TOTAL_START=$SECONDS

if $PARALLEL; then
    echo "Building ${#IMAGES[@]} images in parallel (max 4 concurrent)..."
    for entry in "${IMAGES[@]}"; do
        read -r dockerfile tag <<< "$entry"
        (build_image "$SCRIPT_DIR/$dockerfile" "$tag") &
        # Limit to 4 concurrent builds
        while [ "$(jobs -rp | wc -l)" -ge 4 ]; do
            wait -n 2>/dev/null || true
        done
    done
    wait
else
    echo "Building ${#IMAGES[@]} images sequentially..."
    for entry in "${IMAGES[@]}"; do
        read -r dockerfile tag <<< "$entry"
        build_image "$SCRIPT_DIR/$dockerfile" "$tag"
    done
fi

TOTAL_ELAPSED=$(( SECONDS - TOTAL_START ))
echo ""
echo "=== All base images built in ${TOTAL_ELAPSED}s ==="
echo ""
echo "Base images available:"
docker images --format "  {{.Repository}}:{{.Tag}}  {{.Size}}" | grep ccb-repo || true
