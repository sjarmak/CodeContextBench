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

# Clone kubernetes/api (same pinned SHA as crossrepo-chain-001)
RUN git clone --depth 1 https://github.com/sg-evals/api--f32ed1d6.git api

# Clone kubernetes/apimachinery (same pinned SHA as crossrepo-chain-001)
RUN git clone --depth 1 https://github.com/sg-evals/apimachinery--b2e9f88f.git apimachinery

RUN mkdir -p /logs/verifier /logs/agent

CMD ["/bin/bash"]
