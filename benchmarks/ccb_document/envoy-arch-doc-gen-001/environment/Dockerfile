FROM ubuntu:22.04

WORKDIR /workspace

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    python3 \
    ripgrep \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN git init && \
    git remote add origin https://github.com/envoyproxy/envoy.git && \
    git fetch --depth 1 origin 1d0ba73ad200d28e86c0c23f76c55320f82a8fba && \
    git checkout FETCH_HEAD && \
    git config user.email "agent@example.com" && \
    git config user.name "Agent"
