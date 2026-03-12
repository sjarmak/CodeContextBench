FROM python:3.12-bookworm

WORKDIR /workspace

# Install dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Clone Django at pinned commit (5.2)
RUN (git clone --depth 1 https://github.com/sg-evals/django--6b995cff.git . || (git init && git config user.email "agent@example.com" && git config user.name "Agent")) && \
    git config user.email "agent@example.com" && \
    git config user.name "Agent"

# Create non-root user for agent harness compatibility
RUN (adduser --disabled-password --gecos '' claude 2>/dev/null || true) && \
    for d in /workspace /app /testbed /logs; do [ -d "$d" ] && chown -R claude:claude "$d"; done || true

# Harness-agnostic: ensure all users (root/claude) can read+write workspace files
RUN chmod -R a+rwX /workspace

ENTRYPOINT []
