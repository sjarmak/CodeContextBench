# teleport-ssh-regression-prove-001 (baseline-local-direct)

- Run: `debug_haiku_20260223_154724`
- Status: `passed`
- Reward: `0.5000`
- Audit JSON: [link](../audits/debug_haiku_20260223_154724--baseline-local-direct--teleport-ssh-regression-prove-001.json)
- Trajectory available: `True`
- Transcript available: `True`
- Bundled trajectory: [link](../traces/debug_haiku_20260223_154724--baseline-local-direct--teleport-ssh-regression-prove-001/trajectory.json)
- Bundled transcript: [link](../traces/debug_haiku_20260223_154724--baseline-local-direct--teleport-ssh-regression-prove-001/claude-code.txt)

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 1219.0 |
| Agent execution seconds | 1087.0 |
| Input tokens | 8,436,793 |
| Output tokens | 370 |
| Cache tokens | 8,436,221 |
| Tool calls (total) | 118 |
| Tool calls (MCP) | 0 |
| Tool calls (local) | 118 |
| MCP ratio | 0.000 |
| keyword_search calls | - |
| nls_search calls | - |
| deepsearch calls | - |
| `result.json` SHA256 | `325e04e80b8ab76db83307f97f1bac1b69cf7cb31b950ed73323a8d44bc2865d` |
| `trajectory.json` SHA256 | `68ecb5e4a1f45e9a935ca952eb45951f1efc3c375f0baadb08ce23254a3b3bcc` |
| transcript SHA256 | `e59669c766187e30e341ced4211b3fb38162fa5ce84f11ec97c56ea116855de8` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `Bash` | 64 |
| `Read` | 33 |
| `Edit` | 10 |
| `Grep` | 5 |
| `Write` | 3 |
| `Task` | 1 |
| `TaskOutput` | 1 |
| `TaskStop` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `Bash` |
| `Read` |
| `Read` |
| `Read` |
| `Task` |
| `Grep` |
| `Grep` |
| `Grep` |
| `Read` |
| `Read` |
| `Grep` |
| `Grep` |

## Conversation Preview

Parsed from transcript using the same message categories as the dashboard trace parser.

| Seq | Type | Subtype | Tool | Text |
|---:|---|---|---|---|
| 1 | `system` | `init` | `-` | - |
| 2 | `assistant` | `text` | `-` | I'll help you investigate the multi-device U2F authentication bug and write a regression test. Let me start by exploring the repository structure to understand how U2F authentication is implemented. |
| 3 | `assistant` | `tool_use` | `Bash` | - |
| 4 | `user` | `text` | `-` | - |
| 5 | `assistant` | `tool_use` | `Read` | - |
| 6 | `user` | `text` | `-` | - |
| 7 | `assistant` | `tool_use` | `Read` | - |
| 8 | `user` | `text` | `-` | - |
| 9 | `assistant` | `tool_use` | `Read` | - |
| 10 | `user` | `text` | `-` | - |
| 11 | `assistant` | `tool_use` | `Task` | - |
| 12 | `user` | `text` | `-` | Find where AuthenticateInit is called and how multiple U2F devices are handled during authentication. Also search for code that handles MFA device lists and creates challenges for multiple devices. Look for files that ca... |
| 13 | `assistant` | `tool_use` | `Grep` | - |
| 14 | `assistant` | `tool_use` | `Grep` | - |
| 15 | `user` | `text` | `-` | - |
| 16 | `assistant` | `tool_use` | `Grep` | - |
| 17 | `user` | `text` | `-` | - |
| 18 | `user` | `text` | `-` | - |
| 19 | `assistant` | `tool_use` | `Read` | - |
| 20 | `user` | `text` | `-` | - |
| 21 | `assistant` | `tool_use` | `Read` | - |
| 22 | `user` | `text` | `-` | - |
| 23 | `assistant` | `tool_use` | `Grep` | - |
| 24 | `user` | `text` | `-` | - |
| 25 | `assistant` | `tool_use` | `Grep` | - |
| 26 | `user` | `text` | `-` | - |
| 27 | `assistant` | `tool_use` | `Read` | - |
| 28 | `user` | `text` | `-` | - |
| 29 | `assistant` | `tool_use` | `Bash` | - |
| 30 | `user` | `text` | `-` | - |
| 31 | `assistant` | `tool_use` | `Bash` | - |
| 32 | `user` | `text` | `-` | - |
| 33 | `assistant` | `tool_use` | `Bash` | - |
| 34 | `user` | `text` | `-` | - |
| 35 | `assistant` | `tool_use` | `Bash` | - |
| 36 | `user` | `text` | `-` | - |
| 37 | `assistant` | `tool_use` | `Read` | - |
| 38 | `user` | `text` | `-` | - |
| 39 | `assistant` | `tool_use` | `Read` | - |
| 40 | `user` | `text` | `-` | - |
| 41 | `assistant` | `tool_use` | `Read` | - |
| 42 | `user` | `text` | `-` | - |
| 43 | `assistant` | `tool_use` | `Bash` | - |
| 44 | `user` | `text` | `-` | - |
| 45 | `assistant` | `tool_use` | `Read` | - |
| 46 | `user` | `text` | `-` | - |
| 47 | `assistant` | `tool_use` | `Read` | - |
| 48 | `user` | `text` | `-` | - |
| 49 | `assistant` | `tool_use` | `Bash` | - |
| 50 | `user` | `text` | `-` | - |
| 51 | `assistant` | `tool_use` | `Bash` | - |
| 52 | `user` | `text` | `-` | - |
| 53 | `assistant` | `tool_use` | `Bash` | - |
| 54 | `user` | `text` | `-` | - |
| 55 | `assistant` | `tool_use` | `Bash` | - |
| 56 | `user` | `text` | `-` | - |
| 57 | `assistant` | `tool_use` | `Read` | - |
| 58 | `user` | `text` | `-` | - |
| 59 | `assistant` | `tool_use` | `Bash` | - |
| 60 | `user` | `text` | `-` | - |
| 61 | `assistant` | `tool_use` | `Read` | - |
| 62 | `user` | `text` | `-` | - |
| 63 | `assistant` | `tool_use` | `Bash` | - |
| 64 | `user` | `text` | `-` | - |
| 65 | `assistant` | `tool_use` | `Bash` | - |
| 66 | `user` | `text` | `-` | - |
| 67 | `assistant` | `tool_use` | `Read` | - |
| 68 | `user` | `text` | `-` | - |
| 69 | `assistant` | `tool_use` | `Read` | - |
| 70 | `user` | `text` | `-` | - |
| 71 | `assistant` | `tool_use` | `Bash` | - |
| 72 | `user` | `text` | `-` | - |
| 73 | `assistant` | `tool_use` | `Read` | - |
| 74 | `user` | `text` | `-` | - |
| 75 | `assistant` | `tool_use` | `Bash` | - |
| 76 | `user` | `text` | `-` | - |
| 77 | `assistant` | `tool_use` | `Bash` | - |
| 78 | `user` | `text` | `-` | - |
| 79 | `assistant` | `tool_use` | `Bash` | - |
| 80 | `user` | `text` | `-` | - |
