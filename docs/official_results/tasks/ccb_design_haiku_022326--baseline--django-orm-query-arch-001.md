# django-orm-query-arch-001 (baseline-local-direct)

- Run: `csb_sdlc_design_haiku_022326`
- Status: `passed`
- Reward: `0.9100`
- Audit JSON: [link](../audits/csb_sdlc_design_haiku_022326--baseline--django-orm-query-arch-001.json)
- Trajectory available: `True`
- Transcript available: `True`
- Bundled trajectory: [link](../traces/csb_sdlc_design_haiku_022326--baseline--django-orm-query-arch-001/trajectory.json)
- Bundled transcript: [link](../traces/csb_sdlc_design_haiku_022326--baseline--django-orm-query-arch-001/claude-code.txt)

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 1691.0 |
| Agent execution seconds | 1609.7 |
| Input tokens | 181,110 |
| Output tokens | 8 |
| Cache tokens | 181,028 |
| Tool calls (total) | 53 |
| Tool calls (MCP) | 0 |
| Tool calls (local) | 53 |
| MCP ratio | 0.000 |
| keyword_search calls | - |
| nls_search calls | - |
| deepsearch calls | - |
| `result.json` SHA256 | `33741b74aea36b97323a41d40bf01ea0f4fe90ac88f8d346156e93a524bd2fa2` |
| `trajectory.json` SHA256 | `b0260cac9ca7aed2e232d37b44e19ee717f1212c23f329482a37a022b2e6051a` |
| transcript SHA256 | `9a76db023ff530ef3b74e0dc2fc1787e4aefebc56c627e38483b16e923250ef1` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `Read` | 20 |
| `Bash` | 17 |
| `Glob` | 10 |
| `Grep` | 4 |
| `Task` | 1 |
| `Write` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `Task` |
| `Glob` |
| `Glob` |
| `Glob` |
| `Glob` |
| `Glob` |
| `Glob` |
| `Glob` |
| `Glob` |
| `Glob` |
| `Glob` |
| `Read` |

## Conversation Preview

Parsed from transcript using the same message categories as the dashboard trace parser.

| Seq | Type | Subtype | Tool | Text |
|---:|---|---|---|---|
| 1 | `system` | `init` | `-` | - |
| 2 | `assistant` | `text` | `-` | I'll help you map the Django ORM query compilation pipeline. This is a complex architectural task that requires tracing the flow from high-level QuerySet API calls down to SQL execution. Let me start by exploring the cod... |
| 3 | `assistant` | `tool_use` | `Task` | - |
| 4 | `user` | `text` | `-` | You are helping analyze the Django ORM query compilation pipeline. Your task is to systematically explore and document the architecture.  Focus on these key areas: 1. Entry point: How Manager.get_queryset() starts 2. Que... |
| 5 | `assistant` | `tool_use` | `Glob` | - |
| 6 | `assistant` | `tool_use` | `Glob` | - |
| 7 | `assistant` | `tool_use` | `Glob` | - |
| 8 | `assistant` | `tool_use` | `Glob` | - |
| 9 | `user` | `text` | `-` | - |
| 10 | `user` | `text` | `-` | - |
| 11 | `user` | `text` | `-` | - |
| 12 | `user` | `text` | `-` | - |
| 13 | `assistant` | `tool_use` | `Glob` | - |
| 14 | `user` | `text` | `-` | - |
| 15 | `assistant` | `tool_use` | `Glob` | - |
| 16 | `user` | `text` | `-` | - |
| 17 | `assistant` | `tool_use` | `Glob` | - |
| 18 | `user` | `text` | `-` | - |
| 19 | `assistant` | `tool_use` | `Glob` | - |
| 20 | `user` | `text` | `-` | - |
| 21 | `assistant` | `tool_use` | `Glob` | - |
| 22 | `user` | `text` | `-` | - |
| 23 | `assistant` | `tool_use` | `Glob` | - |
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
| 37 | `assistant` | `tool_use` | `Grep` | - |
| 38 | `user` | `text` | `-` | - |
| 39 | `assistant` | `tool_use` | `Grep` | - |
| 40 | `user` | `text` | `-` | - |
| 41 | `assistant` | `tool_use` | `Read` | - |
| 42 | `user` | `text` | `-` | - |
| 43 | `assistant` | `tool_use` | `Read` | - |
| 44 | `user` | `text` | `-` | - |
| 45 | `assistant` | `tool_use` | `Read` | - |
| 46 | `user` | `text` | `-` | - |
| 47 | `assistant` | `tool_use` | `Grep` | - |
| 48 | `user` | `text` | `-` | - |
| 49 | `assistant` | `tool_use` | `Grep` | - |
| 50 | `user` | `text` | `-` | - |
| 51 | `assistant` | `tool_use` | `Bash` | - |
| 52 | `user` | `text` | `-` | - |
| 53 | `assistant` | `tool_use` | `Bash` | - |
| 54 | `user` | `text` | `-` | - |
| 55 | `assistant` | `tool_use` | `Read` | - |
| 56 | `user` | `text` | `-` | - |
| 57 | `assistant` | `tool_use` | `Read` | - |
| 58 | `user` | `text` | `-` | - |
| 59 | `assistant` | `tool_use` | `Bash` | - |
| 60 | `user` | `text` | `-` | - |
| 61 | `assistant` | `tool_use` | `Bash` | - |
| 62 | `user` | `text` | `-` | - |
| 63 | `assistant` | `tool_use` | `Read` | - |
| 64 | `user` | `text` | `-` | - |
| 65 | `assistant` | `tool_use` | `Bash` | - |
| 66 | `user` | `text` | `-` | - |
| 67 | `assistant` | `tool_use` | `Read` | - |
| 68 | `user` | `text` | `-` | - |
| 69 | `assistant` | `tool_use` | `Bash` | - |
| 70 | `user` | `text` | `-` | - |
| 71 | `assistant` | `tool_use` | `Bash` | - |
| 72 | `user` | `text` | `-` | - |
| 73 | `assistant` | `tool_use` | `Bash` | - |
| 74 | `user` | `text` | `-` | - |
| 75 | `assistant` | `tool_use` | `Read` | - |
| 76 | `user` | `text` | `-` | - |
| 77 | `assistant` | `tool_use` | `Bash` | - |
| 78 | `user` | `text` | `-` | - |
| 79 | `assistant` | `tool_use` | `Read` | - |
| 80 | `user` | `text` | `-` | - |
