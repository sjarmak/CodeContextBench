FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update -qq && apt-get install -y -qq --no-install-recommends \
    git \
    curl \
    ca-certificates \
    python3 \
    python3-pip \
    jq \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

# Clone kubernetes/api (same pinned SHA as crossrepo-chain-001)
RUN git clone --depth 1 https://github.com/sg-evals/api--f32ed1d6.git api || \
    (mkdir -p api && cd api && git init && git config user.email "agent@example.com" && git config user.name "Agent")

# Clone kubernetes/apimachinery (same pinned SHA as crossrepo-chain-001)
RUN git clone --depth 1 https://github.com/sg-evals/apimachinery--b2e9f88f.git apimachinery || \
    (mkdir -p apimachinery && cd apimachinery && git init && git config user.email "agent@example.com" && git config user.name "Agent")

RUN mkdir -p /logs/verifier /logs/agent

# Create non-root user for agent harness compatibility
RUN (adduser --disabled-password --gecos '' claude 2>/dev/null || true) && \
    for d in /workspace /app /testbed /logs; do [ -d "$d" ] && chown -R claude:claude "$d"; done || true

CMD ["/bin/bash"]

# Harness-agnostic: ensure all users (root/claude) can read+write workspace files

ENTRYPOINT []
