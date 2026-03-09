# Navprove Task Environment
# Source: gravitational/teleport (0415e422)

FROM jefzda/sweap-images:gravitational.teleport-gravitational__teleport-0415e422f12454db0c22316cf3eaa5088d6b6322
ENV TASK_WORKDIR=/workspace
ENV TASK_REPO_ROOT=/workspace

# Create required directories for Harbor
RUN mkdir -p /logs

# SWE-bench Pro images have the repository at /app
# Symlink /workspace -> /app so verifier PATCH_APPLY_DIR works
RUN rm -rf /workspace && ln -sf /app /workspace || true

WORKDIR /workspace

ENTRYPOINT []
