FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Install git and dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends git ca-certificates python3 && \
    rm -rf /var/lib/apt/lists/*

# Clone Cilium at pinned commit (v1.17.9)
RUN git clone --depth 1 https://github.com/sg-evals/cilium--a2f97aa8.git /workspace/cilium

WORKDIR /workspace/cilium
