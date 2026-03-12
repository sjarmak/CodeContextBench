FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    ca-certificates \
    python3 \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /ccb_crossrepo/src

RUN git clone --depth 1 https://github.com/sg-evals/numpy--a639fbf5.git /ccb_crossrepo/src/numpy || \
    (mkdir -p /ccb_crossrepo/src/numpy && cd /ccb_crossrepo/src/numpy && git init && git config user.email "agent@example.com" && git config user.name "Agent")
RUN git clone --depth 1 https://github.com/sg-evals/pandas--41968da5.git /ccb_crossrepo/src/pandas || \
    (mkdir -p /ccb_crossrepo/src/pandas && cd /ccb_crossrepo/src/pandas && git init && git config user.email "agent@example.com" && git config user.name "Agent")

RUN (adduser --disabled-password --gecos '' claude 2>/dev/null || true)

WORKDIR /workspace

RUN git init && \
    git config user.email "agent@example.com" && \
    git config user.name "Agent" && \
    git config --global safe.directory '*'

RUN mkdir -p /logs/agent /logs/verifier && \
    chown -R claude:claude /workspace /logs /ccb_crossrepo

# Harness-agnostic: ensure all users (root/claude) can read+write workspace files
RUN chmod -R a+rwX /workspace

ENTRYPOINT []
