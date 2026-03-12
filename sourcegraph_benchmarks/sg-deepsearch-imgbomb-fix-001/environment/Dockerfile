FROM golang:1.26-bookworm

ARG GITHUB_TOKEN

RUN apt-get update && apt-get install -y --no-install-recommends \
    git ca-certificates jq && \
    rm -rf /var/lib/apt/lists/*

# Allow /workspace ownership mismatch (agent runs as different user)
RUN git config --global --add safe.directory /workspace

# Clone repo and checkout pre-fix commit
RUN git init /workspace && cd /workspace && \
    git remote add origin https://x-access-token:${GITHUB_TOKEN}@github.com/sourcegraph/sourcegraph.git && \
    git fetch --depth=1 origin 4755e84afad75751556f10beef150bfdba0d46d4 && \
    git checkout FETCH_HEAD

ENV TASK_WORKDIR=/workspace
ENV TASK_REPO_ROOT=/workspace

WORKDIR /workspace

# Use Go module proxy; skip checksum for pseudo-version modules.
# Do NOT set GOPRIVATE — it bypasses the proxy and forces direct git access.
ENV GONOSUMCHECK=github.com/sourcegraph/*
ENV GOFLAGS=-mod=mod

# Pre-download Go dependencies for the relevant packages
RUN go mod download -modcacherw 2>/dev/null || true

# Verify the test package exists at this commit
RUN go build ./cmd/frontend/internal/deepsearchapi/images/... 2>/dev/null || true

# Configure git auth for Go private module fetching (e.g. sourcegraph/sourceflow)
RUN echo "machine github.com login x-access-token password ${GITHUB_TOKEN}" > /root/.netrc && chmod 600 /root/.netrc

RUN mkdir -p /logs/agent /logs/verifier

# Pre-create claude user and set ownership at build time so agent can write files.
RUN (adduser --disabled-password --gecos '' claude 2>/dev/null || true) && \
    cp /root/.netrc /home/claude/.netrc && chown claude:claude /home/claude/.netrc && \
    for d in /workspace /app /testbed /logs; do [ -d "$d" ] && chown -R claude:claude "$d"; done || true

# Harness-agnostic: ensure all users (root/claude) can read+write workspace files
RUN chmod -R a+rwX /workspace

ENTRYPOINT []
