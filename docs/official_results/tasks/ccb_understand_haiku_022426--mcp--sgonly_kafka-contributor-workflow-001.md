# sgonly_kafka-contributor-workflow-001 (mcp-remote-direct)

- Run: `csb_sdlc_understand_haiku_022426`
- Status: `passed`
- Reward: `0.8200`
- Audit JSON: [link](../audits/csb_sdlc_understand_haiku_022426--mcp--sgonly_kafka-contributor-workflow-001.json)
- Trajectory available: `True`
- Transcript available: `True`
- Bundled trajectory: [link](../traces/csb_sdlc_understand_haiku_022426--mcp--sgonly_kafka-contributor-workflow-001/trajectory.json)
- Bundled transcript: [link](../traces/csb_sdlc_understand_haiku_022426--mcp--sgonly_kafka-contributor-workflow-001/claude-code.txt)

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 203.8 |
| Agent execution seconds | 92.8 |
| Input tokens | 1,591,307 |
| Output tokens | 114 |
| Cache tokens | 1,590,900 |
| Tool calls (total) | 22 |
| Tool calls (MCP) | 21 |
| Tool calls (local) | 1 |
| MCP ratio | 0.955 |
| keyword_search calls | 5 |
| nls_search calls | 0 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `a4194c98d1f7a4df212bb18603002e706aa26490cba7edbc9d7656150365b54c` |
| `trajectory.json` SHA256 | `afc27f445227628e94132bda19a430561ba6347f64f81ebf618d173b1b025678` |
| transcript SHA256 | `bf88e586fc40892f6e3871f1d604220bbd0c106683a0cad795fc720c2ecd0e37` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `mcp__sourcegraph__sg_read_file` | 10 |
| `mcp__sourcegraph__sg_list_files` | 6 |
| `mcp__sourcegraph__sg_keyword_search` | 5 |
| `Write` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_keyword_search` |

## Conversation Preview

Parsed from transcript using the same message categories as the dashboard trace parser.

| Seq | Type | Subtype | Tool | Text |
|---:|---|---|---|---|
| 1 | `system` | `init` | `-` | - |
| 2 | `assistant` | `text` | `-` | I'll help you create a comprehensive contributor guide for Kafka. Let me explore the repository to discover the build system, testing setup, CI pipeline, and code review process. |
| 3 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 4 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 5 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 6 | `user` | `text` | `-` | - |
| 7 | `user` | `text` | `-` | - |
| 8 | `user` | `text` | `-` | - |
| 9 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 10 | `user` | `text` | `-` | - |
| 11 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 12 | `user` | `text` | `-` | - |
| 13 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 14 | `user` | `text` | `-` | - |
| 15 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 16 | `user` | `text` | `-` | - |
| 17 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 18 | `user` | `text` | `-` | - |
| 19 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 20 | `user` | `text` | `-` | - |
| 21 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 22 | `user` | `text` | `-` | - |
| 23 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 24 | `user` | `text` | `-` | - |
| 25 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 26 | `user` | `text` | `-` | - |
| 27 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 28 | `user` | `text` | `-` | - |
| 29 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 30 | `user` | `text` | `-` | - |
| 31 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 32 | `user` | `text` | `-` | - |
| 33 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 34 | `user` | `text` | `-` | - |
| 35 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 36 | `user` | `text` | `-` | - |
| 37 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 38 | `user` | `text` | `-` | - |
| 39 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 40 | `user` | `text` | `-` | - |
| 41 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 42 | `user` | `text` | `-` | - |
| 43 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 44 | `user` | `text` | `-` | - |
| 45 | `assistant` | `text` | `-` | Now let me create a comprehensive contributor guide based on all the information I've gathered: |
| 46 | `assistant` | `tool_use` | `Write` | - |
| 47 | `user` | `text` | `-` | - |
| 48 | `assistant` | `text` | `-` | Perfect! I've created a comprehensive contributor guide for Apache Kafka at `/logs/agent/onboarding.md`. Here's what's included:  ## Summary  The guide covers all six requested areas with specific, actionable information... |
