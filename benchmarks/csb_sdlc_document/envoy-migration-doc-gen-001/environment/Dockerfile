FROM ubuntu:22.04

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    python3 \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

# Clone Envoy at v1.30 and v1.31 tags
RUN git clone --depth 1 https://github.com/sg-evals/envoy--50ea83e6.git envoy-v1.30 || \
    (mkdir -p envoy-v1.30 && cd envoy-v1.30 && git init && git config user.email "agent@example.com" && git config user.name "Agent")
RUN git clone --depth 1 https://github.com/sg-evals/envoy--7b8baff1.git envoy-v1.31 || \
    (mkdir -p envoy-v1.31 && cd envoy-v1.31 && git init && git config user.email "agent@example.com" && git config user.name "Agent")

WORKDIR /workspace

# Create non-root user for agent harness compatibility
RUN (adduser --disabled-password --gecos '' claude 2>/dev/null || true) && \
    for d in /workspace /app /testbed /logs; do [ -d "$d" ] && chown -R claude:claude "$d"; done || true

# Harness-agnostic: ensure all users (root/claude) can read+write workspace files

ENTRYPOINT []
