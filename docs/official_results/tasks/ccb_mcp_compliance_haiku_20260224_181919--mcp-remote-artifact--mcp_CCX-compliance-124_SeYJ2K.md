# mcp_CCX-compliance-124_SeYJ2K (mcp-remote-artifact)

- Run: `ccb_mcp_compliance_haiku_20260224_181919`
- Status: `passed`
- Reward: `0.7419`
- Audit JSON: [link](../audits/ccb_mcp_compliance_haiku_20260224_181919--mcp-remote-artifact--mcp_CCX-compliance-124_SeYJ2K.json)
- Trajectory available: `True`
- Transcript available: `True`
- Bundled trajectory: [link](../traces/ccb_mcp_compliance_haiku_20260224_181919--mcp-remote-artifact--mcp_CCX-compliance-124_SeYJ2K/trajectory.json)
- Bundled transcript: [link](../traces/ccb_mcp_compliance_haiku_20260224_181919--mcp-remote-artifact--mcp_CCX-compliance-124_SeYJ2K/claude-code.txt)

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 115.8 |
| Agent execution seconds | 68.0 |
| Input tokens | 2,348,490 |
| Output tokens | 83 |
| Cache tokens | 2,348,069 |
| Tool calls (total) | 20 |
| Tool calls (MCP) | 19 |
| Tool calls (local) | 1 |
| MCP ratio | 0.950 |
| keyword_search calls | 8 |
| nls_search calls | 2 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `e30478ab3d191fc3c6511231b6aa0d0e2d5efa5456e8126f5ef75a7798cb2a19` |
| `trajectory.json` SHA256 | `8389f9efc2b167b54e3832be94fa25d177140f47dd18a364a6bcebc5cd995e3c` |
| transcript SHA256 | `b9739f3890c478d81477adf9e5fbbb44bf438b82a59b3cc0f174572bcd83210a` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `mcp__sourcegraph__sg_keyword_search` | 8 |
| `mcp__sourcegraph__sg_read_file` | 8 |
| `mcp__sourcegraph__sg_nls_search` | 2 |
| `Write` | 1 |
| `mcp__sourcegraph__sg_list_files` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_nls_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_nls_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_keyword_search` |

## Conversation Preview

Parsed from transcript using the same message categories as the dashboard trace parser.

| Seq | Type | Subtype | Tool | Text |
|---:|---|---|---|---|
| 1 | `system` | `init` | `-` | - |
| 2 | `assistant` | `text` | `-` | I'll help you audit the CSP enforcement infrastructure in Firefox. Let me search for the relevant files in the `dom/security/` directory. |
| 3 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 4 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 5 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 6 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 7 | `user` | `text` | `-` | - |
| 8 | `user` | `text` | `-` | - |
| 9 | `user` | `text` | `-` | - |
| 10 | `user` | `text` | `-` | - |
| 11 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 12 | `user` | `text` | `-` | - |
| 13 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_nls_search` | - |
| 14 | `user` | `text` | `-` | - |
| 15 | `assistant` | `text` | `-` | Now let me search for the file that performs script-src evaluation for inline scripts: |
| 16 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 17 | `user` | `text` | `-` | - |
| 18 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_nls_search` | - |
| 19 | `user` | `text` | `-` | - |
| 20 | `assistant` | `text` | `-` | Let me read the key files to understand their structure and verify the primary classes: |
| 21 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 22 | `user` | `text` | `-` | - |
| 23 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 24 | `user` | `text` | `-` | - |
| 25 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 26 | `user` | `text` | `-` | - |
| 27 | `assistant` | `text` | `-` | Now let me check the nsCSPContext.cpp file to find script-src evaluation functions: |
| 28 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 29 | `user` | `text` | `-` | - |
| 30 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 31 | `user` | `text` | `-` | - |
| 32 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 33 | `user` | `text` | `-` | - |
| 34 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 35 | `user` | `text` | `-` | - |
| 36 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 37 | `user` | `text` | `-` | - |
| 38 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 39 | `user` | `text` | `-` | - |
| 40 | `assistant` | `text` | `-` | Now let me search for more details on inline script evaluation: |
| 41 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 42 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 43 | `user` | `text` | `-` | - |
| 44 | `user` | `text` | `-` | - |
| 45 | `assistant` | `text` | `-` | Now let me write the comprehensive analysis to the answer.json file: |
| 46 | `assistant` | `tool_use` | `Write` | - |
| 47 | `user` | `text` | `-` | - |
| 48 | `assistant` | `text` | `-` | Perfect! I've completed the CSP enforcement infrastructure audit for Firefox. Here's a summary of what I found:  ## Key Findings  I've identified all five major components of Firefox's CSP enforcement system in the `dom/... |
