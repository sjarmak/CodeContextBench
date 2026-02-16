FROM golang:1.23-alpine AS base

# Install git for cloning
RUN apk add --no-cache git bash

# Clone repos at pinned commits
WORKDIR /workspace

# Clone istio/istio
RUN git clone https://github.com/istio/istio.git istio && \
    cd istio && \
    git checkout 1.24.1

# Clone envoyproxy/go-control-plane
RUN git clone https://github.com/envoyproxy/go-control-plane.git go-control-plane && \
    cd go-control-plane && \
    git checkout v0.13.3

# Clone envoyproxy/data-plane-api (protobuf definitions)
RUN git clone https://github.com/envoyproxy/data-plane-api.git data-plane-api && \
    cd data-plane-api && \
    git checkout v3.36.0

# Verify repos exist
RUN ls -la /workspace/ && \
    test -d /workspace/istio && \
    test -d /workspace/go-control-plane && \
    test -d /workspace/data-plane-api

FROM base AS final
WORKDIR /workspace
CMD ["/bin/bash"]
