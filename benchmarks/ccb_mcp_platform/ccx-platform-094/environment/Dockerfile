FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Base tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    ca-certificates \
    curl \
    python3 \
    golang-go \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

# Clone fixture repo (baseline has full local access)
RUN git clone --depth 1 https://github.com/sg-evals/grafana--v11.4.0.git /workspace/grafana

# Initialize git identity for agent commits
RUN git config --global user.email "agent@example.com" && \
    git config --global user.name "Agent" && \
    git config --global safe.directory '*'

# Create log directories
RUN mkdir -p /logs/agent /logs/verifier

ENTRYPOINT []
