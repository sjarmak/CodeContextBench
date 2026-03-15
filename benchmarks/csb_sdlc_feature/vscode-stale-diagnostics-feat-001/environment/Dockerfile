FROM node:22-bookworm

WORKDIR /workspace

# Install dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    build-essential \
    python3 \
    python3-pip \
    libxkbfile-dev \
    libx11-dev \
    && rm -rf /var/lib/apt/lists/*

# Create claude user and writable work dirs before clone.
RUN (adduser --disabled-password --gecos '' claude 2>/dev/null || true) && \
    mkdir -p /workspace /logs && \
    chown -R claude:claude /workspace /logs

# Clone the actual VS Code repository at pinned commit (1.96.0)
# This ensures BOTH baseline and MCP agents have identical file access
USER claude
RUN (git clone --depth 1 https://github.com/sg-evals/vscode--138f619c.git . || (git init && git config user.email "agent@example.com" && git config user.name "Agent")) && \
    git config user.email "agent@example.com" && \
    git config user.name "Agent"
USER root

# Install VS Code dependencies (required for testing)
RUN npm install --legacy-peer-deps 2>&1 | tail -10 || true


ENTRYPOINT []
