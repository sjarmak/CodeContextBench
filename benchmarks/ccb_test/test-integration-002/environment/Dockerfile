FROM golang:1.22-bookworm

WORKDIR /workspace

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    python3 \
    ripgrep \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

RUN git clone --filter=blob:none --no-checkout https://github.com/navidrome/navidrome.git . && \
    git checkout 9c3b4561652a15846993d477003e111f0df0c585 && \
    git config user.email "agent@example.com" && \
    git config user.name "Agent"

RUN mkdir -p /workspace/scanner /workspace/testdata /app
