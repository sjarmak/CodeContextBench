# sgonly_test-coverage-gap-002 (mcp-remote-direct)

- Run: `ccb_test_haiku_022326`
- Status: `passed`
- Reward: `1.0000`
- Audit JSON: [link](../audits/ccb_test_haiku_022326--mcp--sgonly_test-coverage-gap-002.json)
- Trajectory available: `True`
- Transcript available: `True`
- Bundled trajectory: [link](../traces/ccb_test_haiku_022326--mcp--sgonly_test-coverage-gap-002/trajectory.json)
- Bundled transcript: [link](../traces/ccb_test_haiku_022326--mcp--sgonly_test-coverage-gap-002/claude-code.txt)

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 217.9 |
| Agent execution seconds | 106.9 |
| Input tokens | 2,787,860 |
| Output tokens | 74 |
| Cache tokens | 2,787,300 |
| Tool calls (total) | 28 |
| Tool calls (MCP) | 27 |
| Tool calls (local) | 1 |
| MCP ratio | 0.964 |
| keyword_search calls | 5 |
| nls_search calls | 2 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `b95e0f4ceead4e2464b2cbc114add023b28e7a934774a43e708d19d7b5bab4a4` |
| `trajectory.json` SHA256 | `dfdf5e20df85a7eb23cbb59ffa780b5a2fafa560fde263237b79a09932c8bad9` |
| transcript SHA256 | `c76c1937de42bd9d28686ef43551b895cba22303a5590f6bfbb10fa5481fe593` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `mcp__sourcegraph__sg_read_file` | 15 |
| `mcp__sourcegraph__sg_keyword_search` | 5 |
| `mcp__sourcegraph__sg_list_files` | 5 |
| `mcp__sourcegraph__sg_nls_search` | 2 |
| `Write` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |

## Conversation Preview

Parsed from transcript using the same message categories as the dashboard trace parser.

| Seq | Type | Subtype | Tool | Text |
|---:|---|---|---|---|
| 1 | `system` | `init` | `-` | - |
| 2 | `assistant` | `text` | `-` | I'll help you identify test coverage gaps in the Kafka consumer group coordinator. Let me start by exploring the repository structure and reading the actual source files. |
| 3 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 4 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 5 | `user` | `text` | `-` | - |
| 6 | `user` | `text` | `-` | - |
| 7 | `assistant` | `text` | `-` | Let me search more broadly for the coordinator files: |
| 8 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 9 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 10 | `user` | `text` | `-` | - |
| 11 | `user` | `text` | `-` | - |
| 12 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 13 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 14 | `user` | `text` | `-` | - |
| 15 | `user` | `text` | `-` | - |
| 16 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 17 | `user` | `text` | `-` | - |
| 18 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 19 | `user` | `text` | `-` | - |
| 20 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 21 | `user` | `text` | `-` | - |
| 22 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 23 | `user` | `text` | `-` | - |
| 24 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 25 | `user` | `text` | `-` | - |
| 26 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 27 | `user` | `text` | `-` | - |
| 28 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 29 | `user` | `text` | `-` | - |
| 30 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 31 | `user` | `text` | `-` | - |
| 32 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 33 | `user` | `text` | `-` | - |
| 34 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 35 | `user` | `text` | `-` | - |
| 36 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 37 | `user` | `text` | `-` | - |
| 38 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 39 | `user` | `text` | `-` | - |
| 40 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 41 | `user` | `text` | `-` | - |
| 42 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 43 | `user` | `text` | `-` | - |
| 44 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_nls_search` | - |
| 45 | `user` | `text` | `-` | - |
| 46 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_nls_search` | - |
| 47 | `user` | `text` | `-` | - |
| 48 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 49 | `user` | `text` | `-` | - |
| 50 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 51 | `user` | `text` | `-` | - |
| 52 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 53 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 54 | `user` | `text` | `-` | - |
| 55 | `user` | `text` | `-` | - |
| 56 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 57 | `user` | `text` | `-` | - |
| 58 | `assistant` | `text` | `-` | Now I have a good understanding of the Kafka consumer group coordinator codebase. Let me create a comprehensive test coverage gap analysis. |
| 59 | `assistant` | `tool_use` | `Write` | - |
| 60 | `user` | `text` | `-` | - |
| 61 | `assistant` | `text` | `-` | Perfect! I've completed the test coverage gap analysis for the Kafka consumer group coordinator. The analysis has been written to `/workspace/coverage_analysis.md`.  ## Summary  The analysis identifies **6 specific failu... |
