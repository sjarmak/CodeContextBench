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

# Clone terraform at pre-fix commit as claude user
USER claude
RUN git clone --depth 1 https://github.com/hashicorp/terraform.git /workspace && \
    cd /workspace && \
    git fetch --depth 1 origin abd6b9ef1ba5e98ed273f59f667d3b9f2077a87b && \
    git checkout FETCH_HEAD
USER root

ENTRYPOINT []
