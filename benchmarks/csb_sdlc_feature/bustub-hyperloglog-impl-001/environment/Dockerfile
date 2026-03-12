# TAC Task Wrapper: sde-implement-hyperloglog
FROM ghcr.io/theagentcompany/sde-implement-hyperloglog-image:1.0.0

# Create logs directory for Harbor compatibility
RUN mkdir -p /logs /workspace

# Set working directory
WORKDIR /workspace

# Environment variables
ENV TAC_SERVER_HOSTNAME=localhost
ENV DECRYPTION_KEY="theagentcompany is all you need"

# Create non-root user for agent harness compatibility
RUN (adduser --disabled-password --gecos '' claude 2>/dev/null || true) && \
    for d in /workspace /app /testbed /logs; do [ -d "$d" ] && chown -R claude:claude "$d"; done || true

CMD ["bash"]

# Harness-agnostic: ensure all users (root/claude) can read+write workspace files
RUN chmod -R a+rwX /workspace

ENTRYPOINT []
