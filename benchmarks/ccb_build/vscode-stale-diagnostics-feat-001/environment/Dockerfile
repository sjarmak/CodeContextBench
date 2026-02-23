FROM node:22-bookworm

WORKDIR /workspace

# Install dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    build-essential \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Clone the actual VS Code repository at pinned commit (1.96.0)
# This ensures BOTH baseline and MCP agents have identical file access
RUN git clone --depth 1 https://github.com/sg-evals/vscode--138f619c.git . && \
    git config user.email "agent@example.com" && \
    git config user.name "Agent"

# Install VS Code dependencies (required for testing)
RUN npm install --legacy-peer-deps 2>&1 | tail -10 || true

# Task setup complete
# Note: Both baseline and MCP agents now have access to the real VS Code source.
# Baseline will use local grep/find/rg. MCP will use Sourcegraph semantic search.
