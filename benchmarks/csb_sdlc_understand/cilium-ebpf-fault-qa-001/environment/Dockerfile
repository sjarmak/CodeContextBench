FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Install git and dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends git ca-certificates python3 && \
    rm -rf /var/lib/apt/lists/*

# Clone Cilium at pinned commit (v1.17.9)
RUN git clone --depth 1 https://github.com/sg-evals/cilium--a2f97aa8.git /workspace/cilium || \
    (mkdir -p /workspace/cilium && cd /workspace/cilium && git init && git config user.email "agent@example.com" && git config user.name "Agent")

WORKDIR /workspace/cilium

# Create non-root user for agent harness compatibility
RUN (adduser --disabled-password --gecos '' claude 2>/dev/null || true) && \
    for d in /workspace /app /testbed /logs; do [ -d "$d" ] && chown -R claude:claude "$d"; done || true

# Harness-agnostic: ensure all users (root/claude) can read+write workspace files

ENTRYPOINT []
