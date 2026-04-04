# django-select-for-update-fix-001 (baseline-local-direct)

- Run: `csb_sdlc_fix_haiku_022326`
- Status: `passed`
- Reward: `0.6700`
- Audit JSON: [link](../audits/csb_sdlc_fix_haiku_022326--baseline--django-select-for-update-fix-001.json)
- Trajectory available: `True`
- Transcript available: `True`
- Bundled trajectory: [link](../traces/csb_sdlc_fix_haiku_022326--baseline--django-select-for-update-fix-001/trajectory.json)
- Bundled transcript: [link](../traces/csb_sdlc_fix_haiku_022326--baseline--django-select-for-update-fix-001/claude-code.txt)

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 881.7 |
| Agent execution seconds | 797.7 |
| Input tokens | 5,007,532 |
| Output tokens | 593 |
| Cache tokens | 5,006,551 |
| Tool calls (total) | 53 |
| Tool calls (MCP) | 0 |
| Tool calls (local) | 53 |
| MCP ratio | 0.000 |
| keyword_search calls | - |
| nls_search calls | - |
| deepsearch calls | - |
| `result.json` SHA256 | `12ae06e70a4fb86444126d7574c1c22d9b613f737b41c3ce401dd53d1b7ff753` |
| `trajectory.json` SHA256 | `458d487a8eabc13a11ec6d099181537a2bdee480717a4644f44986c099cba38b` |
| transcript SHA256 | `083aefda6d931faff067b93f634067b0b17761679ff985e7b3c8936e07fa439b` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `Bash` | 28 |
| `Read` | 14 |
| `TodoWrite` | 6 |
| `Edit` | 3 |
| `Glob` | 1 |
| `Write` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `TodoWrite` |
| `Glob` |
| `Bash` |
| `Bash` |
| `Bash` |
| `Read` |
| `Bash` |
| `Bash` |
| `Bash` |
| `Bash` |
| `Bash` |
| `Bash` |

## Conversation Preview

Parsed from transcript using the same message categories as the dashboard trace parser.

| Seq | Type | Subtype | Tool | Text |
|---:|---|---|---|---|
| 1 | `system` | `init` | `-` | - |
| 2 | `assistant` | `text` | `-` | I'll help you investigate this Django bug related to `select_for_update(of=...)` with annotation expressions in `values_list()`. Let me start by exploring the repository structure and tracing the execution path. |
| 3 | `assistant` | `tool_use` | `TodoWrite` | - |
| 4 | `user` | `text` | `-` | - |
| 5 | `assistant` | `tool_use` | `Glob` | - |
| 6 | `user` | `text` | `-` | - |
| 7 | `assistant` | `tool_use` | `Bash` | - |
| 8 | `user` | `text` | `-` | - |
| 9 | `assistant` | `tool_use` | `Bash` | - |
| 10 | `user` | `text` | `-` | - |
| 11 | `assistant` | `tool_use` | `Bash` | - |
| 12 | `user` | `text` | `-` | - |
| 13 | `assistant` | `tool_use` | `Read` | - |
| 14 | `user` | `text` | `-` | - |
| 15 | `assistant` | `tool_use` | `Bash` | - |
| 16 | `user` | `text` | `-` | - |
| 17 | `assistant` | `tool_use` | `Bash` | - |
| 18 | `user` | `text` | `-` | - |
| 19 | `assistant` | `tool_use` | `Bash` | - |
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
| 45 | `assistant` | `tool_use` | `Bash` | - |
| 46 | `user` | `text` | `-` | - |
| 47 | `assistant` | `tool_use` | `Read` | - |
| 48 | `user` | `text` | `-` | - |
| 49 | `assistant` | `tool_use` | `Bash` | - |
| 50 | `user` | `text` | `-` | - |
| 51 | `assistant` | `tool_use` | `Read` | - |
| 52 | `user` | `text` | `-` | - |
| 53 | `assistant` | `tool_use` | `Read` | - |
| 54 | `user` | `text` | `-` | - |
| 55 | `assistant` | `tool_use` | `TodoWrite` | - |
| 56 | `user` | `text` | `-` | - |
| 57 | `assistant` | `tool_use` | `Bash` | - |
| 58 | `user` | `text` | `-` | - |
| 59 | `assistant` | `tool_use` | `Bash` | - |
| 60 | `user` | `text` | `-` | - |
| 61 | `assistant` | `tool_use` | `Read` | - |
| 62 | `user` | `text` | `-` | - |
| 63 | `assistant` | `tool_use` | `Read` | - |
| 64 | `user` | `text` | `-` | - |
| 65 | `assistant` | `tool_use` | `Bash` | - |
| 66 | `user` | `text` | `-` | - |
| 67 | `assistant` | `tool_use` | `Read` | - |
| 68 | `user` | `text` | `-` | - |
| 69 | `assistant` | `tool_use` | `Edit` | - |
| 70 | `user` | `text` | `-` | - |
| 71 | `assistant` | `tool_use` | `Bash` | - |
| 72 | `user` | `text` | `-` | - |
| 73 | `assistant` | `tool_use` | `Bash` | - |
| 74 | `user` | `text` | `-` | - |
| 75 | `assistant` | `tool_use` | `Read` | - |
| 76 | `user` | `text` | `-` | - |
| 77 | `assistant` | `tool_use` | `TodoWrite` | - |
| 78 | `user` | `text` | `-` | - |
| 79 | `assistant` | `tool_use` | `Read` | - |
| 80 | `user` | `text` | `-` | - |
