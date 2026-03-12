# Navprove Task Environment
# Source: gravitational/teleport (0415e422)

FROM ghcr.io/sg-evals/sweap-images:gravitational.teleport-gravitational__teleport-0415e422f12454db0c22316cf3eaa5088d6b6322
ENV TASK_WORKDIR=/workspace
ENV TASK_REPO_ROOT=/workspace

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
