FROM golang:1.26-bookworm

ARG GITHUB_TOKEN

RUN apt-get update && apt-get install -y --no-install-recommends \
    git ca-certificates jq && \
    rm -rf /var/lib/apt/lists/*

# Allow /workspace ownership mismatch (agent runs as different user)
RUN git config --global --add safe.directory /workspace

# Clone repo and checkout pre-fix commit
RUN git init /workspace && cd /workspace && \
    git remote add origin https://x-access-token:${GITHUB_TOKEN}@github.com/sourcegraph/sourcegraph.git && \
    git fetch --depth=1 origin 4755e84afad75751556f10beef150bfdba0d46d4 && \
    git checkout FETCH_HEAD

ENV TASK_WORKDIR=/workspace
ENV TASK_REPO_ROOT=/workspace

WORKDIR /workspace

# Configure Go for private modules
ENV GONOSUMCHECK=github.com/sourcegraph/*
ENV GOFLAGS=-mod=mod
ENV GOPRIVATE=github.com/sourcegraph/*

# Pre-download Go dependencies for the relevant packages
RUN go mod download -modcacherw 2>/dev/null || true

# Verify the test package exists at this commit
RUN go build ./cmd/frontend/internal/deepsearchapi/images/... 2>/dev/null || true

RUN mkdir -p /logs/agent /logs/verifier

# Pre-create claude user and set ownership at build time so agent can write files.
RUN (adduser --disabled-password --gecos '' claude 2>/dev/null || true) && \
    for d in /workspace /app /testbed /logs; do [ -d "$d" ] && chown -R claude:claude "$d"; done || true

# Harness-agnostic: ensure all users (root/claude) can read+write workspace files
RUN chmod -R a+rwX /workspace

ENTRYPOINT []
