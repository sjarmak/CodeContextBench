# Pre-built base image contains gcc:13, tools, Claude Code CLI, and the
# Linux kernel source at v4.14.114.  Build it first if missing:
#   ./benchmarks/ccb_linuxflbench/base_images/build_base_images.sh v4.14.114
# See benchmarks/ccb_linuxflbench/README.md for details.
FROM ccb-linux-base:v4.14.114

# Copy task-specific test files (thin layer — rebuilds are fast)
COPY tests/ /workspace/tests/
RUN chmod +x /workspace/tests/test.sh
