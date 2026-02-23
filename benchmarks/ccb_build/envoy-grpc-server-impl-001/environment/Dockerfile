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
RUN git clone --depth 1 https://github.com/sg-benchmarks/go-control-plane--71637ad6.git go-control-plane

# Clone istio/istio at 1.29.0
RUN git clone --depth 1 https://github.com/sg-benchmarks/istio--2300e245.git istio

# Clone emissary-ingress/emissary at v4.0.0-rc.1
RUN git clone --depth 1 https://github.com/sg-benchmarks/emissary--3bbdbe0f.git emissary

RUN mkdir -p /logs/verifier /logs/agent

CMD ["/bin/bash"]
