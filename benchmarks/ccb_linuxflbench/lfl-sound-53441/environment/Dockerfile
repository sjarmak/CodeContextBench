# Pre-built base image contains gcc:13, tools, Claude Code CLI, and the
# Linux kernel source at v3.7.6.  Build it first if missing:
#   ./benchmarks/ccb_linuxflbench/base_images/build_base_images.sh v3.7.6
# See benchmarks/ccb_linuxflbench/README.md for details.
FROM ccb-linux-base:v3.7.6

# Copy task-specific test files (thin layer — rebuilds are fast)
COPY tests/ /workspace/tests/
RUN chmod +x /workspace/tests/test.sh
