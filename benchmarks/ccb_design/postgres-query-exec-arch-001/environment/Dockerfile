FROM gcc:14-bookworm

WORKDIR /workspace

# Install dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    python3 \
    python3-pip \
    bison \
    flex \
    libreadline-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Clone PostgreSQL at pinned commit (REL_18_2)
RUN git clone --filter=blob:none --no-checkout https://github.com/postgres/postgres.git . && \
    git checkout 5a461dc4dbf72a1ec281394a76eb36d68cbdd935 && \
    git config user.email "agent@example.com" && \
    git config user.name "Agent"
