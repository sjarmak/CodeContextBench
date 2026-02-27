# mcp_CCX-onboard-109_OSHkLJ (mcp-remote-direct)

- Run: `ccb_mcp_onboarding_haiku_20260226_035617`
- Status: `passed`
- Reward: `0.8155`
- Audit JSON: [link](../audits/ccb_mcp_onboarding_haiku_20260226_035617--mcp-remote-direct--mcp_CCX-onboard-109_OSHkLJ.json)
- Trajectory available: `True`
- Transcript available: `True`
- Bundled trajectory: [link](../traces/ccb_mcp_onboarding_haiku_20260226_035617--mcp-remote-direct--mcp_CCX-onboard-109_OSHkLJ/trajectory.json)
- Bundled transcript: [link](../traces/ccb_mcp_onboarding_haiku_20260226_035617--mcp-remote-direct--mcp_CCX-onboard-109_OSHkLJ/claude-code.txt)

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 274.0 |
| Agent execution seconds | 63.2 |
| Input tokens | 1,361,286 |
| Output tokens | 5,602 |
| Cache tokens | 1,360,968 |
| Tool calls (total) | 17 |
| Tool calls (MCP) | 16 |
| Tool calls (local) | 1 |
| MCP ratio | 0.941 |
| keyword_search calls | 3 |
| nls_search calls | 0 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `211ec39a2f99ae264cf4737c8da8b0587089e21353b201e59bee97cc5ec08712` |
| `trajectory.json` SHA256 | `acfd7a35be513575941db9fd50e8f8f1498cb2f2e083612f7c4990c527746954` |
| transcript SHA256 | `bddca7e840239f835e5a283dd1d32154d50bd6332336b66ba7107cccac101073` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `mcp__sourcegraph__sg_read_file` | 11 |
| `mcp__sourcegraph__sg_keyword_search` | 3 |
| `Write` | 1 |
| `mcp__sourcegraph__sg_list_files` | 1 |
| `mcp__sourcegraph__sg_list_repos` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_list_repos` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_keyword_search` |

## Conversation Preview

Parsed from transcript using the same message categories as the dashboard trace parser.

| Seq | Type | Subtype | Tool | Text |
|---:|---|---|---|---|
| 1 | `system` | `init` | `-` | - |
| 2 | `assistant` | `text` | `-` | I'll help you find all the key C++ source files in Firefox's SpiderMonkey JIT compilation pipeline. Let me search for these files systematically using Sourcegraph MCP tools. |
| 3 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_repos` | - |
| 4 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 5 | `user` | `text` | `-` | - |
| 6 | `user` | `text` | `-` | - |
| 7 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 8 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 9 | `user` | `text` | `-` | - |
| 10 | `user` | `text` | `-` | - |
| 11 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 12 | `user` | `text` | `-` | - |
| 13 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 14 | `user` | `text` | `-` | - |
| 15 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 16 | `user` | `text` | `-` | - |
| 17 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 18 | `user` | `text` | `-` | - |
| 19 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 20 | `user` | `text` | `-` | - |
| 21 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 22 | `user` | `text` | `-` | - |
| 23 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 24 | `user` | `text` | `-` | - |
| 25 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 26 | `user` | `text` | `-` | - |
| 27 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 28 | `user` | `text` | `-` | - |
| 29 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 30 | `user` | `text` | `-` | - |
| 31 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 32 | `user` | `text` | `-` | - |
| 33 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 34 | `user` | `text` | `-` | - |
| 35 | `assistant` | `text` | `-` | Perfect! I've found all the key C++ files in Firefox's SpiderMonkey JIT compilation pipeline. Let me create a comprehensive answer document. |
| 36 | `assistant` | `tool_use` | `Write` | - |
| 37 | `user` | `text` | `-` | - |
| 38 | `assistant` | `text` | `-` | Perfect! I've created a comprehensive answer document analyzing Firefox's SpiderMonkey JIT compilation pipeline. Here's a summary of what I found:  ## Key Findings  I've identified all 5 major C++ components in the JIT c... |
