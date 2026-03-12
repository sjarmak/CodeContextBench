FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update -qq && apt-get install -y -qq --no-install-recommends \
    git \
    curl \
    ca-certificates \
    python3 \
    python3-pip \
    jq \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

# Clone envoyproxy/go-control-plane at xdsmatcher/v0.14.0
RUN git clone --depth 1 https://github.com/sg-evals/go-control-plane--71637ad6.git go-control-plane || \
    (mkdir -p go-control-plane && cd go-control-plane && git init && git config user.email "agent@example.com" && git config user.name "Agent")

# Clone istio/istio at 1.29.0
RUN git clone --depth 1 https://github.com/sg-evals/istio--2300e245.git istio || \
    (mkdir -p istio && cd istio && git init && git config user.email "agent@example.com" && git config user.name "Agent")

# Clone emissary-ingress/emissary at v4.0.0-rc.1
RUN git clone --depth 1 https://github.com/sg-evals/emissary--3bbdbe0f.git emissary || \
    (mkdir -p emissary && cd emissary && git init && git config user.email "agent@example.com" && git config user.name "Agent")

RUN mkdir -p /logs/verifier /logs/agent

# Create non-root user for agent harness compatibility
RUN (adduser --disabled-password --gecos '' claude 2>/dev/null || true) && \
    for d in /workspace /app /testbed /logs; do [ -d "$d" ] && chown -R claude:claude "$d"; done || true

CMD ["/bin/bash"]

# Harness-agnostic: ensure all users (root/claude) can read+write workspace files
RUN chmod -R a+rwX /workspace

ENTRYPOINT []
