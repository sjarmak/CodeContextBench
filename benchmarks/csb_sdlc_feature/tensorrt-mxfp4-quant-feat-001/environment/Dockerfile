FROM python:3.11-bookworm

WORKDIR /workspace

# Install dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    build-essential \
    cmake \
    ninja-build \
    && rm -rf /var/lib/apt/lists/*

# Create claude user and writable work dirs before clone.
RUN (adduser --disabled-password --gecos '' claude 2>/dev/null || true) && \
    mkdir -p /workspace /logs && \
    chown -R claude:claude /workspace /logs

# Clone the actual TensorRT-LLM repository at pinned commit
# This ensures BOTH baseline and MCP agents have identical file access
USER claude
RUN (git clone --depth 1 https://github.com/sg-evals/TensorRT-LLM--b98f3fca.git . || (git init && git config user.email "agent@example.com" && git config user.name "Agent")) && \
    git config user.email "agent@example.com" && \
    git config user.name "Agent"
USER root

# Install Python dependencies (basic setup only)
# Full build may require CUDA and other deps, but we need the source files
RUN pip install --upgrade pip && \
    pip install pybind11==2.13.6 2>&1 || true


ENTRYPOINT []
