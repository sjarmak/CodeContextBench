# sgonly_openlibrary-search-query-fix-001 (mcp-remote-direct)

- Run: `fix_haiku_20260223_171232`
- Status: `failed`
- Reward: `0.0000`
- Audit JSON: [link](../audits/fix_haiku_20260223_171232--mcp-remote-direct--sgonly_openlibrary-search-query-fix-001.json)
- Trajectory available: `True`
- Transcript available: `True`
- Bundled trajectory: [link](../traces/fix_haiku_20260223_171232--mcp-remote-direct--sgonly_openlibrary-search-query-fix-001/trajectory.json)
- Bundled transcript: [link](../traces/fix_haiku_20260223_171232--mcp-remote-direct--sgonly_openlibrary-search-query-fix-001/claude-code.txt)

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 942.6 |
| Agent execution seconds | 816.4 |
| Input tokens | 25,177,048 |
| Output tokens | 575 |
| Cache tokens | 25,175,990 |
| Tool calls (total) | 111 |
| Tool calls (MCP) | 17 |
| Tool calls (local) | 94 |
| MCP ratio | 0.153 |
| keyword_search calls | 5 |
| nls_search calls | 0 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `657d18697bcc356ef2f775def486825015f5e430ad6b56740f1f1502a2eb3bda` |
| `trajectory.json` SHA256 | `e1b27086f8320d34293ba23bedefb829d897859d18b7cb431a00aa62d2e91536` |
| transcript SHA256 | `03a8cddbbccee48057ff6669b106485664afdf0115cf53f5d2857239424eff43` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `Bash` | 50 |
| `Edit` | 18 |
| `Write` | 15 |
| `mcp__sourcegraph__sg_read_file` | 9 |
| `Read` | 7 |
| `mcp__sourcegraph__sg_keyword_search` | 5 |
| `TodoWrite` | 4 |
| `mcp__sourcegraph__sg_list_files` | 2 |
| `mcp__sourcegraph__sg_list_repos` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_list_repos` |
| `TodoWrite` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `Bash` |

## Conversation Preview

Parsed from transcript using the same message categories as the dashboard trace parser.

| Seq | Type | Subtype | Tool | Text |
|---:|---|---|---|---|
| 1 | `system` | `init` | `-` | - |
| 2 | `assistant` | `text` | `-` | I'll help you fix the work search query processing issue. Let me start by exploring the codebase to understand the architecture and locate the relevant code. |
| 3 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_repos` | - |
| 4 | `assistant` | `tool_use` | `TodoWrite` | - |
| 5 | `user` | `text` | `-` | - |
| 6 | `user` | `text` | `-` | - |
| 7 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 8 | `user` | `text` | `-` | - |
| 9 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 10 | `user` | `text` | `-` | - |
| 11 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 12 | `user` | `text` | `-` | - |
| 13 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 14 | `user` | `text` | `-` | - |
| 15 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 16 | `user` | `text` | `-` | - |
| 17 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 18 | `user` | `text` | `-` | - |
| 19 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 20 | `user` | `text` | `-` | - |
| 21 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 22 | `user` | `text` | `-` | - |
| 23 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 24 | `user` | `text` | `-` | - |
| 25 | `assistant` | `text` | `-` | Now let me update my todo and look at the issue more closely. Let me first run the tests to see what's failing: |
| 26 | `assistant` | `tool_use` | `Bash` | - |
| 27 | `user` | `text` | `-` | - |
| 28 | `assistant` | `text` | `-` | Let me check the workspace structure: |
| 29 | `assistant` | `tool_use` | `Bash` | - |
| 30 | `user` | `text` | `-` | - |
| 31 | `assistant` | `tool_use` | `Bash` | - |
| 32 | `user` | `text` | `-` | - |
| 33 | `assistant` | `tool_use` | `Write` | - |
| 34 | `user` | `text` | `-` | - |
| 35 | `assistant` | `tool_use` | `Bash` | - |
| 36 | `user` | `text` | `-` | - |
| 37 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 38 | `user` | `text` | `-` | - |
| 39 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 40 | `user` | `text` | `-` | - |
| 41 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 42 | `user` | `text` | `-` | - |
| 43 | `assistant` | `tool_use` | `Write` | - |
| 44 | `user` | `text` | `-` | - |
| 45 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 46 | `user` | `text` | `-` | - |
| 47 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 48 | `user` | `text` | `-` | - |
| 49 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 50 | `user` | `text` | `-` | - |
| 51 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 52 | `user` | `text` | `-` | - |
| 53 | `assistant` | `tool_use` | `Write` | - |
| 54 | `user` | `text` | `-` | - |
| 55 | `assistant` | `tool_use` | `Write` | - |
| 56 | `user` | `text` | `-` | - |
| 57 | `assistant` | `tool_use` | `Write` | - |
| 58 | `user` | `text` | `-` | - |
| 59 | `assistant` | `tool_use` | `Write` | - |
| 60 | `user` | `text` | `-` | - |
| 61 | `assistant` | `tool_use` | `Write` | - |
| 62 | `user` | `text` | `-` | - |
| 63 | `assistant` | `tool_use` | `Write` | - |
| 64 | `user` | `text` | `-` | - |
| 65 | `assistant` | `tool_use` | `Write` | - |
| 66 | `user` | `text` | `-` | - |
| 67 | `assistant` | `tool_use` | `Write` | - |
| 68 | `user` | `text` | `-` | - |
| 69 | `assistant` | `tool_use` | `Write` | - |
| 70 | `user` | `text` | `-` | - |
| 71 | `assistant` | `tool_use` | `Write` | - |
| 72 | `user` | `text` | `-` | - |
| 73 | `assistant` | `tool_use` | `Write` | - |
| 74 | `user` | `text` | `-` | - |
| 75 | `assistant` | `tool_use` | `Write` | - |
| 76 | `user` | `text` | `-` | - |
| 77 | `assistant` | `tool_use` | `Write` | - |
| 78 | `user` | `text` | `-` | - |
| 79 | `assistant` | `tool_use` | `Bash` | - |
| 80 | `user` | `text` | `-` | - |
