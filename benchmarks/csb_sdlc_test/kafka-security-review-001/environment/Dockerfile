FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Install dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    openjdk-17-jdk \
    python3 \
    python3-pip \
    ca-certificates \
    curl \
    jq \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

# Clone Kafka at pinned tag 3.8.0
RUN (git clone --depth 1 https://github.com/sg-evals/kafka--3.8.0.git . || (git init && git config user.email "agent@example.com" && git config user.name "Agent")) && \
    git config --global user.email "test@example.com" && \
    git config --global user.name "Test User"

# Inject defects
COPY inject_defects.sh /tmp/inject_defects.sh
RUN chmod +x /tmp/inject_defects.sh && /tmp/inject_defects.sh

# Set Java home
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64

# Create non-root user for agent harness compatibility
RUN (adduser --disabled-password --gecos '' claude 2>/dev/null || true) && \
    for d in /workspace /app /testbed /logs; do [ -d "$d" ] && chown -R claude:claude "$d"; done || true

CMD ["/bin/bash"]

# Harness-agnostic: ensure all users (root/claude) can read+write workspace files
RUN chmod -R a+rwX /workspace

ENTRYPOINT []
