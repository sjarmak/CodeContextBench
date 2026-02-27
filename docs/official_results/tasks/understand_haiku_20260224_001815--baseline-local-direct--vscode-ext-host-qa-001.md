# vscode-ext-host-qa-001 (baseline-local-direct)

- Run: `understand_haiku_20260224_001815`
- Status: `passed`
- Reward: `1.0000`
- Audit JSON: [link](../audits/understand_haiku_20260224_001815--baseline-local-direct--vscode-ext-host-qa-001.json)
- Trajectory available: `True`
- Transcript available: `True`
- Bundled trajectory: [link](../traces/understand_haiku_20260224_001815--baseline-local-direct--vscode-ext-host-qa-001/trajectory.json)
- Bundled transcript: [link](../traces/understand_haiku_20260224_001815--baseline-local-direct--vscode-ext-host-qa-001/claude-code.txt)

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 226.6 |
| Agent execution seconds | 169.3 |
| Input tokens | 170,084 |
| Output tokens | 8 |
| Cache tokens | 170,002 |
| Tool calls (total) | 38 |
| Tool calls (MCP) | 0 |
| Tool calls (local) | 38 |
| MCP ratio | 0.000 |
| keyword_search calls | - |
| nls_search calls | - |
| deepsearch calls | - |
| `result.json` SHA256 | `5d8cc6c90698ff0aee42976b89627e559994cce73e4d662cd558a8aec53930fc` |
| `trajectory.json` SHA256 | `c5e0cf9d46609ea9ef3c046ec4be72f0baa9c74700d4c7130644c3cb84b5137d` |
| transcript SHA256 | `8d9e5caeb84c7164042f01fcee60379438e1eb66ce52feee88777880d1673aba` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `Read` | 20 |
| `Grep` | 9 |
| `Bash` | 5 |
| `Glob` | 2 |
| `Task` | 1 |
| `Write` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `Task` |
| `Glob` |
| `Glob` |
| `Grep` |
| `Grep` |
| `Grep` |
| `Grep` |
| `Grep` |
| `Read` |
| `Read` |
| `Read` |
| `Read` |

## Conversation Preview

Parsed from transcript using the same message categories as the dashboard trace parser.

| Seq | Type | Subtype | Tool | Text |
|---:|---|---|---|---|
| 1 | `system` | `init` | `-` | - |
| 2 | `assistant` | `text` | `-` | I'll investigate VS Code's extension host isolation architecture by exploring the relevant source directories and analyzing the code. This is a complex multi-process system, so let me start by mapping out the key compone... |
| 3 | `assistant` | `tool_use` | `Task` | - |
| 4 | `user` | `text` | `-` | Explore the VS Code repository to understand the extension host isolation architecture. Focus on:  1. Main entry points for spawning the extension host process in `src/vs/workbench/services/extensions/` and `src/vs/platf... |
| 5 | `assistant` | `tool_use` | `Glob` | - |
| 6 | `user` | `text` | `-` | - |
| 7 | `assistant` | `tool_use` | `Glob` | - |
| 8 | `user` | `text` | `-` | - |
| 9 | `assistant` | `tool_use` | `Grep` | - |
| 10 | `assistant` | `tool_use` | `Grep` | - |
| 11 | `user` | `text` | `-` | - |
| 12 | `user` | `text` | `-` | - |
| 13 | `assistant` | `tool_use` | `Grep` | - |
| 14 | `user` | `text` | `-` | - |
| 15 | `assistant` | `tool_use` | `Grep` | - |
| 16 | `user` | `text` | `-` | - |
| 17 | `assistant` | `tool_use` | `Grep` | - |
| 18 | `user` | `text` | `-` | - |
| 19 | `assistant` | `tool_use` | `Read` | - |
| 20 | `user` | `text` | `-` | - |
| 21 | `assistant` | `tool_use` | `Read` | - |
| 22 | `user` | `text` | `-` | - |
| 23 | `assistant` | `tool_use` | `Read` | - |
| 24 | `user` | `text` | `-` | - |
| 25 | `assistant` | `tool_use` | `Read` | - |
| 26 | `user` | `text` | `-` | - |
| 27 | `assistant` | `tool_use` | `Read` | - |
| 28 | `user` | `text` | `-` | - |
| 29 | `assistant` | `tool_use` | `Read` | - |
| 30 | `user` | `text` | `-` | - |
| 31 | `assistant` | `tool_use` | `Read` | - |
| 32 | `user` | `text` | `-` | - |
| 33 | `assistant` | `tool_use` | `Read` | - |
| 34 | `user` | `text` | `-` | - |
| 35 | `assistant` | `tool_use` | `Read` | - |
| 36 | `user` | `text` | `-` | - |
| 37 | `assistant` | `tool_use` | `Read` | - |
| 38 | `user` | `text` | `-` | - |
| 39 | `assistant` | `tool_use` | `Read` | - |
| 40 | `user` | `text` | `-` | - |
| 41 | `assistant` | `tool_use` | `Grep` | - |
| 42 | `user` | `text` | `-` | - |
| 43 | `assistant` | `tool_use` | `Read` | - |
| 44 | `user` | `text` | `-` | - |
| 45 | `assistant` | `tool_use` | `Grep` | - |
| 46 | `user` | `text` | `-` | - |
| 47 | `assistant` | `tool_use` | `Grep` | - |
| 48 | `user` | `text` | `-` | - |
| 49 | `assistant` | `tool_use` | `Bash` | - |
| 50 | `user` | `text` | `-` | - |
| 51 | `assistant` | `tool_use` | `Read` | - |
| 52 | `user` | `text` | `-` | - |
| 53 | `assistant` | `tool_use` | `Bash` | - |
| 54 | `user` | `text` | `-` | - |
| 55 | `assistant` | `tool_use` | `Read` | - |
| 56 | `user` | `text` | `-` | - |
| 57 | `assistant` | `tool_use` | `Bash` | - |
| 58 | `user` | `text` | `-` | - |
| 59 | `assistant` | `tool_use` | `Read` | - |
| 60 | `user` | `text` | `-` | - |
| 61 | `assistant` | `tool_use` | `Read` | - |
| 62 | `user` | `text` | `-` | - |
| 63 | `assistant` | `tool_use` | `Read` | - |
| 64 | `user` | `text` | `-` | - |
| 65 | `assistant` | `tool_use` | `Bash` | - |
| 66 | `user` | `text` | `-` | - |
| 67 | `assistant` | `tool_use` | `Bash` | - |
| 68 | `user` | `text` | `-` | - |
| 69 | `assistant` | `tool_use` | `Read` | - |
| 70 | `user` | `text` | `-` | - |
| 71 | `assistant` | `tool_use` | `Grep` | - |
| 72 | `user` | `text` | `-` | - |
| 73 | `assistant` | `tool_use` | `Read` | - |
| 74 | `user` | `text` | `-` | - |
| 75 | `assistant` | `tool_use` | `Read` | - |
| 76 | `user` | `text` | `-` | - |
| 77 | `user` | `text` | `-` | - |
| 78 | `assistant` | `text` | `-` | Now let me create the investigation report with the findings structured according to the questions: |
| 79 | `assistant` | `tool_use` | `Write` | - |
| 80 | `user` | `text` | `-` | - |
