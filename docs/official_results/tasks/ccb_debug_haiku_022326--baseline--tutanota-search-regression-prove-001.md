# tutanota-search-regression-prove-001 (baseline-local-direct)

- Run: `csb_sdlc_debug_haiku_022326`
- Status: `passed`
- Reward: `0.5000`
- Audit JSON: [link](../audits/csb_sdlc_debug_haiku_022326--baseline--tutanota-search-regression-prove-001.json)
- Trajectory available: `True`
- Transcript available: `True`
- Bundled trajectory: [link](../traces/csb_sdlc_debug_haiku_022326--baseline--tutanota-search-regression-prove-001/trajectory.json)
- Bundled transcript: [link](../traces/csb_sdlc_debug_haiku_022326--baseline--tutanota-search-regression-prove-001/claude-code.txt)

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 1330.7 |
| Agent execution seconds | 1219.2 |
| Input tokens | 4,320,501 |
| Output tokens | 194 |
| Cache tokens | 4,319,944 |
| Tool calls (total) | 100 |
| Tool calls (MCP) | 0 |
| Tool calls (local) | 100 |
| MCP ratio | 0.000 |
| keyword_search calls | - |
| nls_search calls | - |
| deepsearch calls | - |
| `result.json` SHA256 | `feec4dea7e68c0493bdec85fb08e3ef7a8d865e8cfea058fa0c5a322c71cebf9` |
| `trajectory.json` SHA256 | `d6c60839ff862c616a7d9b87ebd4c00b5fc07f0eeb8c66ac85b26a3271c28eee` |
| transcript SHA256 | `733b9a74ceb82143b3c4e655e111fe99342393af439ffc9d22549d89ce7d76fb` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `Bash` | 51 |
| `Read` | 30 |
| `Grep` | 8 |
| `Edit` | 4 |
| `Write` | 4 |
| `Glob` | 2 |
| `Task` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `Task` |
| `Bash` |
| `Bash` |
| `Bash` |
| `Bash` |
| `Glob` |
| `Glob` |
| `Bash` |
| `Bash` |
| `Bash` |
| `Grep` |
| `Read` |

## Conversation Preview

Parsed from transcript using the same message categories as the dashboard trace parser.

| Seq | Type | Subtype | Tool | Text |
|---:|---|---|---|---|
| 1 | `system` | `init` | `-` | - |
| 2 | `assistant` | `text` | `-` | I'll help you investigate this bug and write a regression test. Let me start by exploring the codebase to understand the structure and identify the root cause of the missing key propagation issue. |
| 3 | `assistant` | `tool_use` | `Task` | - |
| 4 | `user` | `text` | `-` | Explore the tutanota codebase to understand: 1. How mails are structured and loaded (Mail entity) 2. Where session keys are managed and stored 3. How entity loading and decryption works 4. The difference between legacy a... |
| 5 | `assistant` | `tool_use` | `Bash` | - |
| 6 | `user` | `text` | `-` | - |
| 7 | `assistant` | `tool_use` | `Bash` | - |
| 8 | `user` | `text` | `-` | - |
| 9 | `assistant` | `tool_use` | `Bash` | - |
| 10 | `user` | `text` | `-` | - |
| 11 | `assistant` | `tool_use` | `Bash` | - |
| 12 | `user` | `text` | `-` | - |
| 13 | `assistant` | `tool_use` | `Glob` | - |
| 14 | `user` | `text` | `-` | - |
| 15 | `assistant` | `tool_use` | `Glob` | - |
| 16 | `user` | `text` | `-` | - |
| 17 | `assistant` | `tool_use` | `Bash` | - |
| 18 | `user` | `text` | `-` | - |
| 19 | `assistant` | `tool_use` | `Bash` | - |
| 20 | `user` | `text` | `-` | - |
| 21 | `assistant` | `tool_use` | `Bash` | - |
| 22 | `user` | `text` | `-` | - |
| 23 | `assistant` | `tool_use` | `Grep` | - |
| 24 | `user` | `text` | `-` | - |
| 25 | `assistant` | `tool_use` | `Read` | - |
| 26 | `user` | `text` | `-` | - |
| 27 | `assistant` | `tool_use` | `Grep` | - |
| 28 | `user` | `text` | `-` | - |
| 29 | `assistant` | `tool_use` | `Grep` | - |
| 30 | `user` | `text` | `-` | - |
| 31 | `assistant` | `tool_use` | `Bash` | - |
| 32 | `user` | `text` | `-` | - |
| 33 | `assistant` | `tool_use` | `Bash` | - |
| 34 | `user` | `text` | `-` | - |
| 35 | `assistant` | `tool_use` | `Bash` | - |
| 36 | `user` | `text` | `-` | - |
| 37 | `assistant` | `tool_use` | `Read` | - |
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
| 49 | `assistant` | `tool_use` | `Read` | - |
| 50 | `user` | `text` | `-` | - |
| 51 | `assistant` | `tool_use` | `Read` | - |
| 52 | `user` | `text` | `-` | - |
| 53 | `assistant` | `tool_use` | `Grep` | - |
| 54 | `user` | `text` | `-` | - |
| 55 | `assistant` | `tool_use` | `Read` | - |
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
| 77 | `assistant` | `tool_use` | `Bash` | - |
| 78 | `user` | `text` | `-` | - |
| 79 | `assistant` | `tool_use` | `Grep` | - |
| 80 | `user` | `text` | `-` | - |
