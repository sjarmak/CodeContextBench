# Navprove Task Environment
# Source: future-architect/vuls (139f3a81)

FROM jefzda/sweap-images:future-architect.vuls-future-architect__vuls-139f3a81b66c47e6d8f70ce6c4afe7a9196a6ea8
ENV TASK_WORKDIR=/workspace
ENV TASK_REPO_ROOT=/workspace

# Create required directories for Harbor
RUN mkdir -p /logs

# SWE-bench Pro images have the repository at /app
# Symlink /workspace -> /app so verifier PATCH_APPLY_DIR works
RUN rm -rf /workspace && ln -sf /app /workspace || true

WORKDIR /workspace

ENTRYPOINT []
