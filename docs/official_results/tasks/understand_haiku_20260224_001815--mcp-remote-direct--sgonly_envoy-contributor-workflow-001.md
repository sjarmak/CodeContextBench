# sgonly_envoy-contributor-workflow-001 (mcp-remote-direct)

- Run: `understand_haiku_20260224_001815`
- Status: `passed`
- Reward: `0.9100`
- Audit JSON: [link](../audits/understand_haiku_20260224_001815--mcp-remote-direct--sgonly_envoy-contributor-workflow-001.json)
- Trajectory available: `True`
- Transcript available: `True`
- Bundled trajectory: [link](../traces/understand_haiku_20260224_001815--mcp-remote-direct--sgonly_envoy-contributor-workflow-001/trajectory.json)
- Bundled transcript: [link](../traces/understand_haiku_20260224_001815--mcp-remote-direct--sgonly_envoy-contributor-workflow-001/claude-code.txt)

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 265.2 |
| Agent execution seconds | 120.0 |
| Input tokens | 2,164,909 |
| Output tokens | 123 |
| Cache tokens | 2,164,486 |
| Tool calls (total) | 22 |
| Tool calls (MCP) | 21 |
| Tool calls (local) | 1 |
| MCP ratio | 0.955 |
| keyword_search calls | 3 |
| nls_search calls | 0 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `fd5f7559cff4872523948d2c0cd1560b1a37034bb6f5a1d7f1d9281684a50b1b` |
| `trajectory.json` SHA256 | `8097d867b15ffe9f54d740609b922c8e8d327b45d7839472c5c7ba084f1a2fb2` |
| transcript SHA256 | `846227626736242982a78f074cea97bf31340b01c5c580351bd14a09cdb80faf` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `mcp__sourcegraph__sg_read_file` | 13 |
| `mcp__sourcegraph__sg_list_files` | 5 |
| `mcp__sourcegraph__sg_keyword_search` | 3 |
| `Write` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_read_file` |

## Conversation Preview

Parsed from transcript using the same message categories as the dashboard trace parser.

| Seq | Type | Subtype | Tool | Text |
|---:|---|---|---|---|
| 1 | `system` | `init` | `-` | - |
| 2 | `assistant` | `text` | `-` | I'll help you explore the Envoy repository and create a comprehensive contributor guide. Let me start by discovering the repository structure and key documentation files. |
| 3 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 4 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 5 | `user` | `text` | `-` | - |
| 6 | `user` | `text` | `-` | - |
| 7 | `assistant` | `text` | `-` | Great! I can see this is using Bazel as the build system. Let me read the key documentation files to understand the workflow. |
| 8 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 9 | `user` | `text` | `-` | - |
| 10 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 11 | `user` | `text` | `-` | - |
| 12 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 13 | `user` | `text` | `-` | - |
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
| 24 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 25 | `user` | `text` | `-` | - |
| 26 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 27 | `user` | `text` | `-` | - |
| 28 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 29 | `user` | `text` | `-` | - |
| 30 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 31 | `user` | `text` | `-` | - |
| 32 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 33 | `user` | `text` | `-` | - |
| 34 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 35 | `user` | `text` | `-` | - |
| 36 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 37 | `user` | `text` | `-` | - |
| 38 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 39 | `user` | `text` | `-` | - |
| 40 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 41 | `user` | `text` | `-` | - |
| 42 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 43 | `user` | `text` | `-` | - |
| 44 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 45 | `user` | `text` | `-` | - |
| 46 | `assistant` | `text` | `-` | Perfect! I now have comprehensive information about the Envoy contributor workflow. Let me create the detailed contributor guide. |
| 47 | `assistant` | `tool_use` | `Write` | - |
| 48 | `user` | `text` | `-` | - |
| 49 | `assistant` | `text` | `-` | Perfect! I've successfully created a comprehensive Envoy contributor guide. Here's what I've documented:  ## Summary of the Contributor Guide  I've written `/logs/agent/onboarding.md` covering all the essential workflow ... |
