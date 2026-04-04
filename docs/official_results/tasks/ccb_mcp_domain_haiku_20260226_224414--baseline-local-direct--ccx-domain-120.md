# ccx-domain-120 (baseline-local-direct)

- Run: `csb_org_domain_haiku_20260226_224414`
- Status: `passed`
- Reward: `0.8000`
- Audit JSON: [link](../audits/csb_org_domain_haiku_20260226_224414--baseline-local-direct--ccx-domain-120.json)
- Trajectory available: `True`
- Transcript available: `True`
- Bundled trajectory: [link](../traces/csb_org_domain_haiku_20260226_224414--baseline-local-direct--ccx-domain-120/trajectory.json)
- Bundled transcript: [link](../traces/csb_org_domain_haiku_20260226_224414--baseline-local-direct--ccx-domain-120/claude-code.txt)

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 129.0 |
| Agent execution seconds | 83.8 |
| Input tokens | 1,708,228 |
| Output tokens | 10,432 |
| Cache tokens | 1,707,555 |
| Tool calls (total) | 31 |
| Tool calls (MCP) | 0 |
| Tool calls (local) | 31 |
| MCP ratio | 0.000 |
| keyword_search calls | - |
| nls_search calls | - |
| deepsearch calls | - |
| `result.json` SHA256 | `f682ee3040ef8caf51782220119e46f11e58dc8c8e90eee2f8d887e5d1682b62` |
| `trajectory.json` SHA256 | `536c2a40f3362d9272406c5fdb282f45bd80ead0b589c68f1af1fb5c740203c6` |
| transcript SHA256 | `aa81a7e67561450b81479444d7a60b7e04f8c85420909f3e515ee608b4a8d79c` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `Bash` | 20 |
| `Grep` | 6 |
| `Read` | 4 |
| `Write` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `Bash` |
| `Bash` |
| `Bash` |
| `Bash` |
| `Grep` |
| `Grep` |
| `Grep` |
| `Grep` |
| `Grep` |
| `Bash` |
| `Bash` |
| `Bash` |

## Conversation Preview

Parsed from transcript using the same message categories as the dashboard trace parser.

| Seq | Type | Subtype | Tool | Text |
|---:|---|---|---|---|
| 1 | `system` | `init` | `-` | - |
| 2 | `assistant` | `text` | `-` | I'll help you trace the complete type family for `FxVanillaOption` across the OpenGamma Strata project. Let me start by exploring the repository structure. |
| 3 | `assistant` | `tool_use` | `Bash` | - |
| 4 | `assistant` | `tool_use` | `Bash` | - |
| 5 | `user` | `text` | `-` | - |
| 6 | `user` | `text` | `-` | - |
| 7 | `assistant` | `tool_use` | `Bash` | - |
| 8 | `user` | `text` | `-` | - |
| 9 | `assistant` | `tool_use` | `Bash` | - |
| 10 | `user` | `text` | `-` | - |
| 11 | `assistant` | `tool_use` | `Grep` | - |
| 12 | `assistant` | `tool_use` | `Grep` | - |
| 13 | `assistant` | `tool_use` | `Grep` | - |
| 14 | `assistant` | `tool_use` | `Grep` | - |
| 15 | `user` | `text` | `-` | - |
| 16 | `user` | `text` | `-` | - |
| 17 | `user` | `text` | `-` | - |
| 18 | `user` | `text` | `-` | - |
| 19 | `assistant` | `text` | `-` | Now let me search for the pricer classes: |
| 20 | `assistant` | `tool_use` | `Grep` | - |
| 21 | `user` | `text` | `-` | - |
| 22 | `assistant` | `tool_use` | `Bash` | - |
| 23 | `user` | `text` | `-` | - |
| 24 | `assistant` | `tool_use` | `Bash` | - |
| 25 | `user` | `text` | `-` | - |
| 26 | `assistant` | `tool_use` | `Bash` | - |
| 27 | `user` | `text` | `-` | - |
| 28 | `assistant` | `tool_use` | `Grep` | - |
| 29 | `user` | `text` | `-` | - |
| 30 | `assistant` | `tool_use` | `Bash` | - |
| 31 | `user` | `text` | `-` | - |
| 32 | `assistant` | `tool_use` | `Bash` | - |
| 33 | `user` | `text` | `-` | - |
| 34 | `assistant` | `tool_use` | `Bash` | - |
| 35 | `user` | `text` | `-` | - |
| 36 | `assistant` | `tool_use` | `Bash` | - |
| 37 | `user` | `text` | `-` | - |
| 38 | `assistant` | `tool_use` | `Read` | - |
| 39 | `user` | `text` | `-` | - |
| 40 | `assistant` | `tool_use` | `Bash` | - |
| 41 | `user` | `text` | `-` | - |
| 42 | `assistant` | `tool_use` | `Bash` | - |
| 43 | `user` | `text` | `-` | - |
| 44 | `assistant` | `tool_use` | `Bash` | - |
| 45 | `user` | `text` | `-` | - |
| 46 | `assistant` | `tool_use` | `Read` | - |
| 47 | `user` | `text` | `-` | - |
| 48 | `assistant` | `tool_use` | `Read` | - |
| 49 | `user` | `text` | `-` | - |
| 50 | `assistant` | `text` | `-` | Let me search more thoroughly for all possible pricer variants: |
| 51 | `assistant` | `tool_use` | `Bash` | - |
| 52 | `user` | `text` | `-` | - |
| 53 | `assistant` | `tool_use` | `Bash` | - |
| 54 | `user` | `text` | `-` | - |
| 55 | `assistant` | `tool_use` | `Bash` | - |
| 56 | `user` | `text` | `-` | - |
| 57 | `assistant` | `tool_use` | `Bash` | - |
| 58 | `user` | `text` | `-` | - |
| 59 | `assistant` | `tool_use` | `Read` | - |
| 60 | `user` | `text` | `-` | - |
| 61 | `assistant` | `tool_use` | `Bash` | - |
| 62 | `user` | `text` | `-` | - |
| 63 | `assistant` | `tool_use` | `Bash` | - |
| 64 | `user` | `text` | `-` | - |
| 65 | `assistant` | `text` | `-` | Now let me create the comprehensive answer file with all the findings: |
| 66 | `assistant` | `tool_use` | `Write` | - |
| 67 | `user` | `text` | `-` | - |
| 68 | `assistant` | `text` | `-` | Perfect! I've successfully traced the complete type family for `FxVanillaOption` across the OpenGamma Strata project. Here's a summary of the findings:  ## Summary of Findings  ### 1. **Core Joda-Beans Domain Classes** (... |
