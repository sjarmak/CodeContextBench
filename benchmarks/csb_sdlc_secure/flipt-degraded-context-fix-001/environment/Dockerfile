FROM golang:1.21-bookworm

WORKDIR /workspace

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Clone Flipt at pinned commit
RUN (git clone --depth 1 https://github.com/sg-evals/flipt--3d5a345f.git . || (git init && git config user.email "agent@example.com" && git config user.name "Agent")) && \
    git config user.email "agent@example.com" && \
    git config user.name "Agent"

# Download Go modules
RUN go mod download 2>/dev/null || true

# Simulate degraded context: remove key dependency files
# These files exist in the Sourcegraph index but not in the local workspace
# The agent must infer types from usage patterns or search remotely via MCP
RUN rm -f internal/storage/storage.go && \
    rm -f rpc/flipt/evaluation/evaluation.proto && \
    rm -f rpc/flipt/flipt.proto

# Create non-root user for agent harness compatibility
RUN (adduser --disabled-password --gecos '' claude 2>/dev/null || true) && \
    for d in /workspace /app /testbed /logs; do [ -d "$d" ] && chown -R claude:claude "$d"; done || true

# Harness-agnostic: ensure all users (root/claude) can read+write workspace files

ENTRYPOINT []
