FROM ubuntu:22.04

# Prevent interactive prompts
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update -qq && apt-get install -y -qq \
    git \
    curl \
    ca-certificates \
    build-essential \
    python3 \
    python3-pip \
    make \
    jq \
    && rm -rf /var/lib/apt/lists/*

# Copy 10Figure-Codebases repository
COPY 10Figure-Codebases /10figure

# Install Python dependencies
WORKDIR /10figure
RUN pip3 install --no-cache-dir -r requirements.txt

# Corpus is already built externally - just verify structure
RUN test -d /10figure/src/kubernetes && \
    test -d /10figure/src/envoy && \
    test -d /10figure/src/django && \
    test -d /10figure/src/tensorflow && \
    test -d /10figure/tasks && \
    test -f /10figure/scripts/validate_patch.py && \
    echo "✓ Corpus structure validated (tasks: $(ls /10figure/tasks/*.yaml 2>/dev/null | wc -l) files)"

# Create workspace directory
RUN mkdir -p /workspace

# Set working directory
WORKDIR /workspace

# Expose corpus path as env var
ENV CORPUS_ROOT=/10figure/src
ENV VALIDATOR_PATH=/10figure/scripts/validate_patch.py

# Default command
CMD ["/bin/bash"]
