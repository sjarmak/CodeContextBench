FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    python3 python3-pip \
    git curl \
    && rm -rf /var/lib/apt/lists/*

# Clone repository at specific commit
RUN git clone https://github.com/helix-editor/helix.git /app/repo && \
    cd /app/repo && \
    git checkout e69292e5eb7b0f727fefa19cffec910718af31b3

# Install Python dependencies for verification (if needed)
RUN pip install --no-cache-dir -q \
    tree-sitter==0.20.1 \
    python-dotenv

WORKDIR /app
