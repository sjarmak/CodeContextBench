# SWE-bench Pro Task Environment
# Instance: {instance_id}
# Repo: {repo}

FROM {docker_image}

# Install uv for Python package management (if needed)
RUN curl -LsSf https://astral.sh/uv/0.7.13/install.sh | sh || true

# Create required directories
RUN mkdir -p /logs /workspace

WORKDIR /app

# Note: test files (config.json, test.sh) are NOT copied here.
# Harbor uploads them to /tests at verification time via docker compose cp.
