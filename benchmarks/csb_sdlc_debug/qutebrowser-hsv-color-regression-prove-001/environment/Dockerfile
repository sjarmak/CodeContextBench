# Navprove Task Environment
# Source: qutebrowser/qutebrowser (6b320dc1)

FROM ghcr.io/sg-evals/sweap-images:qutebrowser.qutebrowser-qutebrowser__qutebrowser-6b320dc18662580e1313d2548fdd6231d2a97e6d-v363c8a7e5ccdf6968fc7ab84a2053ac780366
ENV TASK_WORKDIR=/workspace
ENV TASK_REPO_ROOT=/workspace

# Install uv for Python package management
RUN curl -LsSf https://astral.sh/uv/0.7.13/install.sh | sh || true

# Install test dependencies
RUN pip install pytest pytest-timeout || true

# Create required directories for Harbor
RUN mkdir -p /logs

# SWE-bench Pro images have the repository at /app
# Symlink /workspace -> /app so verifier PATCH_APPLY_DIR works
RUN rm -rf /workspace && ln -sf /app /workspace || true

WORKDIR /workspace

# Create non-root user for agent harness compatibility
RUN (adduser --disabled-password --gecos '' claude 2>/dev/null || true) && \
    for d in /workspace /app /testbed /logs; do [ -d "$d" ] && chown -R claude:claude "$d"; done || true

# Harness-agnostic: ensure all users (root/claude) can read+write workspace files
RUN chmod -R a+rwX /workspace

ENTRYPOINT []
