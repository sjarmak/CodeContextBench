FROM debian:bookworm-slim

WORKDIR /workspace

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    python3 \
    build-essential \
    jq \
    bc \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN git init && \
    git remote add origin https://github.com/curl/curl.git && \
    git fetch --depth 1 origin 09e25b9d94f4106eac8ca3a43b221bdc66f405e4 && \
    git checkout FETCH_HEAD && \
    git config user.email "agent@example.com" && \
    git config user.name "Agent"
