# vscode-ext-host-qa-001 (baseline-local-direct)

- Run: `understand_haiku_20260225_211346`
- Status: `passed`
- Reward: `0.9500`
- Audit JSON: [link](../audits/understand_haiku_20260225_211346--baseline-local-direct--vscode-ext-host-qa-001.json)
- Trajectory available: `True`
- Transcript available: `True`
- Bundled trajectory: [link](../traces/understand_haiku_20260225_211346--baseline-local-direct--vscode-ext-host-qa-001/trajectory.json)
- Bundled transcript: [link](../traces/understand_haiku_20260225_211346--baseline-local-direct--vscode-ext-host-qa-001/claude-code.txt)

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 1044.8 |
| Agent execution seconds | 885.1 |
| Input tokens | 3,153,250 |
| Output tokens | 119 |
| Cache tokens | 3,152,555 |
| Tool calls (total) | 29 |
| Tool calls (MCP) | 0 |
| Tool calls (local) | 29 |
| MCP ratio | 0.000 |
| keyword_search calls | - |
| nls_search calls | - |
| deepsearch calls | - |
| `result.json` SHA256 | `43e1da563db914ba691b0cadd5334e992acedb949329f88fbd0dcb462ea47975` |
| `trajectory.json` SHA256 | `e24a4ff6192f15d43e4a736c733d31c1b38a11b8a0a8a0942bd693b9e16fafde` |
| transcript SHA256 | `be5096499c3cb5539e5b1ba44b4b03847bb34065b3292a092076944ec3b10d94` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `Read` | 15 |
| `Bash` | 13 |
| `Write` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `Bash` |
| `Bash` |
| `Bash` |
| `Bash` |
| `Bash` |
| `Bash` |
| `Bash` |
| `Read` |
| `Read` |
| `Read` |
| `Read` |
| `Bash` |

## Conversation Preview

Parsed from transcript using the same message categories as the dashboard trace parser.

| Seq | Type | Subtype | Tool | Text |
|---:|---|---|---|---|
| 1 | `system` | `init` | `-` | - |
| 2 | `assistant` | `text` | `-` | I'll help you investigate VS Code's extension host isolation architecture. Let me start by exploring the relevant directories and understanding the codebase structure. |
| 3 | `assistant` | `tool_use` | `Bash` | - |
| 4 | `user` | `text` | `-` | - |
| 5 | `assistant` | `tool_use` | `Bash` | - |
| 6 | `user` | `text` | `-` | - |
| 7 | `assistant` | `tool_use` | `Bash` | - |
| 8 | `user` | `text` | `-` | - |
| 9 | `assistant` | `tool_use` | `Bash` | - |
| 10 | `user` | `text` | `-` | - |
| 11 | `assistant` | `tool_use` | `Bash` | - |
| 12 | `user` | `text` | `-` | - |
| 13 | `assistant` | `tool_use` | `Bash` | - |
| 14 | `user` | `text` | `-` | - |
| 15 | `assistant` | `tool_use` | `Bash` | - |
| 16 | `user` | `text` | `-` | - |
| 17 | `assistant` | `text` | `-` | Now let me explore the key files that handle extension host process management and communication: |
| 18 | `assistant` | `tool_use` | `Read` | - |
| 19 | `user` | `text` | `-` | - |
| 20 | `assistant` | `tool_use` | `Read` | - |
| 21 | `user` | `text` | `-` | - |
| 22 | `assistant` | `tool_use` | `Read` | - |
| 23 | `user` | `text` | `-` | - |
| 24 | `assistant` | `tool_use` | `Read` | - |
| 25 | `user` | `text` | `-` | - |
| 26 | `assistant` | `tool_use` | `Bash` | - |
| 27 | `user` | `text` | `-` | - |
| 28 | `assistant` | `tool_use` | `Read` | - |
| 29 | `user` | `text` | `-` | - |
| 30 | `assistant` | `tool_use` | `Read` | - |
| 31 | `user` | `text` | `-` | - |
| 32 | `assistant` | `tool_use` | `Bash` | - |
| 33 | `user` | `text` | `-` | - |
| 34 | `assistant` | `tool_use` | `Read` | - |
| 35 | `user` | `text` | `-` | - |
| 36 | `assistant` | `tool_use` | `Read` | - |
| 37 | `user` | `text` | `-` | - |
| 38 | `assistant` | `tool_use` | `Read` | - |
| 39 | `user` | `text` | `-` | - |
| 40 | `assistant` | `tool_use` | `Bash` | - |
| 41 | `user` | `text` | `-` | - |
| 42 | `assistant` | `tool_use` | `Read` | - |
| 43 | `user` | `text` | `-` | - |
| 44 | `assistant` | `tool_use` | `Read` | - |
| 45 | `user` | `text` | `-` | - |
| 46 | `assistant` | `tool_use` | `Bash` | - |
| 47 | `user` | `text` | `-` | - |
| 48 | `assistant` | `tool_use` | `Read` | - |
| 49 | `user` | `text` | `-` | - |
| 50 | `assistant` | `tool_use` | `Read` | - |
| 51 | `user` | `text` | `-` | - |
| 52 | `assistant` | `tool_use` | `Bash` | - |
| 53 | `user` | `text` | `-` | - |
| 54 | `assistant` | `tool_use` | `Read` | - |
| 55 | `user` | `text` | `-` | - |
| 56 | `assistant` | `text` | `-` | Now let me check one more key file about the RPC protocol's responsiveness and disconnect handling: |
| 57 | `assistant` | `tool_use` | `Read` | - |
| 58 | `user` | `text` | `-` | - |
| 59 | `assistant` | `text` | `-` | Now I'll create a comprehensive investigation report. Let me first create the logs directory: |
| 60 | `assistant` | `tool_use` | `Bash` | - |
| 61 | `user` | `text` | `-` | - |
| 62 | `assistant` | `tool_use` | `Write` | - |
| 63 | `user` | `text` | `-` | - |
| 64 | `assistant` | `text` | `-` | Perfect! I've completed a comprehensive investigation of VS Code's extension host isolation architecture. Here's what I've documented:  ## Investigation Summary  I've created `/logs/agent/investigation.md` with detailed ... |
