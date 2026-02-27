# mcp_CCX-crossorg-062_7tCLGe (mcp-remote-direct)

- Run: `ccb_mcp_crossorg_haiku_20260226_035628_variance`
- Status: `passed`
- Reward: `0.6800`
- Audit JSON: [link](../audits/ccb_mcp_crossorg_haiku_20260226_035628_variance--mcp-remote-direct--mcp_CCX-crossorg-062_7tCLGe.json)
- Trajectory available: `True`
- Transcript available: `True`
- Bundled trajectory: [link](../traces/ccb_mcp_crossorg_haiku_20260226_035628_variance--mcp-remote-direct--mcp_CCX-crossorg-062_7tCLGe/trajectory.json)
- Bundled transcript: [link](../traces/ccb_mcp_crossorg_haiku_20260226_035628_variance--mcp-remote-direct--mcp_CCX-crossorg-062_7tCLGe/claude-code.txt)

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 1590.5 |
| Agent execution seconds | 224.9 |
| Input tokens | 8,037,173 |
| Output tokens | 14,844 |
| Cache tokens | 8,036,031 |
| Tool calls (total) | 71 |
| Tool calls (MCP) | 70 |
| Tool calls (local) | 1 |
| MCP ratio | 0.986 |
| keyword_search calls | - |
| nls_search calls | - |
| deepsearch calls | - |
| `result.json` SHA256 | `5b4a8bfd8a201926cf65de7cbc15d76f207c5530af8d97327c561b0acd55a8df` |
| `trajectory.json` SHA256 | `0d712a0e309052d64172b413635e5a0a1ce4fab1464816148633a460539884bf` |
| transcript SHA256 | `c0b8ceb67a3973fa3e33607aa00c5e8e580c20de43d8f5ff32741003531b0d66` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `mcp__sourcegraph__sg_list_files` | 44 |
| `mcp__sourcegraph__sg_read_file` | 19 |
| `mcp__sourcegraph__sg_keyword_search` | 7 |
| `Write` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_read_file` |

## Conversation Preview

Parsed from transcript using the same message categories as the dashboard trace parser.

| Seq | Type | Subtype | Tool | Text |
|---:|---|---|---|---|
| 1 | `system` | `init` | `-` | - |
| 2 | `assistant` | `text` | `-` | I'll help you find the gRPC service definitions across these repositories. Let me start by exploring both repositories systematically. |
| 3 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 4 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 5 | `user` | `text` | `-` | - |
| 6 | `user` | `text` | `-` | - |
| 7 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 8 | `user` | `text` | `-` | - |
| 9 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 10 | `user` | `text` | `-` | - |
| 11 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 12 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 13 | `user` | `text` | `-` | - |
| 14 | `user` | `text` | `-` | - |
| 15 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 16 | `user` | `text` | `-` | - |
| 17 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 18 | `user` | `text` | `-` | - |
| 19 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 20 | `user` | `text` | `-` | - |
| 21 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 22 | `user` | `text` | `-` | - |
| 23 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 24 | `user` | `text` | `-` | - |
| 25 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 26 | `user` | `text` | `-` | - |
| 27 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 28 | `user` | `text` | `-` | - |
| 29 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 30 | `user` | `text` | `-` | - |
| 31 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 32 | `user` | `text` | `-` | - |
| 33 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 34 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 35 | `user` | `text` | `-` | - |
| 36 | `user` | `text` | `-` | - |
| 37 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 38 | `user` | `text` | `-` | - |
| 39 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 40 | `user` | `text` | `-` | - |
| 41 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 42 | `user` | `text` | `-` | - |
| 43 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 44 | `user` | `text` | `-` | - |
| 45 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 46 | `user` | `text` | `-` | - |
| 47 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 48 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 49 | `user` | `text` | `-` | - |
| 50 | `user` | `text` | `-` | - |
| 51 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 52 | `user` | `text` | `-` | - |
| 53 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 54 | `user` | `text` | `-` | - |
| 55 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 56 | `user` | `text` | `-` | - |
| 57 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 58 | `user` | `text` | `-` | - |
| 59 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 60 | `user` | `text` | `-` | - |
| 61 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 62 | `user` | `text` | `-` | - |
| 63 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 64 | `user` | `text` | `-` | - |
| 65 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 66 | `user` | `text` | `-` | - |
| 67 | `assistant` | `text` | `-` | Now let me compile the complete list of all service definitions. Let me search more comprehensively for all remaining service directories. |
| 68 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 69 | `user` | `text` | `-` | - |
| 70 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 71 | `user` | `text` | `-` | - |
| 72 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 73 | `user` | `text` | `-` | - |
| 74 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 75 | `user` | `text` | `-` | - |
| 76 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 77 | `user` | `text` | `-` | - |
| 78 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 79 | `user` | `text` | `-` | - |
| 80 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
