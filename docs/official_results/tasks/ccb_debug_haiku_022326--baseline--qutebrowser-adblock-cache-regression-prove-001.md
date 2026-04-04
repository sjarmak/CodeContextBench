# qutebrowser-adblock-cache-regression-prove-001 (baseline-local-direct)

- Run: `csb_sdlc_debug_haiku_022326`
- Status: `passed`
- Reward: `0.5000`
- Audit JSON: [link](../audits/csb_sdlc_debug_haiku_022326--baseline--qutebrowser-adblock-cache-regression-prove-001.json)
- Trajectory available: `True`
- Transcript available: `True`
- Bundled trajectory: [link](../traces/csb_sdlc_debug_haiku_022326--baseline--qutebrowser-adblock-cache-regression-prove-001/trajectory.json)
- Bundled transcript: [link](../traces/csb_sdlc_debug_haiku_022326--baseline--qutebrowser-adblock-cache-regression-prove-001/claude-code.txt)

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 313.6 |
| Agent execution seconds | 222.5 |
| Input tokens | 3,194,515 |
| Output tokens | 180 |
| Cache tokens | 3,193,821 |
| Tool calls (total) | 33 |
| Tool calls (MCP) | 0 |
| Tool calls (local) | 33 |
| MCP ratio | 0.000 |
| keyword_search calls | - |
| nls_search calls | - |
| deepsearch calls | - |
| `result.json` SHA256 | `ad8ef925f683f0c84032f504501f05fc9aa6520f115232668b5a181c2d60de42` |
| `trajectory.json` SHA256 | `2bc3be61fbb80d20bdf4ddba8ca9bc52dfc94e68dc682879229a901a1acd4633` |
| transcript SHA256 | `e9161b9c3b6a598f8307f62ef2449cc7a4cfba66c8b80e172098a23289a1640b` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `Bash` | 25 |
| `Read` | 5 |
| `Write` | 2 |
| `Edit` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `Bash` |
| `Read` |
| `Read` |
| `Bash` |
| `Bash` |
| `Read` |
| `Bash` |
| `Bash` |
| `Bash` |
| `Bash` |
| `Bash` |
| `Write` |

## Conversation Preview

Parsed from transcript using the same message categories as the dashboard trace parser.

| Seq | Type | Subtype | Tool | Text |
|---:|---|---|---|---|
| 1 | `system` | `init` | `-` | - |
| 2 | `assistant` | `text` | `-` | I'll help you investigate this bug and write a regression test. Let me start by exploring the qutebrowser codebase to understand the ad-blocker cache loading mechanism. |
| 3 | `assistant` | `tool_use` | `Bash` | - |
| 4 | `user` | `text` | `-` | - |
| 5 | `assistant` | `tool_use` | `Read` | - |
| 6 | `user` | `text` | `-` | - |
| 7 | `assistant` | `text` | `-` | Let me check the test file to understand how this is tested: |
| 8 | `assistant` | `tool_use` | `Read` | - |
| 9 | `user` | `text` | `-` | - |
| 10 | `assistant` | `text` | `-` | Let me check how the tests set up mocks and what imports are available: |
| 11 | `assistant` | `tool_use` | `Bash` | - |
| 12 | `user` | `text` | `-` | - |
| 13 | `assistant` | `tool_use` | `Bash` | - |
| 14 | `user` | `text` | `-` | - |
| 15 | `assistant` | `tool_use` | `Read` | - |
| 16 | `user` | `text` | `-` | - |
| 17 | `assistant` | `tool_use` | `Bash` | - |
| 18 | `user` | `text` | `-` | - |
| 19 | `assistant` | `tool_use` | `Bash` | - |
| 20 | `user` | `text` | `-` | - |
| 21 | `assistant` | `tool_use` | `Bash` | - |
| 22 | `user` | `text` | `-` | - |
| 23 | `assistant` | `tool_use` | `Bash` | - |
| 24 | `user` | `text` | `-` | - |
| 25 | `assistant` | `text` | `-` | Now let me create a comprehensive regression test. First, let me verify the current behavior: |
| 26 | `assistant` | `tool_use` | `Bash` | - |
| 27 | `user` | `text` | `-` | - |
| 28 | `assistant` | `text` | `-` | Now I'll create the regression test file: |
| 29 | `assistant` | `tool_use` | `Write` | - |
| 30 | `user` | `text` | `-` | - |
| 31 | `assistant` | `tool_use` | `Bash` | - |
| 32 | `user` | `text` | `-` | - |
| 33 | `assistant` | `tool_use` | `Bash` | - |
| 34 | `user` | `text` | `-` | - |
| 35 | `assistant` | `tool_use` | `Read` | - |
| 36 | `user` | `text` | `-` | - |
| 37 | `assistant` | `tool_use` | `Bash` | - |
| 38 | `user` | `text` | `-` | - |
| 39 | `assistant` | `tool_use` | `Edit` | - |
| 40 | `user` | `text` | `-` | - |
| 41 | `assistant` | `tool_use` | `Bash` | - |
| 42 | `user` | `text` | `-` | - |
| 43 | `assistant` | `tool_use` | `Bash` | - |
| 44 | `user` | `text` | `-` | - |
| 45 | `assistant` | `tool_use` | `Bash` | - |
| 46 | `user` | `text` | `-` | - |
| 47 | `assistant` | `tool_use` | `Bash` | - |
| 48 | `user` | `text` | `-` | - |
| 49 | `assistant` | `tool_use` | `Bash` | - |
| 50 | `user` | `text` | `-` | - |
| 51 | `assistant` | `tool_use` | `Bash` | - |
| 52 | `user` | `text` | `-` | - |
| 53 | `assistant` | `tool_use` | `Bash` | - |
| 54 | `user` | `text` | `-` | - |
| 55 | `assistant` | `tool_use` | `Bash` | - |
| 56 | `user` | `text` | `-` | - |
| 57 | `assistant` | `text` | `-` | Perfect! The tests are working. Let me verify they can be run with the exact command specified and create a summary: |
| 58 | `assistant` | `tool_use` | `Bash` | - |
| 59 | `user` | `text` | `-` | - |
| 60 | `assistant` | `text` | `-` | Let me create a comprehensive summary document: |
| 61 | `assistant` | `tool_use` | `Write` | - |
| 62 | `user` | `text` | `-` | - |
| 63 | `assistant` | `tool_use` | `Bash` | - |
| 64 | `user` | `text` | `-` | - |
| 65 | `assistant` | `tool_use` | `Read` | - |
| 66 | `user` | `text` | `-` | - |
| 67 | `assistant` | `text` | `-` | Perfect! Let me create a final summary showing the test structure: |
| 68 | `assistant` | `tool_use` | `Bash` | - |
| 69 | `user` | `text` | `-` | - |
| 70 | `assistant` | `tool_use` | `Bash` | - |
| 71 | `user` | `text` | `-` | - |
| 72 | `assistant` | `tool_use` | `Bash` | - |
| 73 | `user` | `text` | `-` | - |
| 74 | `assistant` | `tool_use` | `Bash` | - |
| 75 | `user` | `text` | `-` | - |
| 76 | `assistant` | `text` | `-` | Perfect! I have successfully completed the task. Here's what has been delivered:  ## Summary  I've investigated the qutebrowser ad-blocker cache corruption bug and created a comprehensive regression test that demonstrate... |
