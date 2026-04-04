# test-coverage-gap-001 (baseline-local-direct)

- Run: `csb_sdlc_test_haiku_20260224_180149`
- Status: `passed`
- Reward: `0.8600`
- Audit JSON: [link](../audits/csb_sdlc_test_haiku_20260224_180149--baseline-local-direct--test-coverage-gap-001.json)
- Trajectory available: `True`
- Transcript available: `True`
- Bundled trajectory: [link](../traces/csb_sdlc_test_haiku_20260224_180149--baseline-local-direct--test-coverage-gap-001/trajectory.json)
- Bundled transcript: [link](../traces/csb_sdlc_test_haiku_20260224_180149--baseline-local-direct--test-coverage-gap-001/claude-code.txt)

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 307.2 |
| Agent execution seconds | 252.7 |
| Input tokens | 3,161,062 |
| Output tokens | 88 |
| Cache tokens | 3,160,284 |
| Tool calls (total) | 35 |
| Tool calls (MCP) | 0 |
| Tool calls (local) | 35 |
| MCP ratio | 0.000 |
| keyword_search calls | - |
| nls_search calls | - |
| deepsearch calls | - |
| `result.json` SHA256 | `532828d4ce21631903b98687bfb8e9c86884f69340c92b8d60021db2f68f90e6` |
| `trajectory.json` SHA256 | `1ea0622ef54a30098250ca4171c89c74aa9542e2589a27991eb3943c499338f2` |
| transcript SHA256 | `4e1453b52e893cec937bc535b2fb4be2bf2b2bb81985c2db2b3661df0ccb8cb4` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `Bash` | 16 |
| `Read` | 15 |
| `Grep` | 3 |
| `Write` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `Bash` |
| `Bash` |
| `Read` |
| `Read` |
| `Bash` |
| `Read` |
| `Read` |
| `Grep` |
| `Bash` |
| `Read` |
| `Bash` |
| `Bash` |

## Conversation Preview

Parsed from transcript using the same message categories as the dashboard trace parser.

| Seq | Type | Subtype | Tool | Text |
|---:|---|---|---|---|
| 1 | `system` | `init` | `-` | - |
| 2 | `assistant` | `text` | `-` | I'll analyze the test coverage gaps in Envoy's HTTP Connection Manager. Let me start by exploring the repository structure and examining the relevant files. |
| 3 | `assistant` | `tool_use` | `Bash` | - |
| 4 | `assistant` | `tool_use` | `Bash` | - |
| 5 | `user` | `text` | `-` | - |
| 6 | `user` | `text` | `-` | - |
| 7 | `assistant` | `tool_use` | `Read` | - |
| 8 | `user` | `text` | `-` | - |
| 9 | `assistant` | `tool_use` | `Read` | - |
| 10 | `user` | `text` | `-` | - |
| 11 | `assistant` | `tool_use` | `Bash` | - |
| 12 | `user` | `text` | `-` | - |
| 13 | `assistant` | `tool_use` | `Read` | - |
| 14 | `user` | `text` | `-` | - |
| 15 | `assistant` | `tool_use` | `Read` | - |
| 16 | `user` | `text` | `-` | - |
| 17 | `assistant` | `text` | `-` | Let me use grep to search for key functions and error handling paths in the implementation: |
| 18 | `assistant` | `tool_use` | `Grep` | - |
| 19 | `user` | `text` | `-` | - |
| 20 | `assistant` | `tool_use` | `Bash` | - |
| 21 | `user` | `text` | `-` | - |
| 22 | `assistant` | `tool_use` | `Read` | - |
| 23 | `user` | `text` | `-` | - |
| 24 | `assistant` | `tool_use` | `Bash` | - |
| 25 | `user` | `text` | `-` | - |
| 26 | `assistant` | `tool_use` | `Bash` | - |
| 27 | `user` | `text` | `-` | - |
| 28 | `assistant` | `tool_use` | `Grep` | - |
| 29 | `user` | `text` | `-` | - |
| 30 | `assistant` | `tool_use` | `Read` | - |
| 31 | `user` | `text` | `-` | - |
| 32 | `assistant` | `tool_use` | `Read` | - |
| 33 | `user` | `text` | `-` | - |
| 34 | `assistant` | `tool_use` | `Bash` | - |
| 35 | `user` | `text` | `-` | - |
| 36 | `assistant` | `tool_use` | `Bash` | - |
| 37 | `user` | `text` | `-` | - |
| 38 | `assistant` | `tool_use` | `Grep` | - |
| 39 | `user` | `text` | `-` | - |
| 40 | `assistant` | `tool_use` | `Read` | - |
| 41 | `user` | `text` | `-` | - |
| 42 | `assistant` | `tool_use` | `Read` | - |
| 43 | `user` | `text` | `-` | - |
| 44 | `assistant` | `tool_use` | `Bash` | - |
| 45 | `user` | `text` | `-` | - |
| 46 | `assistant` | `tool_use` | `Read` | - |
| 47 | `user` | `text` | `-` | - |
| 48 | `assistant` | `tool_use` | `Read` | - |
| 49 | `user` | `text` | `-` | - |
| 50 | `assistant` | `tool_use` | `Bash` | - |
| 51 | `user` | `text` | `-` | - |
| 52 | `assistant` | `tool_use` | `Read` | - |
| 53 | `user` | `text` | `-` | - |
| 54 | `assistant` | `tool_use` | `Read` | - |
| 55 | `user` | `text` | `-` | - |
| 56 | `assistant` | `tool_use` | `Bash` | - |
| 57 | `user` | `text` | `-` | - |
| 58 | `assistant` | `tool_use` | `Read` | - |
| 59 | `user` | `text` | `-` | - |
| 60 | `assistant` | `tool_use` | `Bash` | - |
| 61 | `user` | `text` | `-` | - |
| 62 | `assistant` | `tool_use` | `Read` | - |
| 63 | `user` | `text` | `-` | - |
| 64 | `assistant` | `tool_use` | `Bash` | - |
| 65 | `user` | `text` | `-` | - |
| 66 | `assistant` | `tool_use` | `Bash` | - |
| 67 | `user` | `text` | `-` | - |
| 68 | `assistant` | `tool_use` | `Bash` | - |
| 69 | `user` | `text` | `-` | - |
| 70 | `assistant` | `text` | `-` | Now let me create a comprehensive analysis document by examining actual code paths and test coverage: |
| 71 | `assistant` | `tool_use` | `Bash` | - |
| 72 | `user` | `text` | `-` | - |
| 73 | `assistant` | `text` | `-` | Based on my thorough analysis of the codebase, I'll now create a comprehensive test coverage gap analysis: |
| 74 | `assistant` | `tool_use` | `Write` | - |
| 75 | `user` | `text` | `-` | - |
| 76 | `assistant` | `text` | `-` | Perfect! I've completed a comprehensive test coverage gap analysis for Envoy's HTTP Connection Manager. Here's what I found:  ## Analysis Complete ✓  The analysis identifies **7 specific untested code paths** with concre... |
