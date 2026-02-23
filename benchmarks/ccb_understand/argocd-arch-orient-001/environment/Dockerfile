FROM golang:1.23-bookworm

WORKDIR /workspace

# Install dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    python3 \
    && rm -rf /var/lib/apt/lists/*

# Clone Argo CD at a stable release tag
# v2.13.2 is a recent stable release with well-established structure
RUN git clone --depth 1 https://github.com/sg-benchmarks/argo-cd--v2.13.2.git . && \
    git config user.email "agent@example.com" && \
    git config user.name "Agent"

# Create output directories
RUN mkdir -p /logs/agent /logs/verifier
