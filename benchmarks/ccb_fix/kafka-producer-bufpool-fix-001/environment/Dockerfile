FROM eclipse-temurin:17-jdk

WORKDIR /workspace

# Install dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    python3 \
    && rm -rf /var/lib/apt/lists/*

# Clone Apache Kafka at pinned commit (4.1.1)
RUN git clone --filter=blob:none --no-checkout https://github.com/apache/kafka.git . && \
    git checkout be816b82d25370ceac697ccf7c88cea873e9b4e3 && \
    git config user.email "agent@example.com" && \
    git config user.name "Agent"
