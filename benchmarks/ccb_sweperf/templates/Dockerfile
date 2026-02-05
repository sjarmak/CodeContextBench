FROM python:3.12-bookworm

# Install system dependencies (including build tools for C/Cython extensions)
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    curl \
    gfortran \
    git \
    jq \
    libopenblas-dev \
    liblapack-dev \
    pkg-config \
    time \
    && rm -rf /var/lib/apt/lists/*

# Install uv package manager for fast installs
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

# Create working directories
RUN mkdir -p /workspace/original /workspace/optimized /workspace/tests /logs /benchmark

# Install benchmarking and profiling tools
RUN pip install --no-cache-dir \
    pytest \
    pytest-benchmark \
    pyperf \
    memory_profiler \
    line_profiler \
    cython \
    numpy

# ============================================
# IMPORTANT: Task-specific Dockerfiles must add:
# 1. git clone of the target repo at a pinned commit
# 2. cp -a to /workspace/original/ and /workspace/optimized/
# 3. pip install --no-cache-dir . to build from source (NOT editable install)
# 4. Copy relevant test suite to /workspace/tests/
# ============================================

WORKDIR /workspace

# Set up benchmark environment
ENV BENCHMARK_ITERATIONS=10
ENV BENCHMARK_WARMUP=3

CMD ["/bin/bash"]
