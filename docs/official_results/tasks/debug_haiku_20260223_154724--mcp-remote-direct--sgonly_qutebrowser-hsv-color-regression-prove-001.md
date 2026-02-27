# sgonly_qutebrowser-hsv-color-regression-prove-001 (mcp-remote-direct)

- Run: `debug_haiku_20260223_154724`
- Status: `failed`
- Reward: `0.0000`
- Audit JSON: [link](../audits/debug_haiku_20260223_154724--mcp-remote-direct--sgonly_qutebrowser-hsv-color-regression-prove-001.json)
- Trajectory available: `True`
- Transcript available: `True`
- Bundled trajectory: [link](../traces/debug_haiku_20260223_154724--mcp-remote-direct--sgonly_qutebrowser-hsv-color-regression-prove-001/trajectory.json)
- Bundled transcript: [link](../traces/debug_haiku_20260223_154724--mcp-remote-direct--sgonly_qutebrowser-hsv-color-regression-prove-001/claude-code.txt)

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 348.0 |
| Agent execution seconds | 280.1 |
| Input tokens | 8,157,386 |
| Output tokens | 416 |
| Cache tokens | 8,156,526 |
| Tool calls (total) | 69 |
| Tool calls (MCP) | 1 |
| Tool calls (local) | 67 |
| MCP ratio | 0.014 |
| keyword_search calls | 1 |
| nls_search calls | 0 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `0a9d9b6b3b97fd010aa27dbbc907578be306a7be2f9e1e887847e2c306605760` |
| `trajectory.json` SHA256 | `d33689c917fc745d0bd0c7c7b717de482425780c9e54f703d8a4be7362850318` |
| transcript SHA256 | `c251bab2497e08d34a46e108e42c4b02a2c33acc6458567384cabe732197e5ed` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `Bash` | 64 |
| `Read` | 2 |
| `Write` | 1 |
| `bash` | 1 |
| `mcp__sourcegraph__sg_keyword_search` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_keyword_search` |
| `Bash` |
| `Bash` |
| `Bash` |
| `Bash` |
| `Bash` |
| `Bash` |
| `Bash` |
| `Bash` |
| `Bash` |
| `bash` |
| `Bash` |

## Conversation Preview

Parsed from transcript using the same message categories as the dashboard trace parser.

| Seq | Type | Subtype | Tool | Text |
|---:|---|---|---|---|
| 1 | `system` | `init` | `-` | - |
| 2 | `assistant` | `text` | `-` | I'll help you investigate the HSV color percentage parsing bug and write a regression test. Let me start by exploring the codebase to understand how colors are parsed. |
| 3 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 4 | `user` | `text` | `-` | - |
| 5 | `assistant` | `text` | `-` | Let me search for HSV color parsing locally: |
| 6 | `assistant` | `tool_use` | `Bash` | - |
| 7 | `user` | `text` | `-` | - |
| 8 | `assistant` | `tool_use` | `Bash` | - |
| 9 | `user` | `text` | `-` | - |
| 10 | `assistant` | `tool_use` | `Bash` | - |
| 11 | `user` | `text` | `-` | - |
| 12 | `assistant` | `tool_use` | `Bash` | - |
| 13 | `user` | `text` | `-` | - |
| 14 | `assistant` | `tool_use` | `Bash` | - |
| 15 | `user` | `text` | `-` | - |
| 16 | `assistant` | `tool_use` | `Bash` | - |
| 17 | `user` | `text` | `-` | - |
| 18 | `assistant` | `tool_use` | `Bash` | - |
| 19 | `user` | `text` | `-` | - |
| 20 | `assistant` | `tool_use` | `Bash` | - |
| 21 | `user` | `text` | `-` | - |
| 22 | `assistant` | `tool_use` | `Bash` | - |
| 23 | `user` | `text` | `-` | - |
| 24 | `assistant` | `tool_use` | `bash` | - |
| 25 | `user` | `text` | `-` | - |
| 26 | `assistant` | `tool_use` | `Bash` | - |
| 27 | `user` | `text` | `-` | - |
| 28 | `assistant` | `tool_use` | `Bash` | - |
| 29 | `user` | `text` | `-` | - |
| 30 | `assistant` | `tool_use` | `Read` | - |
| 31 | `user` | `text` | `-` | - |
| 32 | `assistant` | `tool_use` | `Bash` | - |
| 33 | `user` | `text` | `-` | - |
| 34 | `assistant` | `tool_use` | `Bash` | - |
| 35 | `user` | `text` | `-` | - |
| 36 | `assistant` | `tool_use` | `Bash` | - |
| 37 | `user` | `text` | `-` | - |
| 38 | `assistant` | `tool_use` | `Bash` | - |
| 39 | `user` | `text` | `-` | - |
| 40 | `assistant` | `tool_use` | `Bash` | - |
| 41 | `user` | `text` | `-` | - |
| 42 | `assistant` | `tool_use` | `Bash` | - |
| 43 | `user` | `text` | `-` | - |
| 44 | `assistant` | `tool_use` | `Bash` | - |
| 45 | `user` | `text` | `-` | - |
| 46 | `assistant` | `tool_use` | `Bash` | - |
| 47 | `user` | `text` | `-` | - |
| 48 | `assistant` | `tool_use` | `Bash` | - |
| 49 | `user` | `text` | `-` | - |
| 50 | `assistant` | `tool_use` | `Bash` | - |
| 51 | `user` | `text` | `-` | - |
| 52 | `assistant` | `tool_use` | `Bash` | - |
| 53 | `user` | `text` | `-` | - |
| 54 | `assistant` | `tool_use` | `Bash` | - |
| 55 | `user` | `text` | `-` | - |
| 56 | `assistant` | `tool_use` | `Bash` | - |
| 57 | `user` | `text` | `-` | - |
| 58 | `assistant` | `tool_use` | `Bash` | - |
| 59 | `user` | `text` | `-` | - |
| 60 | `assistant` | `tool_use` | `Bash` | - |
| 61 | `user` | `text` | `-` | - |
| 62 | `assistant` | `tool_use` | `Bash` | - |
| 63 | `user` | `text` | `-` | - |
| 64 | `assistant` | `tool_use` | `Bash` | - |
| 65 | `user` | `text` | `-` | - |
| 66 | `assistant` | `tool_use` | `Bash` | - |
| 67 | `user` | `text` | `-` | - |
| 68 | `assistant` | `tool_use` | `Bash` | - |
| 69 | `user` | `text` | `-` | - |
| 70 | `assistant` | `tool_use` | `Bash` | - |
| 71 | `user` | `text` | `-` | - |
| 72 | `assistant` | `tool_use` | `Bash` | - |
| 73 | `user` | `text` | `-` | - |
| 74 | `assistant` | `tool_use` | `Bash` | - |
| 75 | `user` | `text` | `-` | - |
| 76 | `assistant` | `tool_use` | `Bash` | - |
| 77 | `user` | `text` | `-` | - |
| 78 | `assistant` | `tool_use` | `Bash` | - |
| 79 | `user` | `text` | `-` | - |
| 80 | `assistant` | `tool_use` | `Bash` | - |
