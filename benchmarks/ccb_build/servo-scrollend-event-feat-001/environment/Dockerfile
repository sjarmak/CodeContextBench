FROM rust:1.83-bookworm

WORKDIR /workspace

# Install dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    python3 \
    python3-pip \
    build-essential \
    autoconf \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Clone the actual Servo repository at pinned commit
# This ensures BOTH baseline and MCP agents have identical file access
# Note: Servo is a large Rust codebase (~1.6GB)
RUN git clone --depth 1 https://github.com/sg-evals/servo--be6a2f99.git . && \
    git config user.email "agent@example.com" && \
    git config user.name "Agent"

# Task setup complete
# Note: Both baseline and MCP agents now have access to the real Servo source.
# Baseline will use local grep/find/rg. MCP will use Sourcegraph semantic search.
