# bl_CCX-agentic-122_8VHUFv (baseline-local-artifact)

- Run: `ccb_mcp_org_haiku_20260225_011700`
- Status: `passed`
- Reward: `0.5000`
- Audit JSON: [link](../audits/ccb_mcp_org_haiku_20260225_011700--baseline-local-artifact--bl_CCX-agentic-122_8VHUFv.json)
- Trajectory available: `True`
- Transcript available: `True`
- Bundled trajectory: [link](../traces/ccb_mcp_org_haiku_20260225_011700--baseline-local-artifact--bl_CCX-agentic-122_8VHUFv/trajectory.json)
- Bundled transcript: [link](../traces/ccb_mcp_org_haiku_20260225_011700--baseline-local-artifact--bl_CCX-agentic-122_8VHUFv/claude-code.txt)

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 8550.3 |
| Agent execution seconds | 3683.3 |
| Input tokens | 2,828,702 |
| Output tokens | 184 |
| Cache tokens | 2,828,084 |
| Tool calls (total) | 39 |
| Tool calls (MCP) | 0 |
| Tool calls (local) | 39 |
| MCP ratio | 0.000 |
| keyword_search calls | - |
| nls_search calls | - |
| deepsearch calls | - |
| `result.json` SHA256 | `47d48c8069bc0f18ab5ec45f857100eba686442895407bbe43c8ad420ddea219` |
| `trajectory.json` SHA256 | `074b6ae860d520fd5614367f9e5afcb1a4a70f6446af448ea2e4dc65f5b39308` |
| transcript SHA256 | `35bcbb16c1c5be455339f0ee930cfbc340e950300170ee461011637e240c817f` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `Bash` | 21 |
| `Read` | 15 |
| `Write` | 3 |

## Parsed Trace Samples

| Tool |
|---|
| `Bash` |
| `Bash` |
| `Bash` |
| `Bash` |
| `Read` |
| `Bash` |
| `Bash` |
| `Read` |
| `Read` |
| `Bash` |
| `Bash` |
| `Bash` |

## Conversation Preview

Parsed from transcript using the same message categories as the dashboard trace parser.

| Seq | Type | Subtype | Tool | Text |
|---:|---|---|---|---|
| 1 | `system` | `init` | `-` | - |
| 2 | `assistant` | `text` | `-` | I'll help you implement an XPCOM component following Firefox's established patterns. Let me start by exploring the repository structure and understanding the requirements. |
| 3 | `assistant` | `tool_use` | `Bash` | - |
| 4 | `user` | `text` | `-` | - |
| 5 | `assistant` | `tool_use` | `Bash` | - |
| 6 | `user` | `text` | `-` | - |
| 7 | `assistant` | `tool_use` | `Bash` | - |
| 8 | `user` | `text` | `-` | - |
| 9 | `assistant` | `tool_use` | `Bash` | - |
| 10 | `user` | `text` | `-` | - |
| 11 | `assistant` | `tool_use` | `Read` | - |
| 12 | `user` | `text` | `-` | - |
| 13 | `assistant` | `tool_use` | `Bash` | - |
| 14 | `user` | `text` | `-` | - |
| 15 | `assistant` | `tool_use` | `Bash` | - |
| 16 | `user` | `text` | `-` | - |
| 17 | `assistant` | `tool_use` | `Read` | - |
| 18 | `user` | `text` | `-` | - |
| 19 | `assistant` | `tool_use` | `Read` | - |
| 20 | `user` | `text` | `-` | - |
| 21 | `assistant` | `tool_use` | `Bash` | - |
| 22 | `user` | `text` | `-` | - |
| 23 | `assistant` | `tool_use` | `Bash` | - |
| 24 | `user` | `text` | `-` | - |
| 25 | `assistant` | `tool_use` | `Bash` | - |
| 26 | `user` | `text` | `-` | - |
| 27 | `assistant` | `tool_use` | `Read` | - |
| 28 | `user` | `text` | `-` | - |
| 29 | `assistant` | `tool_use` | `Read` | - |
| 30 | `user` | `text` | `-` | - |
| 31 | `assistant` | `tool_use` | `Bash` | - |
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
| 45 | `assistant` | `tool_use` | `Read` | - |
| 46 | `user` | `text` | `-` | - |
| 47 | `assistant` | `tool_use` | `Read` | - |
| 48 | `user` | `text` | `-` | - |
| 49 | `assistant` | `tool_use` | `Bash` | - |
| 50 | `user` | `text` | `-` | - |
| 51 | `assistant` | `tool_use` | `Read` | - |
| 52 | `user` | `text` | `-` | - |
| 53 | `assistant` | `tool_use` | `Bash` | - |
| 54 | `user` | `text` | `-` | - |
| 55 | `assistant` | `tool_use` | `Bash` | - |
| 56 | `user` | `text` | `-` | - |
| 57 | `assistant` | `tool_use` | `Bash` | - |
| 58 | `user` | `text` | `-` | - |
| 59 | `assistant` | `tool_use` | `Bash` | - |
| 60 | `user` | `text` | `-` | - |
| 61 | `assistant` | `tool_use` | `Bash` | - |
| 62 | `user` | `text` | `-` | - |
| 63 | `assistant` | `tool_use` | `Bash` | - |
| 64 | `user` | `text` | `-` | - |
| 65 | `assistant` | `tool_use` | `Read` | - |
| 66 | `user` | `text` | `-` | - |
| 67 | `assistant` | `text` | `-` | Now I'll create an XPCOM component following Firefox's established patterns. Let me start by writing the component files. |
| 68 | `assistant` | `tool_use` | `Write` | - |
| 69 | `user` | `text` | `-` | - |
| 70 | `assistant` | `tool_use` | `Write` | - |
| 71 | `user` | `text` | `-` | - |
| 72 | `assistant` | `tool_use` | `Write` | - |
| 73 | `user` | `text` | `-` | - |
| 74 | `assistant` | `tool_use` | `Bash` | - |
| 75 | `user` | `text` | `-` | - |
| 76 | `assistant` | `tool_use` | `Read` | - |
| 77 | `user` | `text` | `-` | - |
| 78 | `assistant` | `tool_use` | `Read` | - |
| 79 | `user` | `text` | `-` | - |
| 80 | `assistant` | `tool_use` | `Read` | - |
