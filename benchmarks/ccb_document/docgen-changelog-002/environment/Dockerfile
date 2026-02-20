FROM golang:1.22-bookworm

WORKDIR /workspace

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    python3 \
    ripgrep \
    && rm -rf /var/lib/apt/lists/*

RUN git clone --filter=blob:none --no-checkout https://github.com/flipt-io/flipt.git . && \
    git checkout 3d5a345f94c2adc8a0eaa102c189c08ad4c0f8e8 && \
    git config user.email "agent@example.com" && \
    git config user.name "Agent"

RUN mkdir -p /app
