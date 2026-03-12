FROM ubuntu:22.04

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    openjdk-17-jdk \
    python3 \
    && rm -rf /var/lib/apt/lists/*

# Clone Kafka at the pinned version
RUN git clone --depth 1 https://github.com/sg-evals/kafka--3.9.0.git /workspace || \
    (mkdir -p /workspace && cd /workspace && git init && git config user.email "agent@example.com" && git config user.name "Agent")

WORKDIR /workspace

# Create non-root user for agent harness compatibility
RUN (adduser --disabled-password --gecos '' claude 2>/dev/null || true) && \
    for d in /workspace /app /testbed /logs; do [ -d "$d" ] && chown -R claude:claude "$d"; done || true

# Harness-agnostic: ensure all users (root/claude) can read+write workspace files
RUN chmod -R a+rwX /workspace

ENTRYPOINT []
