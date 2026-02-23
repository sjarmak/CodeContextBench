FROM eclipse-temurin:17-jdk

WORKDIR /workspace

# Install dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    python3 \
    && rm -rf /var/lib/apt/lists/*

# Clone Apache Kafka at pinned commit (4.1.1)
RUN git clone --depth 1 https://github.com/sg-evals/kafka--be816b82.git . && \
    git config user.email "agent@example.com" && \
    git config user.name "Agent"
