# SWE-bench Pro Task Environment
# Instance: instance_NodeBB__NodeBB-76c6e30282906ac664f2c9278fc90999b27b1f48-vd59a5728dfc977f44533186ace531248c2917516
# Repo: NodeBB/NodeBB

FROM ghcr.io/sg-evals/sweap-images:nodebb.nodebb-NodeBB__NodeBB-76c6e30282906ac664f2c9278fc90999b27b1f48-vd59a5728dfc977f44533186ace531248c2917516
ENV TASK_WORKDIR=/workspace
ENV TASK_REPO_ROOT=/workspace

# Install uv for Python package management
RUN curl -LsSf https://astral.sh/uv/0.7.13/install.sh | sh || true

# Create required directories for Harbor
RUN mkdir -p /logs && rm -rf /workspace && ln -sf /app /workspace || true

# SWE-bench Pro images have the repository at /app, not /testbed
WORKDIR /workspace

# Override the default entrypoint to work with Harbor's docker-compose
# (The base image has ENTRYPOINT ["/bin/bash"] which doesn't work with Harbor's command format)

# Create non-root user for agent harness compatibility
RUN (adduser --disabled-password --gecos '' claude 2>/dev/null || true) && \
    for d in /workspace /app /testbed /logs; do [ -d "$d" ] && chown -R claude:claude "$d"; done || true

ENTRYPOINT []
