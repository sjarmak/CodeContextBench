# envoy-request-routing-qa-001 (baseline-local-direct)

- Run: `understand_haiku_20260224_001815`
- Status: `failed`
- Reward: `0.0000`
- Audit JSON: [link](../audits/understand_haiku_20260224_001815--baseline-local-direct--envoy-request-routing-qa-001.json)
- Trajectory available: `True`
- Transcript available: `True`
- Bundled trajectory: [link](../traces/understand_haiku_20260224_001815--baseline-local-direct--envoy-request-routing-qa-001/trajectory.json)
- Bundled transcript: [link](../traces/understand_haiku_20260224_001815--baseline-local-direct--envoy-request-routing-qa-001/claude-code.txt)

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 369.4 |
| Agent execution seconds | 322.3 |
| Input tokens | 150,252 |
| Output tokens | 8 |
| Cache tokens | 148,984 |
| Tool calls (total) | 57 |
| Tool calls (MCP) | 0 |
| Tool calls (local) | 57 |
| MCP ratio | 0.000 |
| keyword_search calls | - |
| nls_search calls | - |
| deepsearch calls | - |
| `result.json` SHA256 | `7c6ebf61a7be6fc2deb76b769b66b3c4ce7dff85a468311e82b8d156bb250608` |
| `trajectory.json` SHA256 | `e3047c27f4f293d24f119a502994fee5c9bd3ef12687a47a5845dcf96d10455e` |
| transcript SHA256 | `a02d8c6567c95271c888928e261007ea991559c3c044b0e4dfa4a77d12acd83a` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `Read` | 24 |
| `Bash` | 17 |
| `Glob` | 8 |
| `Grep` | 6 |
| `Task` | 2 |

## Parsed Trace Samples

| Tool |
|---|
| `Bash` |
| `Bash` |
| `Task` |
| `Glob` |
| `Glob` |
| `Glob` |
| `Glob` |
| `Bash` |
| `Grep` |
| `Bash` |
| `Grep` |
| `Read` |

## Conversation Preview

Parsed from transcript using the same message categories as the dashboard trace parser.

| Seq | Type | Subtype | Tool | Text |
|---:|---|---|---|---|
| 1 | `system` | `init` | `-` | - |
| 2 | `assistant` | `text` | `-` | I'll help you trace the complete path of an HTTP request through Envoy's routing system. This is a detailed investigation task that requires exploring the codebase to understand how requests flow from TCP accept through ... |
| 3 | `assistant` | `tool_use` | `Bash` | - |
| 4 | `assistant` | `tool_use` | `Bash` | - |
| 5 | `user` | `text` | `-` | - |
| 6 | `user` | `text` | `-` | - |
| 7 | `assistant` | `tool_use` | `Task` | - |
| 8 | `user` | `text` | `-` | Find the main listener implementation files in Envoy. Look for files containing listener manager, listener implementation, and how TCP connections are accepted. Search in source/server and source/common/network directori... |
| 9 | `assistant` | `tool_use` | `Glob` | - |
| 10 | `assistant` | `tool_use` | `Glob` | - |
| 11 | `assistant` | `tool_use` | `Glob` | - |
| 12 | `assistant` | `tool_use` | `Glob` | - |
| 13 | `user` | `text` | `-` | - |
| 14 | `user` | `text` | `-` | - |
| 15 | `user` | `text` | `-` | - |
| 16 | `user` | `text` | `-` | - |
| 17 | `assistant` | `tool_use` | `Bash` | - |
| 18 | `user` | `text` | `-` | - |
| 19 | `assistant` | `tool_use` | `Grep` | - |
| 20 | `user` | `text` | `-` | - |
| 21 | `assistant` | `tool_use` | `Bash` | - |
| 22 | `user` | `text` | `-` | - |
| 23 | `assistant` | `tool_use` | `Grep` | - |
| 24 | `user` | `text` | `-` | - |
| 25 | `assistant` | `tool_use` | `Read` | - |
| 26 | `user` | `text` | `-` | - |
| 27 | `assistant` | `tool_use` | `Read` | - |
| 28 | `user` | `text` | `-` | - |
| 29 | `assistant` | `tool_use` | `Read` | - |
| 30 | `user` | `text` | `-` | - |
| 31 | `assistant` | `tool_use` | `Bash` | - |
| 32 | `user` | `text` | `-` | - |
| 33 | `assistant` | `tool_use` | `Read` | - |
| 34 | `user` | `text` | `-` | - |
| 35 | `assistant` | `tool_use` | `Bash` | - |
| 36 | `user` | `text` | `-` | - |
| 37 | `assistant` | `tool_use` | `Bash` | - |
| 38 | `user` | `text` | `-` | - |
| 39 | `assistant` | `tool_use` | `Bash` | - |
| 40 | `user` | `text` | `-` | - |
| 41 | `assistant` | `tool_use` | `Read` | - |
| 42 | `user` | `text` | `-` | - |
| 43 | `assistant` | `tool_use` | `Bash` | - |
| 44 | `user` | `text` | `-` | - |
| 45 | `assistant` | `tool_use` | `Read` | - |
| 46 | `user` | `text` | `-` | - |
| 47 | `assistant` | `tool_use` | `Read` | - |
| 48 | `user` | `text` | `-` | - |
| 49 | `assistant` | `tool_use` | `Read` | - |
| 50 | `user` | `text` | `-` | - |
| 51 | `assistant` | `tool_use` | `Read` | - |
| 52 | `user` | `text` | `-` | - |
| 53 | `assistant` | `tool_use` | `Bash` | - |
| 54 | `user` | `text` | `-` | - |
| 55 | `assistant` | `tool_use` | `Bash` | - |
| 56 | `user` | `text` | `-` | - |
| 57 | `assistant` | `tool_use` | `Read` | - |
| 58 | `user` | `text` | `-` | - |
| 59 | `assistant` | `tool_use` | `Read` | - |
| 60 | `user` | `text` | `-` | - |
| 61 | `assistant` | `tool_use` | `Bash` | - |
| 62 | `user` | `text` | `-` | - |
| 63 | `assistant` | `tool_use` | `Read` | - |
| 64 | `user` | `text` | `-` | - |
| 65 | `assistant` | `tool_use` | `Read` | - |
| 66 | `user` | `text` | `-` | - |
| 67 | `assistant` | `tool_use` | `Bash` | - |
| 68 | `user` | `text` | `-` | - |
| 69 | `assistant` | `tool_use` | `Read` | - |
| 70 | `user` | `text` | `-` | - |
| 71 | `assistant` | `tool_use` | `Bash` | - |
| 72 | `user` | `text` | `-` | - |
| 73 | `assistant` | `tool_use` | `Read` | - |
| 74 | `user` | `text` | `-` | - |
| 75 | `assistant` | `tool_use` | `Read` | - |
| 76 | `user` | `text` | `-` | - |
| 77 | `assistant` | `tool_use` | `Read` | - |
| 78 | `user` | `text` | `-` | - |
| 79 | `assistant` | `tool_use` | `Bash` | - |
| 80 | `user` | `text` | `-` | - |
