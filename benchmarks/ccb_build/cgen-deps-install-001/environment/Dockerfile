FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update -qq && apt-get install -y -qq --no-install-recommends \
    python3 python3-pip git curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Python already installed above
# Copy repo
COPY repo /app/repo

WORKDIR /app/repo
