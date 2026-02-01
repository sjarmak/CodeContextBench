# SWE-bench Pro Benchmark

## Quick Start

```bash
# 1. Generate tasks (first 10 instances)
./scripts/generate_ccb_swebenchpro_tasks.sh 10

# 2. Run single task with baseline agent
harbor run \
  --path benchmarks/ccb_swebenchpro/tasks/instance_flipt-io__flipt-xxx \
  --agent-import-path agents.claude_baseline_agent:BaselineClaudeCodeAgent \
  --model anthropic/claude-haiku-4-5-20251001 \
  -n 1

# 3. Run comparison (baseline vs MCP)
./scripts/run_ccb_swebenchpro_comparison.sh benchmarks/ccb_swebenchpro/tasks
```

## Overview

SWE-bench Pro is a challenging benchmark for long-horizon software engineering tasks. Unlike standard SWE-bench (Python only), it includes:

- **Go** projects (flipt-io/flipt, future-architect/vuls)
- **TypeScript** projects (tutao/tutanota, protonmail/webclients)  
- **Python** projects (internetarchive/openlibrary)

## MCP Integration

Tasks are generated with Sourcegraph MCP support. Set these environment variables:

```bash
export SOURCEGRAPH_ACCESS_TOKEN="your-token"
export SOURCEGRAPH_URL="https://sourcegraph.com"
```

## Agent Options

| Agent | Import Path | Description |
|-------|-------------|-------------|
| Baseline | `agents.claude_baseline_agent:BaselineClaudeCodeAgent` | No MCP |
| Strategic | `agents.mcp_variants:StrategicDeepSearchAgent` | MCP with targeted Deep Search |
| SWE-agent | `agents.swe_agent_wrapper:SWEAgentMCPAgent` | SWE-agent with MCP |
| SWE-agent Baseline | `agents.swe_agent_wrapper:SWEAgentBaselineAgent` | SWE-agent without MCP |

## Files

- `adapter.py` - Converts HuggingFace dataset to Harbor format
- `run_adapter.py` - CLI for task generation  
- `ccb_swebenchpro.yaml` - Harbor job configuration
- `template/` - Task templates
