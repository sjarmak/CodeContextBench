# test-integration-001 (baseline-local-direct)

- Run: `test_haiku_20260223_235732`
- Status: `passed`
- Reward: `1.0000`
- Audit JSON: [link](../audits/test_haiku_20260223_235732--baseline-local-direct--test-integration-001.json)
- Trajectory available: `True`
- Transcript available: `True`
- Bundled trajectory: [link](../traces/test_haiku_20260223_235732--baseline-local-direct--test-integration-001/trajectory.json)
- Bundled transcript: [link](../traces/test_haiku_20260223_235732--baseline-local-direct--test-integration-001/claude-code.txt)

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 245.5 |
| Agent execution seconds | 196.9 |
| Input tokens | 1,589,019 |
| Output tokens | 73 |
| Cache tokens | 1,584,507 |
| Tool calls (total) | 26 |
| Tool calls (MCP) | 0 |
| Tool calls (local) | 26 |
| MCP ratio | 0.000 |
| keyword_search calls | - |
| nls_search calls | - |
| deepsearch calls | - |
| `result.json` SHA256 | `6d8454c716e5271d5df210cdeaa646db026a30f9790298396a9addac5b0b5f9b` |
| `trajectory.json` SHA256 | `d98fb8b644bacbd6919fb5b1af278581f8860517cb37400ce402410041132170` |
| transcript SHA256 | `17c8611ec0e994acb0977a250fbf25b67981e6c45b222d752ab4e14a023dd4fd` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `Bash` | 15 |
| `Read` | 10 |
| `Write` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `Bash` |
| `Bash` |
| `Read` |
| `Bash` |
| `Read` |
| `Read` |
| `Bash` |
| `Read` |
| `Bash` |
| `Read` |
| `Bash` |
| `Bash` |

## Conversation Preview

Parsed from transcript using the same message categories as the dashboard trace parser.

| Seq | Type | Subtype | Tool | Text |
|---:|---|---|---|---|
| 1 | `system` | `init` | `-` | - |
| 2 | `assistant` | `text` | `-` | I'll help you write integration tests for Flipt's evaluation API. Let me start by exploring the codebase to understand the API structure and handlers. |
| 3 | `assistant` | `tool_use` | `Bash` | - |
| 4 | `assistant` | `tool_use` | `Bash` | - |
| 5 | `user` | `text` | `-` | - |
| 6 | `user` | `text` | `-` | - |
| 7 | `assistant` | `tool_use` | `Read` | - |
| 8 | `user` | `text` | `-` | - |
| 9 | `assistant` | `tool_use` | `Bash` | - |
| 10 | `user` | `text` | `-` | - |
| 11 | `assistant` | `tool_use` | `Read` | - |
| 12 | `user` | `text` | `-` | - |
| 13 | `assistant` | `tool_use` | `Read` | - |
| 14 | `user` | `text` | `-` | - |
| 15 | `assistant` | `tool_use` | `Bash` | - |
| 16 | `user` | `text` | `-` | - |
| 17 | `assistant` | `tool_use` | `Read` | - |
| 18 | `user` | `text` | `-` | - |
| 19 | `assistant` | `tool_use` | `Bash` | - |
| 20 | `user` | `text` | `-` | - |
| 21 | `assistant` | `tool_use` | `Read` | - |
| 22 | `user` | `text` | `-` | - |
| 23 | `assistant` | `tool_use` | `Bash` | - |
| 24 | `user` | `text` | `-` | - |
| 25 | `assistant` | `tool_use` | `Bash` | - |
| 26 | `user` | `text` | `-` | - |
| 27 | `assistant` | `tool_use` | `Read` | - |
| 28 | `user` | `text` | `-` | - |
| 29 | `assistant` | `tool_use` | `Bash` | - |
| 30 | `user` | `text` | `-` | - |
| 31 | `assistant` | `tool_use` | `Bash` | - |
| 32 | `user` | `text` | `-` | - |
| 33 | `assistant` | `tool_use` | `Read` | - |
| 34 | `user` | `text` | `-` | - |
| 35 | `assistant` | `tool_use` | `Bash` | - |
| 36 | `user` | `text` | `-` | - |
| 37 | `assistant` | `tool_use` | `Read` | - |
| 38 | `user` | `text` | `-` | - |
| 39 | `assistant` | `tool_use` | `Bash` | - |
| 40 | `user` | `text` | `-` | - |
| 41 | `assistant` | `tool_use` | `Read` | - |
| 42 | `user` | `text` | `-` | - |
| 43 | `assistant` | `tool_use` | `Bash` | - |
| 44 | `user` | `text` | `-` | - |
| 45 | `assistant` | `tool_use` | `Read` | - |
| 46 | `user` | `text` | `-` | - |
| 47 | `assistant` | `text` | `-` | Now I'll create a comprehensive integration test file for the evaluation API. Let me write the tests to cover all the required scenarios. |
| 48 | `assistant` | `tool_use` | `Write` | - |
| 49 | `user` | `text` | `-` | - |
| 50 | `assistant` | `text` | `-` | Now let me verify the integration test file compiles correctly: |
| 51 | `assistant` | `tool_use` | `Bash` | - |
| 52 | `user` | `text` | `-` | - |
| 53 | `assistant` | `tool_use` | `Bash` | - |
| 54 | `user` | `text` | `-` | - |
| 55 | `assistant` | `tool_use` | `Bash` | - |
| 56 | `user` | `text` | `-` | - |
| 57 | `assistant` | `text` | `-` | Perfect! I've successfully created a comprehensive integration test file for Flipt's evaluation API. Here's a summary of what I've written:  ## Test Coverage  The integration test file (`/workspace/integration/evaluation... |
