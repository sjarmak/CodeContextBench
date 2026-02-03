FROM python:3.10-slim

WORKDIR /workspace

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    wget \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies for evaluation
RUN pip install --no-cache-dir \
    networkx \
    pygments

# Set up output directory
RUN mkdir -p /logs/verifier

# Set default command
CMD ["/bin/bash"]
