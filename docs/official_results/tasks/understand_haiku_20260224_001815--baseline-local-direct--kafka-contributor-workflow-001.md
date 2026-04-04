# kafka-contributor-workflow-001 (baseline-local-direct)

- Run: `understand_haiku_20260224_001815`
- Status: `passed`
- Reward: `0.9500`
- Audit JSON: [link](../audits/understand_haiku_20260224_001815--baseline-local-direct--kafka-contributor-workflow-001.json)
- Trajectory available: `True`
- Transcript available: `True`
- Bundled trajectory: [link](../traces/understand_haiku_20260224_001815--baseline-local-direct--kafka-contributor-workflow-001/trajectory.json)
- Bundled transcript: [link](../traces/understand_haiku_20260224_001815--baseline-local-direct--kafka-contributor-workflow-001/claude-code.txt)

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 491.1 |
| Agent execution seconds | 212.1 |
| Input tokens | 1,207,196 |
| Output tokens | 90 |
| Cache tokens | 1,205,391 |
| Tool calls (total) | 23 |
| Tool calls (MCP) | 0 |
| Tool calls (local) | 23 |
| MCP ratio | 0.000 |
| keyword_search calls | - |
| nls_search calls | - |
| deepsearch calls | - |
| `result.json` SHA256 | `b6785fd7744a95e56701c9e25ea5870b44eabca6689a5f34b13166eacd0f296e` |
| `trajectory.json` SHA256 | `3e05fe7fa1fc639c24d1f6b1c82fa524740bd0b386f169dd932007c1d7cd17f8` |
| transcript SHA256 | `1c4bfd54f02750db6cfb33589244fe04dba82c62b1b193aebac6560a8931820b` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `Bash` | 10 |
| `Read` | 9 |
| `WebFetch` | 2 |
| `Glob` | 1 |
| `Write` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `Bash` |
| `Glob` |
| `Read` |
| `Read` |
| `Read` |
| `Bash` |
| `Bash` |
| `Bash` |
| `Bash` |
| `Read` |
| `Read` |
| `Read` |

## Conversation Preview

Parsed from transcript using the same message categories as the dashboard trace parser.

| Seq | Type | Subtype | Tool | Text |
|---:|---|---|---|---|
| 1 | `system` | `init` | `-` | - |
| 2 | `assistant` | `text` | `-` | I'll help you discover the Apache Kafka contributor workflow by exploring the repository and documenting the key information. Let me start by examining the codebase structure and finding relevant documentation. |
| 3 | `assistant` | `tool_use` | `Bash` | - |
| 4 | `assistant` | `tool_use` | `Glob` | - |
| 5 | `user` | `text` | `-` | - |
| 6 | `user` | `text` | `-` | - |
| 7 | `assistant` | `tool_use` | `Read` | - |
| 8 | `user` | `text` | `-` | - |
| 9 | `assistant` | `tool_use` | `Read` | - |
| 10 | `user` | `text` | `-` | - |
| 11 | `assistant` | `tool_use` | `Read` | - |
| 12 | `user` | `text` | `-` | - |
| 13 | `assistant` | `tool_use` | `Bash` | - |
| 14 | `user` | `text` | `-` | - |
| 15 | `assistant` | `tool_use` | `Bash` | - |
| 16 | `user` | `text` | `-` | - |
| 17 | `assistant` | `tool_use` | `Bash` | - |
| 18 | `user` | `text` | `-` | - |
| 19 | `assistant` | `tool_use` | `Bash` | - |
| 20 | `user` | `text` | `-` | - |
| 21 | `assistant` | `tool_use` | `Read` | - |
| 22 | `user` | `text` | `-` | - |
| 23 | `assistant` | `tool_use` | `Read` | - |
| 24 | `user` | `text` | `-` | - |
| 25 | `assistant` | `tool_use` | `Read` | - |
| 26 | `user` | `text` | `-` | - |
| 27 | `assistant` | `tool_use` | `Read` | - |
| 28 | `user` | `text` | `-` | - |
| 29 | `assistant` | `tool_use` | `Bash` | - |
| 30 | `user` | `text` | `-` | - |
| 31 | `assistant` | `tool_use` | `Bash` | - |
| 32 | `user` | `text` | `-` | - |
| 33 | `assistant` | `tool_use` | `Read` | - |
| 34 | `user` | `text` | `-` | - |
| 35 | `assistant` | `tool_use` | `WebFetch` | - |
| 36 | `assistant` | `tool_use` | `Bash` | - |
| 37 | `user` | `text` | `-` | - |
| 38 | `user` | `text` | `-` | - |
| 39 | `assistant` | `tool_use` | `WebFetch` | - |
| 40 | `assistant` | `tool_use` | `Bash` | - |
| 41 | `user` | `text` | `-` | - |
| 42 | `user` | `text` | `-` | - |
| 43 | `assistant` | `tool_use` | `Read` | - |
| 44 | `user` | `text` | `-` | - |
| 45 | `assistant` | `tool_use` | `Bash` | - |
| 46 | `user` | `text` | `-` | - |
| 47 | `assistant` | `text` | `-` | Now let me create the comprehensive contributor guide based on all the information I've gathered: |
| 48 | `assistant` | `tool_use` | `Write` | - |
| 49 | `user` | `text` | `-` | - |
| 50 | `assistant` | `text` | `-` | Perfect! I've created a comprehensive **Apache Kafka Contributor Guide** at `/logs/agent/onboarding.md`. Here's what I've documented:  ## Summary  ### 1. **Build Prerequisites** - Java 8, 11, 17, or 21 support with speci... |
