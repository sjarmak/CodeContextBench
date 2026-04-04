# mcp_ccx-compliance-051_CKuWlR (mcp-remote-direct)

- Run: `csb_org_compliance_haiku_20260226_035628_variance`
- Status: `passed`
- Reward: `0.6286`
- Audit JSON: [link](../audits/csb_org_compliance_haiku_20260226_035628_variance--mcp-remote-direct--mcp_ccx-compliance-051_CKuWlR.json)
- Trajectory available: `True`
- Transcript available: `True`
- Bundled trajectory: [link](../traces/csb_org_compliance_haiku_20260226_035628_variance--mcp-remote-direct--mcp_ccx-compliance-051_CKuWlR/trajectory.json)
- Bundled transcript: [link](../traces/csb_org_compliance_haiku_20260226_035628_variance--mcp-remote-direct--mcp_ccx-compliance-051_CKuWlR/claude-code.txt)

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 1710.1 |
| Agent execution seconds | 308.1 |
| Input tokens | 7,321,665 |
| Output tokens | 14,257 |
| Cache tokens | 7,320,730 |
| Tool calls (total) | 59 |
| Tool calls (MCP) | 52 |
| Tool calls (local) | 7 |
| MCP ratio | 0.881 |
| keyword_search calls | - |
| nls_search calls | - |
| deepsearch calls | - |
| `result.json` SHA256 | `044150c3ad7cf789cc3eb45edc4b5be9d79400f79d5cb09777e5e1ab2bcd4fca` |
| `trajectory.json` SHA256 | `bedb02e7b050da3e26eced4a781d366cf68b47ad6f97098b38681d34ec251b83` |
| transcript SHA256 | `1b4c08920ceb38d91f7aac896f6f8126ab1b2daa038e8a7868275da4f8f3cf20` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `mcp__sourcegraph__sg_keyword_search` | 22 |
| `mcp__sourcegraph__sg_read_file` | 18 |
| `mcp__sourcegraph__sg_list_files` | 8 |
| `Edit` | 4 |
| `mcp__sourcegraph__sg_nls_search` | 3 |
| `Write` | 2 |
| `Read` | 1 |
| `mcp__sourcegraph__sg_list_repos` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_list_repos` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_nls_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |

## Conversation Preview

Parsed from transcript using the same message categories as the dashboard trace parser.

| Seq | Type | Subtype | Tool | Text |
|---:|---|---|---|---|
| 1 | `system` | `init` | `-` | - |
| 2 | `assistant` | `text` | `-` | I'll help you perform this security compliance audit for TLS configuration across the Prometheus stack. Let me start by discovering and examining the relevant files. |
| 3 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_repos` | - |
| 4 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 5 | `user` | `text` | `-` | - |
| 6 | `user` | `text` | `-` | - |
| 7 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 8 | `user` | `text` | `-` | - |
| 9 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 10 | `user` | `text` | `-` | - |
| 11 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 12 | `user` | `text` | `-` | - |
| 13 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_nls_search` | - |
| 14 | `user` | `text` | `-` | - |
| 15 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 16 | `user` | `text` | `-` | - |
| 17 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 18 | `user` | `text` | `-` | - |
| 19 | `assistant` | `text` | `-` | Now let me search for TLS configurations in the Prometheus repository: |
| 20 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 21 | `user` | `text` | `-` | - |
| 22 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 23 | `user` | `text` | `-` | - |
| 24 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 25 | `user` | `text` | `-` | - |
| 26 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 27 | `user` | `text` | `-` | - |
| 28 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 29 | `user` | `text` | `-` | - |
| 30 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 31 | `user` | `text` | `-` | - |
| 32 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 33 | `user` | `text` | `-` | - |
| 34 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 35 | `user` | `text` | `-` | - |
| 36 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 37 | `user` | `text` | `-` | - |
| 38 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 39 | `user` | `text` | `-` | - |
| 40 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 41 | `user` | `text` | `-` | - |
| 42 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 43 | `user` | `text` | `-` | - |
| 44 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 45 | `user` | `text` | `-` | - |
| 46 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 47 | `user` | `text` | `-` | - |
| 48 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 49 | `user` | `text` | `-` | - |
| 50 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 51 | `user` | `text` | `-` | - |
| 52 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 53 | `user` | `text` | `-` | - |
| 54 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 55 | `user` | `text` | `-` | - |
| 56 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 57 | `user` | `text` | `-` | - |
| 58 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 59 | `user` | `text` | `-` | - |
| 60 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_nls_search` | - |
| 61 | `user` | `text` | `-` | - |
| 62 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 63 | `user` | `text` | `-` | - |
| 64 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 65 | `user` | `text` | `-` | - |
| 66 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 67 | `user` | `text` | `-` | - |
| 68 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 69 | `user` | `text` | `-` | - |
| 70 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 71 | `user` | `text` | `-` | - |
| 72 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 73 | `user` | `text` | `-` | - |
| 74 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 75 | `user` | `text` | `-` | - |
| 76 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 77 | `user` | `text` | `-` | - |
| 78 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 79 | `user` | `text` | `-` | - |
| 80 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
