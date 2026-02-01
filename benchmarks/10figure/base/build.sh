#!/bin/bash
set -e

# Build harbor-10figure:base Docker image with corpus

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

# Check if 10Figure-Codebases exists
CORPUS_PATH="${CORPUS_PATH:-$HOME/10Figure-Codebases}"

if [ ! -d "$CORPUS_PATH" ]; then
    echo "Error: 10Figure-Codebases not found at $CORPUS_PATH"
    echo "Set CORPUS_PATH environment variable or clone to ~/10Figure-Codebases"
    exit 1
fi

# Check if corpus is built
if [ ! -d "$CORPUS_PATH/src/kubernetes" ] || [ ! -d "$CORPUS_PATH/src/envoy" ]; then
    echo "Error: Corpus not built in $CORPUS_PATH"
    echo "Run 'make build-corpus' in $CORPUS_PATH first"
    exit 1
fi

echo "Building harbor-10figure:base Docker image..."
echo "Corpus path: $CORPUS_PATH"
echo "This will take a few minutes (copying ~5GB corpus)..."
echo ""

# Copy 10Figure-Codebases to build context
TEMP_DIR=$(mktemp -d)
trap "rm -rf $TEMP_DIR" EXIT

echo "Copying corpus to build context..."
cp -r "$CORPUS_PATH" "$TEMP_DIR/10Figure-Codebases"

# Build image
cd "$SCRIPT_DIR"
podman build -t harbor-10figure:base -f Dockerfile "$TEMP_DIR"

echo ""
echo "✓ Image built successfully: harbor-10figure:base"
echo ""
echo "To verify:"
echo "  docker run --rm harbor-10figure:base ls -la /10figure/src"
