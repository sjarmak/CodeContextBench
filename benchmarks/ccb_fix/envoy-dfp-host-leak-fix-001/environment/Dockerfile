FROM ubuntu:22.04

WORKDIR /workspace

# Install dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git curl ca-certificates python3 && \
    rm -rf /var/lib/apt/lists/*

# Install Node.js for Claude Code CLI
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get install -y --no-install-recommends nodejs && \
    rm -rf /var/lib/apt/lists/*

# Create claude user before cloning (clone-as-claude pattern)
RUN adduser --disabled-password --gecos '' claude 2>/dev/null || true

# Clone envoy at pre-fix commit as claude user
USER claude
RUN git clone --depth 1 https://github.com/envoyproxy/envoy.git /workspace && \
    cd /workspace && \
    git fetch --depth 1 origin 5160151e14837c6f352b9d0b3a9f55119a9317e8 && \
    git checkout FETCH_HEAD
USER root

ENTRYPOINT []
