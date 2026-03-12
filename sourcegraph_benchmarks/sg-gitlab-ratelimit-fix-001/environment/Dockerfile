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
    git fetch --depth=1 origin 531aad57d54123d359fa4262505f19b055341b3f && \
    git checkout FETCH_HEAD

ENV TASK_WORKDIR=/workspace
ENV TASK_REPO_ROOT=/workspace

WORKDIR /workspace

# Configure Go to skip checksum DB and allow direct fetch for private modules
ENV GONOSUMCHECK=github.com/sourcegraph/*
ENV GOFLAGS=-mod=mod
ENV GOPRIVATE=github.com/sourcegraph/*

# Configure git auth for Go private module fetching (e.g. sourcegraph/sourceflow)
RUN echo "machine github.com login x-access-token password ${GITHUB_TOKEN}" > /root/.netrc && chmod 600 /root/.netrc

# Pre-download Go dependencies for the relevant packages.
# Use -modcacherw so the agent can update go.sum if needed.
RUN go mod download -modcacherw 2>/dev/null || true

# Pre-build the test packages to cache compilation (ignore private dep errors)
RUN go build ./cmd/frontend/internal/auth/gitlaboauth/... 2>/dev/null || true && \
    go build ./internal/extsvc/gitlab/... 2>/dev/null || true

RUN mkdir -p /logs/agent /logs/verifier

# Pre-create claude user and set ownership at build time.
# Copy .netrc for agent user so go test can also fetch private deps at runtime.
RUN (adduser --disabled-password --gecos '' claude 2>/dev/null || true) && \
    cp /root/.netrc /home/claude/.netrc && chown claude:claude /home/claude/.netrc && \
    for d in /workspace /app /testbed /logs; do [ -d "$d" ] && chown -R claude:claude "$d"; done || true

# Harness-agnostic: ensure all users (root/claude) can read+write workspace files
RUN chmod -R a+rwX /workspace

ENTRYPOINT []
