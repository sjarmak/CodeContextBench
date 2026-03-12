# SWE-bench Pro Task Environment
# Repo: element-hq/element-web

FROM ghcr.io/sg-evals/sweap-images:element-hq.element-element-hq__element-web-dae13ac8522fc6d41e64d1ac6e3174486fdcce0c
ENV TASK_WORKDIR=/workspace
ENV TASK_REPO_ROOT=/workspace

# Install uv for Python package management
RUN curl -LsSf https://astral.sh/uv/0.7.13/install.sh 2>/dev/null | sh || true

# Create required directories for Harbor
RUN mkdir -p /logs && rm -rf /workspace && ln -sf /app /workspace || true

# SWE-bench Pro images have the repository at /app, not /testbed
WORKDIR /workspace

# Override the default entrypoint to work with Harbor's docker-compose

# Create non-root user for agent harness compatibility
RUN (adduser --disabled-password --gecos '' claude 2>/dev/null || true) && \
    for d in /workspace /app /testbed /logs; do [ -d "$d" ] && chown -R claude:claude "$d"; done || true

# Harness-agnostic: ensure all users (root/claude) can read+write workspace files
RUN chmod -R a+rwX /workspace

ENTRYPOINT []
