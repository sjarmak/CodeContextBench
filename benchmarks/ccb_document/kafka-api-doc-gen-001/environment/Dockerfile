FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ca-certificates \
        git \
        openjdk-21-jdk-headless \
        python3 \
        vim \
        && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /repo

# Clone Apache Kafka at specific commit (e678b4b, trunk 2026-02-16)
# Use blobless clone + sparse-checkout for speed
RUN git clone --depth 1 https://github.com/sg-evals/kafka--e678b4b.git .

WORKDIR /workspace
