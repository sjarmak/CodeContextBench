FROM node:22-bookworm

ARG GITHUB_TOKEN

RUN apt-get update && apt-get install -y --no-install-recommends \
    git ca-certificates jq && \
    rm -rf /var/lib/apt/lists/*

# Install pnpm at the version required by the repo
RUN corepack enable && corepack prepare pnpm@10.13.1 --activate

# Clone repo and checkout pre-fix commit
RUN git init /workspace && cd /workspace && \
    git remote add origin https://x-access-token:${GITHUB_TOKEN}@github.com/sourcegraph/sourcegraph.git && \
    git fetch --depth=1 origin 43d72ff447ebaac8c134bcabf1c6d8a0b76694e4 && \
    git checkout FETCH_HEAD

ENV TASK_WORKDIR=/workspace
ENV TASK_REPO_ROOT=/workspace

WORKDIR /workspace

# Install JS dependencies (pnpm workspace).
# vitest.workspace.ts imports js-yaml at the root, so ensure it is available.
RUN pnpm install --frozen-lockfile 2>/dev/null || pnpm install 2>/dev/null || true
RUN pnpm add -w -D js-yaml 2>/dev/null || npm install js-yaml 2>/dev/null || true

# Pre-install vitest so it's cached for test runs
RUN npx vitest --version 2>/dev/null || true

RUN mkdir -p /logs/agent /logs/verifier

# Pre-create claude user and set ownership at build time so agent can write files.
RUN (adduser --disabled-password --gecos '' claude 2>/dev/null || true) && \
    for d in /workspace /app /testbed /logs; do [ -d "$d" ] && chown -R claude:claude "$d"; done || true

# Harness-agnostic: ensure all users (root/claude) can read+write workspace files
RUN chmod -R a+rwX /workspace

ENTRYPOINT []
