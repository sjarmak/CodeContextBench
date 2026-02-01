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
COPY 10Figure-Codebases /ccb_crossrepo

# Install Python dependencies
WORKDIR /ccb_crossrepo
RUN pip3 install --no-cache-dir -r requirements.txt

# Corpus is already built externally - just verify structure
RUN test -d /ccb_crossrepo/src/kubernetes && \
    test -d /ccb_crossrepo/src/envoy && \
    test -d /ccb_crossrepo/src/django && \
    test -d /ccb_crossrepo/src/tensorflow && \
    test -d /ccb_crossrepo/tasks && \
    test -f /ccb_crossrepo/scripts/validate_patch.py && \
    echo "✓ Corpus structure validated (tasks: $(ls /ccb_crossrepo/tasks/*.yaml 2>/dev/null | wc -l) files)"

# Create workspace directory
RUN mkdir -p /workspace

# Set working directory
WORKDIR /workspace

# Expose corpus path as env var
ENV CORPUS_ROOT=/ccb_crossrepo/src
ENV VALIDATOR_PATH=/ccb_crossrepo/scripts/validate_patch.py

# Default command
CMD ["/bin/bash"]
