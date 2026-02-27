# flipt-degraded-context-fix-001 (baseline-local-direct)

- Run: `secure_haiku_20260223_232545`
- Status: `passed`
- Reward: `0.6000`
- Audit JSON: [link](../audits/secure_haiku_20260223_232545--baseline-local-direct--flipt-degraded-context-fix-001.json)
- Trajectory available: `True`
- Transcript available: `True`
- Bundled trajectory: [link](../traces/secure_haiku_20260223_232545--baseline-local-direct--flipt-degraded-context-fix-001/trajectory.json)
- Bundled transcript: [link](../traces/secure_haiku_20260223_232545--baseline-local-direct--flipt-degraded-context-fix-001/claude-code.txt)

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 431.0 |
| Agent execution seconds | 298.6 |
| Input tokens | 5,383,664 |
| Output tokens | 283 |
| Cache tokens | 5,383,069 |
| Tool calls (total) | 54 |
| Tool calls (MCP) | 0 |
| Tool calls (local) | 54 |
| MCP ratio | 0.000 |
| keyword_search calls | - |
| nls_search calls | - |
| deepsearch calls | - |
| `result.json` SHA256 | `de62ef0f8c600cded3a88dcd2ef9b9f5aedb05f886d8febd4e94726f164ae132` |
| `trajectory.json` SHA256 | `cd9061710d0ffba737af3c6be423e75f5662b4ccaa5457edac6d8e0f29d0a0bf` |
| transcript SHA256 | `888817f18f306b77f7c2c7c75681f54cac11f57d804feeccfd3ad402e055e16c` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `Bash` | 18 |
| `Read` | 17 |
| `Edit` | 13 |
| `TodoWrite` | 5 |
| `Write` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `TodoWrite` |
| `Bash` |
| `Read` |
| `Read` |
| `Read` |
| `Read` |
| `Read` |
| `Bash` |
| `Read` |
| `Bash` |
| `Bash` |
| `Bash` |

## Conversation Preview

Parsed from transcript using the same message categories as the dashboard trace parser.

| Seq | Type | Subtype | Tool | Text |
|---:|---|---|---|---|
| 1 | `system` | `init` | `-` | - |
| 2 | `assistant` | `text` | `-` | I'll help you add graceful error handling to the evaluation server. Let me start by exploring the repository structure and understanding the current implementation. |
| 3 | `assistant` | `tool_use` | `TodoWrite` | - |
| 4 | `user` | `text` | `-` | - |
| 5 | `assistant` | `tool_use` | `Bash` | - |
| 6 | `user` | `text` | `-` | - |
| 7 | `assistant` | `tool_use` | `Read` | - |
| 8 | `user` | `text` | `-` | - |
| 9 | `assistant` | `tool_use` | `Read` | - |
| 10 | `user` | `text` | `-` | - |
| 11 | `assistant` | `tool_use` | `Read` | - |
| 12 | `user` | `text` | `-` | - |
| 13 | `assistant` | `tool_use` | `Read` | - |
| 14 | `user` | `text` | `-` | - |
| 15 | `assistant` | `tool_use` | `Read` | - |
| 16 | `user` | `text` | `-` | - |
| 17 | `assistant` | `tool_use` | `Bash` | - |
| 18 | `user` | `text` | `-` | - |
| 19 | `assistant` | `tool_use` | `Read` | - |
| 20 | `user` | `text` | `-` | - |
| 21 | `assistant` | `tool_use` | `Bash` | - |
| 22 | `user` | `text` | `-` | - |
| 23 | `assistant` | `tool_use` | `Bash` | - |
| 24 | `user` | `text` | `-` | - |
| 25 | `assistant` | `tool_use` | `Bash` | - |
| 26 | `user` | `text` | `-` | - |
| 27 | `assistant` | `tool_use` | `Bash` | - |
| 28 | `user` | `text` | `-` | - |
| 29 | `assistant` | `tool_use` | `Bash` | - |
| 30 | `user` | `text` | `-` | - |
| 31 | `assistant` | `tool_use` | `TodoWrite` | - |
| 32 | `user` | `text` | `-` | - |
| 33 | `assistant` | `tool_use` | `Write` | - |
| 34 | `user` | `text` | `-` | - |
| 35 | `assistant` | `tool_use` | `TodoWrite` | - |
| 36 | `user` | `text` | `-` | - |
| 37 | `assistant` | `tool_use` | `Edit` | - |
| 38 | `user` | `text` | `-` | - |
| 39 | `assistant` | `tool_use` | `Edit` | - |
| 40 | `user` | `text` | `-` | - |
| 41 | `assistant` | `tool_use` | `Read` | - |
| 42 | `user` | `text` | `-` | - |
| 43 | `assistant` | `tool_use` | `Edit` | - |
| 44 | `user` | `text` | `-` | - |
| 45 | `assistant` | `tool_use` | `Read` | - |
| 46 | `user` | `text` | `-` | - |
| 47 | `assistant` | `tool_use` | `Edit` | - |
| 48 | `user` | `text` | `-` | - |
| 49 | `assistant` | `tool_use` | `Read` | - |
| 50 | `user` | `text` | `-` | - |
| 51 | `assistant` | `tool_use` | `Edit` | - |
| 52 | `user` | `text` | `-` | - |
| 53 | `assistant` | `tool_use` | `Read` | - |
| 54 | `user` | `text` | `-` | - |
| 55 | `assistant` | `tool_use` | `Edit` | - |
| 56 | `user` | `text` | `-` | - |
| 57 | `assistant` | `tool_use` | `Read` | - |
| 58 | `user` | `text` | `-` | - |
| 59 | `assistant` | `tool_use` | `Edit` | - |
| 60 | `user` | `text` | `-` | - |
| 61 | `assistant` | `tool_use` | `TodoWrite` | - |
| 62 | `user` | `text` | `-` | - |
| 63 | `assistant` | `tool_use` | `Bash` | - |
| 64 | `user` | `text` | `-` | - |
| 65 | `assistant` | `tool_use` | `Edit` | - |
| 66 | `user` | `text` | `-` | - |
| 67 | `assistant` | `tool_use` | `Bash` | - |
| 68 | `user` | `text` | `-` | - |
| 69 | `assistant` | `tool_use` | `Bash` | - |
| 70 | `user` | `text` | `-` | - |
| 71 | `assistant` | `tool_use` | `Read` | - |
| 72 | `user` | `text` | `-` | - |
| 73 | `assistant` | `tool_use` | `Read` | - |
| 74 | `user` | `text` | `-` | - |
| 75 | `assistant` | `tool_use` | `Edit` | - |
| 76 | `user` | `text` | `-` | - |
| 77 | `assistant` | `tool_use` | `Edit` | - |
| 78 | `user` | `text` | `-` | - |
| 79 | `assistant` | `tool_use` | `Bash` | - |
| 80 | `user` | `text` | `-` | - |
