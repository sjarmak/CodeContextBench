FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ca-certificates \
        git \
        openjdk-21-jdk-headless \
        python3 \
        vim \
        && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /repo

# Clone Apache Kafka at specific commit (e678b4b, trunk 2026-02-16)
# Use blobless clone + sparse-checkout for speed
RUN git clone --depth 1 https://github.com/sg-evals/kafka--e678b4b.git . || \
    (git init && git config user.email "agent@example.com" && git config user.name "Agent")

WORKDIR /workspace

# Create non-root user for agent harness compatibility
RUN (adduser --disabled-password --gecos '' claude 2>/dev/null || true) && \
    for d in /workspace /app /testbed /logs; do [ -d "$d" ] && chown -R claude:claude "$d"; done || true

# Harness-agnostic: ensure all users (root/claude) can read+write workspace files

ENTRYPOINT []
