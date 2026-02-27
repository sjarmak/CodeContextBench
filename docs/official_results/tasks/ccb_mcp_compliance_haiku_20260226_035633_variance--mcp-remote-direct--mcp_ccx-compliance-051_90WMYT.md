# mcp_ccx-compliance-051_90WMYT (mcp-remote-direct)

- Run: `ccb_mcp_compliance_haiku_20260226_035633_variance`
- Status: `passed`
- Reward: `0.8462`
- Audit JSON: [link](../audits/ccb_mcp_compliance_haiku_20260226_035633_variance--mcp-remote-direct--mcp_ccx-compliance-051_90WMYT.json)
- Trajectory available: `True`
- Transcript available: `True`
- Bundled trajectory: [link](../traces/ccb_mcp_compliance_haiku_20260226_035633_variance--mcp-remote-direct--mcp_ccx-compliance-051_90WMYT/trajectory.json)
- Bundled transcript: [link](../traces/ccb_mcp_compliance_haiku_20260226_035633_variance--mcp-remote-direct--mcp_ccx-compliance-051_90WMYT/claude-code.txt)

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 1656.6 |
| Agent execution seconds | 272.3 |
| Input tokens | 5,401,492 |
| Output tokens | 7,976 |
| Cache tokens | 5,400,666 |
| Tool calls (total) | 44 |
| Tool calls (MCP) | 41 |
| Tool calls (local) | 3 |
| MCP ratio | 0.932 |
| keyword_search calls | 22 |
| nls_search calls | 0 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `e0f3d33a164119ac967fa7c86b4f31cfe7ec3a22e7e3b4073c125d8cd81d9a47` |
| `trajectory.json` SHA256 | `99bada4d59221c3f391653d1ce2cd1e83df1ec50aac171c38773c3a5c5a10c78` |
| transcript SHA256 | `5864a8d8ff9ace08a6b7b1549e99a71e880c49283fb2c569e317c3c90dab5701` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `mcp__sourcegraph__sg_keyword_search` | 22 |
| `mcp__sourcegraph__sg_read_file` | 13 |
| `mcp__sourcegraph__sg_list_files` | 5 |
| `Edit` | 1 |
| `Read` | 1 |
| `Write` | 1 |
| `mcp__sourcegraph__sg_list_repos` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_list_repos` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |

## Conversation Preview

Parsed from transcript using the same message categories as the dashboard trace parser.

| Seq | Type | Subtype | Tool | Text |
|---:|---|---|---|---|
| 1 | `system` | `init` | `-` | - |
| 2 | `assistant` | `text` | `-` | I'll help you complete this security compliance audit for TLS configuration across the Prometheus stack. Let me start by discovering the relevant files. |
| 3 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_repos` | - |
| 4 | `user` | `text` | `-` | - |
| 5 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 6 | `user` | `text` | `-` | - |
| 7 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 8 | `user` | `text` | `-` | - |
| 9 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 10 | `user` | `text` | `-` | - |
| 11 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 12 | `user` | `text` | `-` | - |
| 13 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 14 | `user` | `text` | `-` | - |
| 15 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 16 | `user` | `text` | `-` | - |
| 17 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 18 | `user` | `text` | `-` | - |
| 19 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 20 | `user` | `text` | `-` | - |
| 21 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 22 | `user` | `text` | `-` | - |
| 23 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 24 | `user` | `text` | `-` | - |
| 25 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 26 | `user` | `text` | `-` | - |
| 27 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 28 | `user` | `text` | `-` | - |
| 29 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 30 | `user` | `text` | `-` | - |
| 31 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 32 | `user` | `text` | `-` | - |
| 33 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 34 | `user` | `text` | `-` | - |
| 35 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 36 | `user` | `text` | `-` | - |
| 37 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 38 | `user` | `text` | `-` | - |
| 39 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 40 | `user` | `text` | `-` | - |
| 41 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 42 | `user` | `text` | `-` | - |
| 43 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 44 | `user` | `text` | `-` | - |
| 45 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 46 | `user` | `text` | `-` | - |
| 47 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 48 | `user` | `text` | `-` | - |
| 49 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 50 | `user` | `text` | `-` | - |
| 51 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 52 | `user` | `text` | `-` | - |
| 53 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 54 | `user` | `text` | `-` | - |
| 55 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 56 | `user` | `text` | `-` | - |
| 57 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 58 | `user` | `text` | `-` | - |
| 59 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 60 | `user` | `text` | `-` | - |
| 61 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 62 | `user` | `text` | `-` | - |
| 63 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 64 | `user` | `text` | `-` | - |
| 65 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 66 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 67 | `user` | `text` | `-` | - |
| 68 | `user` | `text` | `-` | - |
| 69 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 70 | `user` | `text` | `-` | - |
| 71 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 72 | `user` | `text` | `-` | - |
| 73 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 74 | `user` | `text` | `-` | - |
| 75 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 76 | `user` | `text` | `-` | - |
| 77 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 78 | `user` | `text` | `-` | - |
| 79 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 80 | `user` | `text` | `-` | - |
