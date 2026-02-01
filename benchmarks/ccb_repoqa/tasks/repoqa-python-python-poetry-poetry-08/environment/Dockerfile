FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    python3 python3-pip \
    git curl \
    && rm -rf /var/lib/apt/lists/*

# Clone repository at specific commit
RUN git clone https://github.com/python-poetry/poetry.git /app/repo && \
    cd /app/repo && \
    git checkout 21ffd99274d299bd6d2b7b0cdd7ba273fdd941be

# Install Python dependencies for verification (if needed)
RUN pip install --no-cache-dir -q \
    tree-sitter==0.20.1 \
    python-dotenv

WORKDIR /app
