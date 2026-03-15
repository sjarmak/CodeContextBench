FROM gcc:13

WORKDIR /workspace

# Install dependencies including curl for Node.js setup
RUN apt-get update && apt-get install -y --no-install-recommends cmake ninja-build git curl

# Install Node.js for Claude Code CLI
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

# Clone PyTorch repository at task-specific commit (no submodules needed)
RUN git clone --depth 1 https://github.com/sg-evals/pytorch--d18007a1.git /workspace || \
    (mkdir -p /workspace && cd /workspace && git init && git config user.email "agent@example.com" && git config user.name "Agent")

# Pre-create claude user and fix ownership so Harbor agent setup is instant
RUN (adduser --disabled-password --gecos '' claude 2>/dev/null || adduser -D -s /bin/bash claude 2>/dev/null || true) && \
    chown -R claude:claude /workspace

# Harness-agnostic: ensure all users (root/claude) can read+write workspace files

ENTRYPOINT []
