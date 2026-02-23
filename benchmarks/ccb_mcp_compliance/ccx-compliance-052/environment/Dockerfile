FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Base tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    ca-certificates \
    curl \
    python3 \
    g++ make \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

# Clone local checkout repos (baseline config: agent has local access to these)
RUN git clone --depth 1 --branch v1.31.2 https://github.com/sg-benchmarks/envoy--v1.31.2 /workspace/envoy--v1.31.2
RUN git clone --depth 1 --branch 84e84367 https://github.com/sg-benchmarks/data-plane-api--84e84367 /workspace/data-plane-api--84e84367
RUN git clone --depth 1 --branch 71637ad6 https://github.com/sg-benchmarks/go-control-plane--71637ad6 /workspace/go-control-plane--71637ad6
RUN git clone --depth 1 --branch 957dba5e https://github.com/sg-benchmarks/grpc--957dba5e /workspace/grpc--957dba5e

# Initialize git identity for agent commits
RUN git config --global user.email "agent@example.com" && \
    git config --global user.name "Agent" && \
    git config --global safe.directory '*'

# Create log directories
RUN mkdir -p /logs/agent /logs/verifier

ENTRYPOINT []
