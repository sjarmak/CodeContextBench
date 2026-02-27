# mcp_CCX-onboard-109_nCLIh8 (mcp-remote-direct)

- Run: `ccb_mcp_onboarding_haiku_20260226_035628_variance`
- Status: `passed`
- Reward: `0.9301`
- Audit JSON: [link](../audits/ccb_mcp_onboarding_haiku_20260226_035628_variance--mcp-remote-direct--mcp_CCX-onboard-109_nCLIh8.json)
- Trajectory available: `True`
- Transcript available: `True`
- Bundled trajectory: [link](../traces/ccb_mcp_onboarding_haiku_20260226_035628_variance--mcp-remote-direct--mcp_CCX-onboard-109_nCLIh8/trajectory.json)
- Bundled transcript: [link](../traces/ccb_mcp_onboarding_haiku_20260226_035628_variance--mcp-remote-direct--mcp_CCX-onboard-109_nCLIh8/claude-code.txt)

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 286.9 |
| Agent execution seconds | 52.7 |
| Input tokens | 1,124,445 |
| Output tokens | 5,487 |
| Cache tokens | 1,124,178 |
| Tool calls (total) | 14 |
| Tool calls (MCP) | 13 |
| Tool calls (local) | 1 |
| MCP ratio | 0.929 |
| keyword_search calls | - |
| nls_search calls | - |
| deepsearch calls | - |
| `result.json` SHA256 | `dbe40270de40fcf325732bec1d103ecadc97f87ae856e0642e7b7b135199d0ba` |
| `trajectory.json` SHA256 | `0a5cf4b8d6003447aa65c98f20fc92a241e1954cf6aceb97503ac4789f8a8da0` |
| transcript SHA256 | `bb503884e7a3f331be2d58f80c3d4f9282b3cb5b7096094cb075d76e1e80c155` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `mcp__sourcegraph__sg_read_file` | 8 |
| `mcp__sourcegraph__sg_keyword_search` | 5 |
| `Write` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |

## Conversation Preview

Parsed from transcript using the same message categories as the dashboard trace parser.

| Seq | Type | Subtype | Tool | Text |
|---:|---|---|---|---|
| 1 | `system` | `init` | `-` | - |
| 2 | `assistant` | `text` | `-` | I'll help you find these key SpiderMonkey JIT compilation pipeline files. Let me search the Firefox repository for these specific symbols and files. |
| 3 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 4 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 5 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 6 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 7 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 8 | `user` | `text` | `-` | - |
| 9 | `user` | `text` | `-` | - |
| 10 | `user` | `text` | `-` | - |
| 11 | `user` | `text` | `-` | - |
| 12 | `user` | `text` | `-` | - |
| 13 | `assistant` | `text` | `-` | Perfect! I found the key files. Let me read them to get the exact details and confirm their content: |
| 14 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 15 | `user` | `text` | `-` | - |
| 16 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 17 | `user` | `text` | `-` | - |
| 18 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 19 | `user` | `text` | `-` | - |
| 20 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 21 | `user` | `text` | `-` | - |
| 22 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 23 | `user` | `text` | `-` | - |
| 24 | `assistant` | `text` | `-` | Let me also verify the IonCompileTask.cpp file: |
| 25 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 26 | `user` | `text` | `-` | - |
| 27 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 28 | `user` | `text` | `-` | - |
| 29 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 30 | `user` | `text` | `-` | - |
| 31 | `assistant` | `text` | `-` | Perfect! I've found all the key SpiderMonkey JIT compilation pipeline files. Let me create the answer.json file with my findings: |
| 32 | `assistant` | `tool_use` | `Write` | - |
| 33 | `user` | `text` | `-` | - |
| 34 | `assistant` | `text` | `-` | Perfect! I've identified all the key C++ source files in Firefox's SpiderMonkey JavaScript engine that define the JIT compilation pipeline stages. Here's a summary of my findings:  ## SpiderMonkey JIT Compilation Pipelin... |
