#!/usr/bin/env bash
# Re-mirror sg-benchmarks repos at Dockerfile-pinned versions.
# These repos already exist on GitHub — we shallow-clone at the correct tag,
# create an orphan commit, and force-push to overwrite.
#
# Usage: bash scripts/remirror_mcp_unique_repos.sh
set -euo pipefail

SG_ORG="sg-benchmarks"
WORK_DIR=$(mktemp -d)
trap 'rm -rf "$WORK_DIR"' EXIT

SUCCESS=0
FAILED=0

# Format: "upstream_repo tag sg_name"
REPOS=(
    "expressjs/express 4.21.1 expressjs-express"
    "grafana/loki v3.3.4 grafana-loki"
    "kubernetes/client-go v0.32.0 kubernetes-client-go"
)

for entry in "${REPOS[@]}"; do
    read -r github_repo tag sg_name <<< "$entry"
    echo ""
    echo "=== Re-mirroring ${github_repo} @ ${tag} → ${SG_ORG}/${sg_name} ==="

    clone_dir="${WORK_DIR}/clone_${sg_name}"
    fresh_dir="${WORK_DIR}/fresh_${sg_name}"

    # Step 1: Shallow clone at the tag
    echo "  Cloning ${github_repo} at tag ${tag} (shallow)..."
    if ! git clone --depth 1 --branch "$tag" "https://github.com/${github_repo}.git" "$clone_dir" 2>&1; then
        echo "  ERROR: Failed to clone ${github_repo} at tag ${tag}"
        FAILED=$((FAILED + 1))
        continue
    fi

    actual_commit=$(git -C "$clone_dir" rev-parse HEAD)
    echo "  Cloned at commit ${actual_commit:0:12}"

    # Step 2: Create fresh repo with orphan commit (avoids shallow-pack push errors)
    echo "  Creating fresh repo with orphan commit..."
    mkdir -p "$fresh_dir"
    git -C "$fresh_dir" init -b main 2>&1
    rsync -a --exclude='.git' "$clone_dir/" "$fresh_dir/" 2>&1
    git -C "$fresh_dir" add -A 2>&1
    git -C "$fresh_dir" -c user.email="benchmark@sg-benchmarks.dev" -c user.name="sg-benchmarks" \
        commit -m "Re-mirror ${github_repo} @ ${tag} (${actual_commit:0:8}) — pin to Dockerfile version" --quiet 2>&1

    # Clean up shallow clone
    rm -rf "$clone_dir"

    # Step 3: Force-push to existing sg-benchmarks repo
    echo "  Force-pushing to ${SG_ORG}/${sg_name}..."
    git -C "$fresh_dir" remote add sg-target "https://github.com/${SG_ORG}/${sg_name}.git" 2>&1
    if ! git -C "$fresh_dir" push sg-target main --force 2>&1; then
        echo "  ERROR: Failed to push to ${SG_ORG}/${sg_name}"
        rm -rf "$fresh_dir"
        FAILED=$((FAILED + 1))
        continue
    fi

    echo "  SUCCESS: ${SG_ORG}/${sg_name} updated to ${tag}"
    SUCCESS=$((SUCCESS + 1))

    rm -rf "$fresh_dir"
done

echo ""
echo "=============================================="
echo "Re-mirror complete!"
echo "=============================================="
echo "Succeeded: $SUCCESS"
echo "Failed:    $FAILED"
echo ""
echo "Wait ~10-30 minutes for Sourcegraph indexing, then verify with:"
echo "  - Read sg-benchmarks/expressjs-express package.json → version should be 4.21.1"
echo "  - Read sg-benchmarks/grafana-loki pkg/loghttp/query.go → should exist"
echo "  - Search sg-benchmarks/kubernetes-client-go dynamic/ → verify file list"
