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

# Clone local checkout repos (baseline config: agent has local access to these)
RUN git clone --depth 1 https://github.com/sg-benchmarks/kubernetes--v1.32.0 /workspace/kubernetes
RUN git clone --depth 1 https://github.com/sg-benchmarks/client-go--v0.32.0 /workspace/client-go
RUN git clone --depth 1 https://github.com/sg-benchmarks/api--v0.32.0 /workspace/api
RUN git clone --depth 1 https://github.com/sg-benchmarks/etcd-io-etcd /workspace/etcd

# Initialize git identity for agent commits
RUN git config --global user.email "agent@example.com" && \
    git config --global user.name "Agent" && \
    git config --global safe.directory '*'

# Create log directories
RUN mkdir -p /logs/agent /logs/verifier

ENTRYPOINT []
