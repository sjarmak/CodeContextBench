FROM golang:1.23-alpine AS base

# Install git for cloning
RUN apk add --no-cache git bash

# Clone repos at pinned commits
WORKDIR /workspace

# Clone kubernetes/kubernetes
RUN git clone https://github.com/kubernetes/kubernetes.git kubernetes && \
    cd kubernetes && \
    git checkout 31bf3ed00ec0abe1b64d662d2e07e23e08f7cce0

# Clone kubernetes/api (synced from k/k staging)
RUN git clone https://github.com/kubernetes/api.git api && \
    cd api && \
    git checkout 40341bbc11e31a8e5926cffe1c7a84d28a9ca5cb

# Clone kubernetes/apimachinery
RUN git clone https://github.com/kubernetes/apimachinery.git apimachinery && \
    cd apimachinery && \
    git checkout 4b5c7c1a95ffb9c8c70ea8098b7a03e9d1d6c8e0

# Verify repos exist
RUN ls -la /workspace/ && \
    test -d /workspace/kubernetes && \
    test -d /workspace/api && \
    test -d /workspace/apimachinery

FROM base AS final
WORKDIR /workspace
CMD ["/bin/bash"]
