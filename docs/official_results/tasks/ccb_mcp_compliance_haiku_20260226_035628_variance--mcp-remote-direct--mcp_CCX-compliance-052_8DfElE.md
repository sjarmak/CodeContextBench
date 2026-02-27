# mcp_CCX-compliance-052_8DfElE (mcp-remote-direct)

- Run: `ccb_mcp_compliance_haiku_20260226_035628_variance`
- Status: `passed`
- Reward: `0.1815`
- Audit JSON: [link](../audits/ccb_mcp_compliance_haiku_20260226_035628_variance--mcp-remote-direct--mcp_CCX-compliance-052_8DfElE.json)
- Trajectory available: `True`
- Transcript available: `True`
- Bundled trajectory: [link](../traces/ccb_mcp_compliance_haiku_20260226_035628_variance--mcp-remote-direct--mcp_CCX-compliance-052_8DfElE/trajectory.json)
- Bundled transcript: [link](../traces/ccb_mcp_compliance_haiku_20260226_035628_variance--mcp-remote-direct--mcp_CCX-compliance-052_8DfElE/claude-code.txt)

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 1616.7 |
| Agent execution seconds | 245.2 |
| Input tokens | 5,064,096 |
| Output tokens | 13,687 |
| Cache tokens | 5,062,984 |
| Tool calls (total) | 69 |
| Tool calls (MCP) | 68 |
| Tool calls (local) | 1 |
| MCP ratio | 0.986 |
| keyword_search calls | - |
| nls_search calls | - |
| deepsearch calls | - |
| `result.json` SHA256 | `2ac78330d60e8f3607358c7959c8fe6b3ceaf9dc945e659d6c25b6fc0381190e` |
| `trajectory.json` SHA256 | `cfd347fc62ca4068aea5399147278c267c3c69a6cdcbfea5ff490c6370217445` |
| transcript SHA256 | `498056e05bf9ed2f56fbeb5b9bebb1754d1423b0bc62261280bd490165cdecd7` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `mcp__sourcegraph__sg_list_files` | 33 |
| `mcp__sourcegraph__sg_read_file` | 29 |
| `mcp__sourcegraph__sg_keyword_search` | 4 |
| `mcp__sourcegraph__sg_nls_search` | 2 |
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
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |

## Conversation Preview

Parsed from transcript using the same message categories as the dashboard trace parser.

| Seq | Type | Subtype | Tool | Text |
|---:|---|---|---|---|
| 1 | `system` | `init` | `-` | - |
| 2 | `assistant` | `text` | `-` | I'll help you audit the access logging infrastructure in Envoy. Let me start by exploring the relevant directories and files. |
| 3 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 4 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 5 | `user` | `text` | `-` | - |
| 6 | `user` | `text` | `-` | - |
| 7 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 8 | `user` | `text` | `-` | - |
| 9 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 10 | `user` | `text` | `-` | - |
| 11 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 12 | `user` | `text` | `-` | - |
| 13 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 14 | `user` | `text` | `-` | - |
| 15 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 16 | `user` | `text` | `-` | - |
| 17 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 18 | `user` | `text` | `-` | - |
| 19 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 20 | `user` | `text` | `-` | - |
| 21 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 22 | `user` | `text` | `-` | - |
| 23 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 24 | `user` | `text` | `-` | - |
| 25 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 26 | `user` | `text` | `-` | - |
| 27 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 28 | `user` | `text` | `-` | - |
| 29 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 30 | `user` | `text` | `-` | - |
| 31 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 32 | `user` | `text` | `-` | - |
| 33 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 34 | `user` | `text` | `-` | - |
| 35 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 36 | `user` | `text` | `-` | - |
| 37 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 38 | `user` | `text` | `-` | - |
| 39 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 40 | `user` | `text` | `-` | - |
| 41 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 42 | `user` | `text` | `-` | - |
| 43 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 44 | `user` | `text` | `-` | - |
| 45 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 46 | `user` | `text` | `-` | - |
| 47 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 48 | `user` | `text` | `-` | - |
| 49 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 50 | `user` | `text` | `-` | - |
| 51 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 52 | `user` | `text` | `-` | - |
| 53 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 54 | `user` | `text` | `-` | - |
| 55 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 56 | `user` | `text` | `-` | - |
| 57 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 58 | `user` | `text` | `-` | - |
| 59 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 60 | `user` | `text` | `-` | - |
| 61 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 62 | `user` | `text` | `-` | - |
| 63 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 64 | `user` | `text` | `-` | - |
| 65 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 66 | `user` | `text` | `-` | - |
| 67 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 68 | `user` | `text` | `-` | - |
| 69 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 70 | `user` | `text` | `-` | - |
| 71 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 72 | `user` | `text` | `-` | - |
| 73 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 74 | `user` | `text` | `-` | - |
| 75 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 76 | `user` | `text` | `-` | - |
| 77 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 78 | `user` | `text` | `-` | - |
| 79 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 80 | `user` | `text` | `-` | - |
