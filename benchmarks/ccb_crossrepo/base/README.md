# Base Docker Image

This directory contains the Dockerfile and build script for `harbor-ccb_crossrepo:base`, the foundational image containing the 10Figure-Codebases corpus.

## Build Process

The base image includes:
- Ubuntu 22.04 base
- Python 3 + dependencies from requirements.txt
- Git, build tools, jq
- Full 10Figure corpus at `/ccb_crossrepo/`
- Validator script at `/ccb_crossrepo/scripts/validate_patch.py`

## Prerequisites

Before building, ensure you have built the 10Figure-Codebases corpus:

```bash
cd ~/10Figure-Codebases
make install
make build-corpus  # Takes ~15-20 minutes
```

## Building the Image

```bash
# Use default corpus path (~/10Figure-Codebases)
./build.sh

# Or specify custom corpus path
CORPUS_PATH=/path/to/10Figure-Codebases ./build.sh
```

The build process:
1. Copies the entire 10Figure-Codebases directory (~5GB) to a temp build context
2. Builds the Docker image with the corpus embedded
3. Tags as `harbor-ccb_crossrepo:base`

## Image Size

- Expected size: ~6-8GB (includes full corpus + dependencies)

## Verification

```bash
# Check corpus structure
docker run --rm harbor-ccb_crossrepo:base ls -la /ccb_crossrepo/src

# Should show: kubernetes, envoy, django, tensorflow, etc.
```

## Usage in Harbor Tasks

Harbor tasks inherit from this base image:

```dockerfile
FROM harbor-ccb_crossrepo:base

ENV REPO_ROOT=/ccb_crossrepo/src/kubernetes
RUN echo "$REPO_ROOT" > /task/repo_path
```

This avoids rebuilding the corpus for every task, leveraging Docker layer caching.

## Alternative: Podman

If using Podman instead of Docker:

```bash
# Replace 'docker' with 'podman' in build.sh, or:
podman build -t harbor-ccb_crossrepo:base -f Dockerfile /tmp/build-context
```
