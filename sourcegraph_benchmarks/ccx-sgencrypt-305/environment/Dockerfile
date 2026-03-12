FROM golang:1.26-bookworm

ARG GITHUB_TOKEN

RUN apt-get update && apt-get install -y --no-install-recommends \
    git ca-certificates python3 jq && \
    rm -rf /var/lib/apt/lists/*

# Clone repo at pinned commit for reproducibility
RUN git clone https://x-access-token:${GITHUB_TOKEN}@github.com/sourcegraph/sourcegraph.git /workspace && \
    cd /workspace && git checkout 461e2c0ccf9f114032cd8ff8bd3acc0e7335bea5

ENV TASK_WORKDIR=/workspace
ENV TASK_REPO_ROOT=/workspace
ENV TASK_OUTPUT=/workspace/answer.json

WORKDIR /workspace

RUN mkdir -p /logs/agent /logs/verifier

# Pre-create claude user and set ownership at build time so agent can write files.
RUN (adduser --disabled-password --gecos '' claude 2>/dev/null || true) && \
    for d in /workspace /app /testbed /logs; do [ -d "$d" ] && chown -R claude:claude "$d"; done || true

# Harness-agnostic: ensure all users (root/claude) can read+write workspace files
RUN chmod -R a+rwX /workspace

ENTRYPOINT []
