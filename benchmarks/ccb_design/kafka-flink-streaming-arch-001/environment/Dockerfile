FROM eclipse-temurin:17-jdk

WORKDIR /workspace

# Install dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Clone Apache Kafka at pinned tag (4.1.1) into /workspace/kafka/
RUN git clone --depth 1 https://github.com/sg-benchmarks/kafka--0753c489.git /workspace/kafka && \
    git config user.email "agent@example.com" && \
    git config user.name "Agent"

# Clone Apache Flink at pinned branch (release-2.2.0) into /workspace/flink/
RUN git clone --depth 1 https://github.com/sg-benchmarks/flink--0cc95fcc.git /workspace/flink && \
    git config user.email "agent@example.com" && \
    git config user.name "Agent"

