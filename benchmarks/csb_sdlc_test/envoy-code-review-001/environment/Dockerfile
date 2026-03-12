FROM ubuntu:22.04

# Install common tools (python3 needed for inject_defects.sh)
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    ca-certificates \
    curl \
    python3 \
    ripgrep \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js (for Claude Code CLI)
RUN if ! command -v node &> /dev/null; then \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y --no-install-recommends nodejs; \
    fi

# Clone envoyproxy/envoy at pinned v1.33.0 tag (sparse checkout for relevant files)
RUN (git clone --depth 1 https://github.com/sg-evals/envoy--v1.33.0.git /workspace || (mkdir -p /workspace && cd /workspace && git init && git config user.email "agent@example.com" && git config user.name "Agent")) && \
    cd /workspace && \
    git config user.email "agent@example.com" && \
    git config user.name "Agent"

# Inject defects into the codebase
COPY inject_defects.sh /tmp/inject_defects.sh
RUN chmod +x /tmp/inject_defects.sh && /tmp/inject_defects.sh && rm /tmp/inject_defects.sh

# Create directories for verifier (tests uploaded at runtime by Harbor verifier)
RUN mkdir -p /workspace/tests /logs/verifier

WORKDIR /workspace

# Create non-root user for agent harness compatibility
RUN (adduser --disabled-password --gecos '' claude 2>/dev/null || true) && \
    for d in /workspace /app /testbed /logs; do [ -d "$d" ] && chown -R claude:claude "$d"; done || true

# Harness-agnostic: ensure all users (root/claude) can read+write workspace files
RUN chmod -R a+rwX /workspace

ENTRYPOINT []
