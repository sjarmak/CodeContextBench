FROM eclipse-temurin:17-jdk

WORKDIR /workspace

# Install dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    python3 \
    python3-pip \
    maven \
    && rm -rf /var/lib/apt/lists/*

# Clone Apache Flink at pinned commit (release-2.2.0)
RUN git clone --filter=blob:none --no-checkout https://github.com/apache/flink.git . && \
    git checkout 0cc95fcc145eddcfc87fc1b4ddf96ddd0f2ee15f && \
    git config user.email "agent@example.com" && \
    git config user.name "Agent"

