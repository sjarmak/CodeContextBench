# django-csrf-session-audit-001 (baseline-local-direct)

- Run: `secure_haiku_20260223_232545`
- Status: `passed`
- Reward: `0.8000`
- Audit JSON: [link](../audits/secure_haiku_20260223_232545--baseline-local-direct--django-csrf-session-audit-001.json)
- Trajectory available: `True`
- Transcript available: `True`
- Bundled trajectory: [link](../traces/secure_haiku_20260223_232545--baseline-local-direct--django-csrf-session-audit-001/trajectory.json)
- Bundled transcript: [link](../traces/secure_haiku_20260223_232545--baseline-local-direct--django-csrf-session-audit-001/claude-code.txt)

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 406.4 |
| Agent execution seconds | 366.0 |
| Input tokens | 1,133,259 |
| Output tokens | 48 |
| Cache tokens | 1,132,876 |
| Tool calls (total) | 14 |
| Tool calls (MCP) | 0 |
| Tool calls (local) | 14 |
| MCP ratio | 0.000 |
| keyword_search calls | - |
| nls_search calls | - |
| deepsearch calls | - |
| `result.json` SHA256 | `a840896dff63c6acd8a55d66c66faccd6fee93766742b1409a265af68216d515` |
| `trajectory.json` SHA256 | `aeb4f8792a7224989610f40034832ed7765f644c2c3fff108bad747ec8c23f12` |
| transcript SHA256 | `34b5b1fee17f5dcff12f05a14b454b156bbb7451c058f77576f4b0b7273e02b3` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `Read` | 10 |
| `Bash` | 3 |
| `Write` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `Bash` |
| `Bash` |
| `Read` |
| `Read` |
| `Read` |
| `Read` |
| `Read` |
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
| 2 | `assistant` | `text` | `-` | I'll help you analyze Django's CSRF protection and session handling pipeline. This is a comprehensive security analysis task. Let me start by exploring the repository structure and tracing the relevant components. |
| 3 | `assistant` | `tool_use` | `Bash` | - |
| 4 | `user` | `text` | `-` | - |
| 5 | `assistant` | `tool_use` | `Bash` | - |
| 6 | `user` | `text` | `-` | - |
| 7 | `assistant` | `text` | `-` | Now let me read the key files to understand the security pipeline. I'll start with the CSRF middleware: |
| 8 | `assistant` | `tool_use` | `Read` | - |
| 9 | `user` | `text` | `-` | - |
| 10 | `assistant` | `tool_use` | `Read` | - |
| 11 | `user` | `text` | `-` | - |
| 12 | `assistant` | `tool_use` | `Read` | - |
| 13 | `user` | `text` | `-` | - |
| 14 | `assistant` | `tool_use` | `Read` | - |
| 15 | `user` | `text` | `-` | - |
| 16 | `assistant` | `tool_use` | `Read` | - |
| 17 | `user` | `text` | `-` | - |
| 18 | `assistant` | `tool_use` | `Read` | - |
| 19 | `user` | `text` | `-` | - |
| 20 | `assistant` | `tool_use` | `Read` | - |
| 21 | `user` | `text` | `-` | - |
| 22 | `assistant` | `tool_use` | `Read` | - |
| 23 | `user` | `text` | `-` | - |
| 24 | `assistant` | `tool_use` | `Read` | - |
| 25 | `user` | `text` | `-` | - |
| 26 | `assistant` | `text` | `-` | Now let me check for the HTTP request handling and other related components: |
| 27 | `assistant` | `tool_use` | `Bash` | - |
| 28 | `user` | `text` | `-` | - |
| 29 | `assistant` | `tool_use` | `Read` | - |
| 30 | `user` | `text` | `-` | - |
| 31 | `assistant` | `text` | `-` | Perfect! Now I have a comprehensive understanding of the Django CSRF and session handling pipeline. Let me create the security analysis document. |
| 32 | `assistant` | `tool_use` | `Write` | - |
| 33 | `user` | `text` | `-` | - |
| 34 | `assistant` | `text` | `-` | Perfect! I've completed a comprehensive security analysis of Django's CSRF protection and session handling pipeline. Here's what I documented:  ## Analysis Summary  **Written to:** `/logs/agent/solution.md`  ### Key Find... |
