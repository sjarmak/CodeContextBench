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
RUN git clone --depth 1 https://github.com/sg-evals/llvm-project--a8f3c97d /workspace/llvm-project--a8f3c97d || \
    (mkdir -p /workspace/llvm-project--a8f3c97d && cd /workspace/llvm-project--a8f3c97d && git init && git config user.email "agent@example.com" && git config user.name "Agent")
RUN git clone --depth 1 https://github.com/sg-evals/gcc--96dfb333 /workspace/gcc--96dfb333 || \
    (mkdir -p /workspace/gcc--96dfb333 && cd /workspace/gcc--96dfb333 && git init && git config user.email "agent@example.com" && git config user.name "Agent")

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
