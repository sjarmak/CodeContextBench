FROM ubuntu:22.04
ENV TASK_WORKDIR=/app
ENV TASK_REPO_ROOT=/app
ENV TASK_OUTPUT=/app/solution.json
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    git ca-certificates curl python3 python3-pip ripgrep && \
    rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir numpy
RUN adduser --disabled-password --gecos '' claude 2>/dev/null || true
RUN mkdir -p /app /logs/agent /logs/verifier && \
    chown -R claude:claude /app /logs
USER claude
WORKDIR /app
RUN git config --global user.email "agent@example.com" && \
    git config --global user.name "Agent" && \
    git config --global safe.directory '*'
RUN (git clone --depth 1 https://github.com/sg-evals/pandas--41968da5.git /app/repo || (mkdir -p /app/repo && cd /app/repo && git init && git config user.email "agent@example.com" && git config user.name "Agent")) && \
    mv /app/repo/* /app/repo/.* /app/ 2>/dev/null; \
    rm -rf /app/repo
USER root

RUN chmod -R a+rwX /app

ENTRYPOINT []
