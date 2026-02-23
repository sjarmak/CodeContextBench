FROM ubuntu:22.04

# Install git and basic tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    ca-certificates \
    python3 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

# Clone Apache Kafka at a stable release tag (3.9.0 - latest stable as of Feb 2026)
RUN git clone --depth 1 https://github.com/sg-benchmarks/kafka--3.9.0.git . && \
    git config user.email "agent@benchmark.local" && \
    git config user.name "Agent"

# Create logs directory for agent output
RUN mkdir -p /logs/agent

CMD ["/bin/bash"]
