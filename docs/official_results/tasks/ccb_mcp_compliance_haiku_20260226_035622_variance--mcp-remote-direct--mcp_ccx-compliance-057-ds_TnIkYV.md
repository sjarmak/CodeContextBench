# mcp_ccx-compliance-057-ds_TnIkYV (mcp-remote-direct)

- Run: `ccb_mcp_compliance_haiku_20260226_035622_variance`
- Status: `passed`
- Reward: `0.9008`
- Audit JSON: [link](../audits/ccb_mcp_compliance_haiku_20260226_035622_variance--mcp-remote-direct--mcp_ccx-compliance-057-ds_TnIkYV.json)
- Trajectory available: `True`
- Transcript available: `True`
- Bundled trajectory: [link](../traces/ccb_mcp_compliance_haiku_20260226_035622_variance--mcp-remote-direct--mcp_ccx-compliance-057-ds_TnIkYV/trajectory.json)
- Bundled transcript: [link](../traces/ccb_mcp_compliance_haiku_20260226_035622_variance--mcp-remote-direct--mcp_ccx-compliance-057-ds_TnIkYV/claude-code.txt)

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 3414.4 |
| Agent execution seconds | 358.9 |
| Input tokens | 5,427,965 |
| Output tokens | 9,604 |
| Cache tokens | 5,427,096 |
| Tool calls (total) | 52 |
| Tool calls (MCP) | 51 |
| Tool calls (local) | 1 |
| MCP ratio | 0.981 |
| keyword_search calls | 10 |
| nls_search calls | 5 |
| deepsearch calls | 1 |
| `result.json` SHA256 | `716c2fd362e7760441ba27bac5f0db2e03394c4a9ed29fad4e71f6949f1918ad` |
| `trajectory.json` SHA256 | `46037e1b465d752ad1a9577565dba873a4055c2e9a75540fb5ce7157650593ee` |
| transcript SHA256 | `72321e7b207fbb5c9bc4489d2a6806dcf20e7791e46c4b48ca351ea7756ad146` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `mcp__sourcegraph__sg_read_file` | 18 |
| `mcp__sourcegraph__sg_list_files` | 15 |
| `mcp__sourcegraph__sg_keyword_search` | 10 |
| `mcp__sourcegraph__sg_nls_search` | 5 |
| `Write` | 1 |
| `mcp__sourcegraph__sg_deepsearch` | 1 |
| `mcp__sourcegraph__sg_deepsearch_read` | 1 |
| `mcp__sourcegraph__sg_list_repos` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_deepsearch` |
| `mcp__sourcegraph__sg_deepsearch_read` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_nls_search` |
| `mcp__sourcegraph__sg_nls_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_list_repos` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_list_files` |

## Conversation Preview

Parsed from transcript using the same message categories as the dashboard trace parser.

| Seq | Type | Subtype | Tool | Text |
|---:|---|---|---|---|
| 1 | `system` | `init` | `-` | - |
| 2 | `assistant` | `text` | `-` | I'll help you trace the SSO settings feature control across all 4 layers in Grafana. This is a complex cross-cutting concern, so I'll use Deep Search to understand the architecture, then systematically find each critical... |
| 3 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_deepsearch` | - |
| 4 | `user` | `text` | `-` | - |
| 5 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_deepsearch_read` | - |
| 6 | `user` | `text` | `-` | - |
| 7 | `assistant` | `text` | `-` | Let me search directly for the key components across the layers: |
| 8 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 9 | `user` | `text` | `-` | - |
| 10 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 11 | `user` | `text` | `-` | - |
| 12 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 13 | `user` | `text` | `-` | - |
| 14 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 15 | `user` | `text` | `-` | - |
| 16 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_nls_search` | - |
| 17 | `user` | `text` | `-` | - |
| 18 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_nls_search` | - |
| 19 | `user` | `text` | `-` | - |
| 20 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 21 | `user` | `text` | `-` | - |
| 22 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_repos` | - |
| 23 | `user` | `text` | `-` | - |
| 24 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 25 | `user` | `text` | `-` | - |
| 26 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 27 | `user` | `text` | `-` | - |
| 28 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 29 | `user` | `text` | `-` | - |
| 30 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 31 | `user` | `text` | `-` | - |
| 32 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 33 | `user` | `text` | `-` | - |
| 34 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 35 | `user` | `text` | `-` | - |
| 36 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 37 | `user` | `text` | `-` | - |
| 38 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 39 | `user` | `text` | `-` | - |
| 40 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 41 | `user` | `text` | `-` | - |
| 42 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 43 | `user` | `text` | `-` | - |
| 44 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 45 | `user` | `text` | `-` | - |
| 46 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 47 | `user` | `text` | `-` | - |
| 48 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 49 | `user` | `text` | `-` | - |
| 50 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 51 | `user` | `text` | `-` | - |
| 52 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 53 | `user` | `text` | `-` | - |
| 54 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 55 | `user` | `text` | `-` | - |
| 56 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 57 | `user` | `text` | `-` | - |
| 58 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 59 | `user` | `text` | `-` | - |
| 60 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 61 | `user` | `text` | `-` | - |
| 62 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 63 | `user` | `text` | `-` | - |
| 64 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 65 | `user` | `text` | `-` | - |
| 66 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 67 | `user` | `text` | `-` | - |
| 68 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 69 | `user` | `text` | `-` | - |
| 70 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 71 | `user` | `text` | `-` | - |
| 72 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_nls_search` | - |
| 73 | `user` | `text` | `-` | - |
| 74 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 75 | `user` | `text` | `-` | - |
| 76 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_nls_search` | - |
| 77 | `user` | `text` | `-` | - |
| 78 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 79 | `user` | `text` | `-` | - |
| 80 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
