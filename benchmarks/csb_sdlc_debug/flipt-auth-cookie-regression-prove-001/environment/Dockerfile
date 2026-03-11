# Navprove Task Environment
# Source: flipt-io/flipt (6fe76d02)

FROM ghcr.io/sg-evals/sweap-images:flipt-io.flipt-flipt-io__flipt-6fe76d024ee0c50ddb09c86f4ae0bd4c208fd65f
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

ENTRYPOINT []
