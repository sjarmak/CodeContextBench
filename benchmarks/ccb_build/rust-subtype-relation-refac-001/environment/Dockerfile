FROM rust:1.82-bookworm

WORKDIR /workspace

# Install dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Clone Rust compiler at pinned commit (1.93.1)
RUN git clone --depth 1 https://github.com/sg-benchmarks/rust--01f6ddf7.git . && \
    git config user.email "agent@example.com" && \
    git config user.name "Agent"
