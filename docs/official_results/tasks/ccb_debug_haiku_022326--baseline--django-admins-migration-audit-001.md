# django-admins-migration-audit-001 (baseline-local-direct)

- Run: `csb_sdlc_debug_haiku_022326`
- Status: `passed`
- Reward: `1.0000`
- Audit JSON: [link](../audits/csb_sdlc_debug_haiku_022326--baseline--django-admins-migration-audit-001.json)
- Trajectory available: `True`
- Transcript available: `True`
- Bundled trajectory: [link](../traces/csb_sdlc_debug_haiku_022326--baseline--django-admins-migration-audit-001/trajectory.json)
- Bundled transcript: [link](../traces/csb_sdlc_debug_haiku_022326--baseline--django-admins-migration-audit-001/claude-code.txt)

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 577.1 |
| Agent execution seconds | 516.7 |
| Input tokens | 2,488,079 |
| Output tokens | 155 |
| Cache tokens | 2,487,304 |
| Tool calls (total) | 69 |
| Tool calls (MCP) | 0 |
| Tool calls (local) | 69 |
| MCP ratio | 0.000 |
| keyword_search calls | - |
| nls_search calls | - |
| deepsearch calls | - |
| `result.json` SHA256 | `96ebdecbce9203e4438b2363bebfaaf6430d5807400571839c2817597fd17b86` |
| `trajectory.json` SHA256 | `ddbea103b8cd94378ff29ec54dbbf1881e36ec1e209b2de49b59729be46dc17b` |
| transcript SHA256 | `52ea1887c781e5cc3bfad9abb782e7ec55dad430d256cea6f92292aaff05b0aa` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `Bash` | 27 |
| `Grep` | 20 |
| `Read` | 15 |
| `TodoWrite` | 4 |
| `Glob` | 1 |
| `Task` | 1 |
| `Write` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `TodoWrite` |
| `Grep` |
| `Grep` |
| `Read` |
| `Read` |
| `Read` |
| `Read` |
| `Task` |
| `Glob` |
| `Grep` |
| `Grep` |
| `Grep` |

## Conversation Preview

Parsed from transcript using the same message categories as the dashboard trace parser.

| Seq | Type | Subtype | Tool | Text |
|---:|---|---|---|---|
| 1 | `system` | `init` | `-` | - |
| 2 | `assistant` | `text` | `-` | I'll conduct a comprehensive migration audit for Django's ADMINS/MANAGERS settings format change. Let me start by systematically searching the codebase for all references to these settings. |
| 3 | `assistant` | `tool_use` | `TodoWrite` | - |
| 4 | `user` | `text` | `-` | - |
| 5 | `assistant` | `tool_use` | `Grep` | - |
| 6 | `user` | `text` | `-` | - |
| 7 | `assistant` | `tool_use` | `Grep` | - |
| 8 | `user` | `text` | `-` | - |
| 9 | `assistant` | `tool_use` | `Read` | - |
| 10 | `user` | `text` | `-` | - |
| 11 | `assistant` | `tool_use` | `Read` | - |
| 12 | `user` | `text` | `-` | - |
| 13 | `assistant` | `tool_use` | `Read` | - |
| 14 | `user` | `text` | `-` | - |
| 15 | `assistant` | `tool_use` | `Read` | - |
| 16 | `user` | `text` | `-` | - |
| 17 | `assistant` | `tool_use` | `Task` | - |
| 18 | `user` | `text` | `-` | Search for all Python test files that contain references to ADMINS or MANAGERS settings. Find files that have: 1. @override_settings with ADMINS or MANAGERS 2. test functions testing ADMINS or MANAGERS behavior 3. Assert... |
| 19 | `assistant` | `tool_use` | `Glob` | - |
| 20 | `user` | `text` | `-` | - |
| 21 | `assistant` | `tool_use` | `Grep` | - |
| 22 | `user` | `text` | `-` | - |
| 23 | `assistant` | `tool_use` | `Grep` | - |
| 24 | `user` | `text` | `-` | - |
| 25 | `assistant` | `tool_use` | `Grep` | - |
| 26 | `user` | `text` | `-` | - |
| 27 | `assistant` | `tool_use` | `Grep` | - |
| 28 | `user` | `text` | `-` | - |
| 29 | `assistant` | `tool_use` | `Grep` | - |
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
| 43 | `assistant` | `tool_use` | `Grep` | - |
| 44 | `user` | `text` | `-` | - |
| 45 | `assistant` | `tool_use` | `Grep` | - |
| 46 | `user` | `text` | `-` | - |
| 47 | `assistant` | `tool_use` | `Grep` | - |
| 48 | `user` | `text` | `-` | - |
| 49 | `assistant` | `tool_use` | `Grep` | - |
| 50 | `user` | `text` | `-` | - |
| 51 | `assistant` | `tool_use` | `Grep` | - |
| 52 | `user` | `text` | `-` | - |
| 53 | `assistant` | `tool_use` | `Grep` | - |
| 54 | `user` | `text` | `-` | - |
| 55 | `assistant` | `tool_use` | `Grep` | - |
| 56 | `user` | `text` | `-` | - |
| 57 | `assistant` | `tool_use` | `Grep` | - |
| 58 | `user` | `text` | `-` | - |
| 59 | `assistant` | `tool_use` | `Grep` | - |
| 60 | `user` | `text` | `-` | - |
| 61 | `assistant` | `tool_use` | `Grep` | - |
| 62 | `user` | `text` | `-` | - |
| 63 | `assistant` | `tool_use` | `Grep` | - |
| 64 | `user` | `text` | `-` | - |
| 65 | `assistant` | `tool_use` | `Bash` | - |
| 66 | `user` | `text` | `-` | - |
| 67 | `assistant` | `tool_use` | `Bash` | - |
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
| 79 | `assistant` | `tool_use` | `Bash` | - |
| 80 | `user` | `text` | `-` | - |
