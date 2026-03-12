FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Base tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    ca-certificates \
    curl \
    python3 \
    g++ make \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

# Clone local checkout repos (baseline config: agent has local access to these)
RUN git clone --depth 1 https://github.com/sg-evals/envoy--v1.31.2 /workspace/envoy--v1.31.2 || \
    (mkdir -p /workspace/envoy--v1.31.2 && cd /workspace/envoy--v1.31.2 && git init && git config user.email "agent@example.com" && git config user.name "Agent")
RUN git clone --depth 1 https://github.com/sg-evals/data-plane-api--84e84367 /workspace/data-plane-api--84e84367 || \
    (mkdir -p /workspace/data-plane-api--84e84367 && cd /workspace/data-plane-api--84e84367 && git init && git config user.email "agent@example.com" && git config user.name "Agent")
RUN git clone --depth 1 https://github.com/sg-evals/go-control-plane--71637ad6 /workspace/go-control-plane--71637ad6 || \
    (mkdir -p /workspace/go-control-plane--71637ad6 && cd /workspace/go-control-plane--71637ad6 && git init && git config user.email "agent@example.com" && git config user.name "Agent")
RUN git clone --depth 1 https://github.com/sg-evals/grpc--957dba5e /workspace/grpc--957dba5e || \
    (mkdir -p /workspace/grpc--957dba5e && cd /workspace/grpc--957dba5e && git init && git config user.email "agent@example.com" && git config user.name "Agent")

# Initialize git identity for agent commits
RUN git config --global user.email "agent@example.com" && \
    git config --global user.name "Agent" && \
    git config --global safe.directory '*'

# Create log directories
RUN mkdir -p /logs/agent /logs/verifier
RUN chown -R claude:claude /logs

# Pre-create claude user and set ownership at build time so Harbor's
# runtime chown is a no-op (avoids 15-30 min delay on large repos).
RUN (adduser --disabled-password --gecos '' claude 2>/dev/null || true) && \
    for d in /workspace /app /testbed /logs; do [ -d "$d" ] && chown -R claude:claude "$d"; done || true

# Harness-agnostic: ensure all users (root/claude) can read+write workspace files
RUN chmod -R a+rwX /workspace

ENTRYPOINT []
