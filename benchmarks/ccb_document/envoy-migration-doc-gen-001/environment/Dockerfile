FROM ubuntu:22.04

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    python3 \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

# Clone Envoy at v1.30 and v1.31 tags
RUN git clone --depth 1 https://github.com/sg-evals/envoy--50ea83e6.git envoy-v1.30
RUN git clone --depth 1 https://github.com/sg-evals/envoy--7b8baff1.git envoy-v1.31

WORKDIR /workspace
