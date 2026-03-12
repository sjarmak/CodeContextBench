FROM ubuntu:22.04

# Install git and basic tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    ca-certificates \
    python3 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

# Clone Apache Kafka at a stable release tag (3.9.0 - latest stable as of Feb 2026)
RUN (git clone --depth 1 https://github.com/sg-evals/kafka--3.9.0.git . || (git init && git config user.email "agent@example.com" && git config user.name "Agent")) && \
    git config user.email "agent@benchmark.local" && \
    git config user.name "Agent"

# Create logs directory for agent output
RUN mkdir -p /logs/agent

# Create non-root user for agent harness compatibility
RUN (adduser --disabled-password --gecos '' claude 2>/dev/null || true) && \
    for d in /workspace /app /testbed /logs; do [ -d "$d" ] && chown -R claude:claude "$d"; done || true

CMD ["/bin/bash"]

# Harness-agnostic: ensure all users (root/claude) can read+write workspace files
RUN chmod -R a+rwX /workspace

ENTRYPOINT []
