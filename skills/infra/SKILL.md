---
name: infra
description: Check infrastructure readiness, manage MCP tools, and audit system dependencies.
---

# Skill: Infrastructure & Operations

## Scope

Use this skill when the user asks to:
- Check infrastructure readiness before runs
- Verify account quotas and rate limits
- Audit MCP (Model Context Protocol) tool availability
- Debug connectivity and credential issues
- Manage Docker images and build environments

## Canonical Commands

```bash
# Check overall infra readiness
python3 scripts/infra/check_infra.py

# Account health and rate limits
python3 scripts/infra/account_health.py status

# Check rate limit observations
python3 scripts/infra/account_health.py observations

# MCP audit (tool availability)
python3 scripts/infra/mcp_audit.py --json

# Build and push base images
./scripts/infra/build_linux_base_images.sh

# Check Daytona readiness
python3 scripts/infra/check_infra.py --daytona
```

## Infrastructure Checks

- **Tokens** — API keys valid, not expired
- **Docker** — daemon running, images available
- **Disk** — sufficient space in /tmp and working directories
- **Harbor CLI** — installed and authenticated
- **Network** — connectivity to external services
- **Quotas** — account concurrency limits and rate limits

## Account Readiness

- **OAuth tokens** — refresh if expired (older than 7 days)
- **Rate limits** — check recent observations for throttling
- **Concurrency** — each account has safe parallel slot capacity
- **Unsafe accounts** — automatically excluded from runs if flagged

## MCP Availability

- **Sourcegraph** — configured and accessible
- **DeepSearch** — credential validation
- **Tool coverage** — which tools are available per model
- **Fallback routing** — when MCP is unavailable

## Related Skills

- `/run` — uses infra checks before launch
- `/audit` — validates infrastructure compliance
