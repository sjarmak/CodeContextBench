FROM ubuntu:22.04

# Install dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    build-essential \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Install Go 1.21 (Prometheus 2.x requires Go 1.20+)
RUN wget https://go.dev/dl/go1.21.0.linux-amd64.tar.gz && \
    tar -C /usr/local -xzf go1.21.0.linux-amd64.tar.gz && \
    rm go1.21.0.linux-amd64.tar.gz

ENV PATH="/usr/local/go/bin:${PATH}"
ENV GOPATH="/go"
ENV PATH="${GOPATH}/bin:${PATH}"

# Clone Prometheus repository and checkout the regressing commit
# Commit 52630ad introduced the head posting optimization that caused 3-5x slowdown
# This is the commit AFTER the regression was introduced, allowing investigation
WORKDIR /workspace
RUN git clone --filter=blob:none --no-checkout https://github.com/prometheus/prometheus.git && \
    cd prometheus && \
    git checkout 52630ad0c735f2dce4ce5bb851acb6c5d7df5eb1

WORKDIR /workspace/prometheus

# Create logs directory for investigation output
RUN mkdir -p /logs/agent

# Set up git for better commit analysis
RUN git config --global core.pager cat
