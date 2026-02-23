FROM python:3.12-bookworm

WORKDIR /workspace

# Install dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Clone Django at pinned commit (5.2)
RUN git clone --depth 1 https://github.com/sg-evals/django--6b995cff.git . && \
    git config user.email "agent@example.com" && \
    git config user.name "Agent"
