FROM golang:1.23-alpine AS base

# Install git, bash, and python3 (needed by verifier test.sh scoring)
RUN apk add --no-cache git bash python3

# Clone repos at pinned commits
WORKDIR /workspace

# Clone istio/istio
RUN git clone --depth 1 https://github.com/sg-benchmarks/istio--4c1f845d.git istio

# Clone envoyproxy/go-control-plane
RUN git clone --depth 1 https://github.com/sg-benchmarks/go-control-plane--71637ad6.git go-control-plane

# Clone envoyproxy/data-plane-api (protobuf definitions)
RUN git clone --depth 1 https://github.com/sg-benchmarks/data-plane-api--84e84367.git data-plane-api

# Verify repos exist
RUN ls -la /workspace/ && \
    test -d /workspace/istio && \
    test -d /workspace/go-control-plane && \
    test -d /workspace/data-plane-api

FROM base AS final
WORKDIR /workspace
CMD ["/bin/bash"]
