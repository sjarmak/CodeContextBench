# sgonly_django-policy-enforcement-001 (mcp-remote-direct)

- Run: `csb_sdlc_secure_haiku_022326`
- Status: `passed`
- Reward: `0.7500`
- Audit JSON: [link](../audits/csb_sdlc_secure_haiku_022326--mcp--sgonly_django-policy-enforcement-001.json)
- Trajectory available: `True`
- Transcript available: `True`
- Bundled trajectory: [link](../traces/csb_sdlc_secure_haiku_022326--mcp--sgonly_django-policy-enforcement-001/trajectory.json)
- Bundled transcript: [link](../traces/csb_sdlc_secure_haiku_022326--mcp--sgonly_django-policy-enforcement-001/claude-code.txt)

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 367.4 |
| Agent execution seconds | 223.3 |
| Input tokens | 7,388,980 |
| Output tokens | 381 |
| Cache tokens | 7,388,551 |
| Tool calls (total) | 63 |
| Tool calls (MCP) | 13 |
| Tool calls (local) | 50 |
| MCP ratio | 0.206 |
| keyword_search calls | 6 |
| nls_search calls | 0 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `a65fc867dc0b556f3c5a857fb730ec5eb9c4b16e5a7c74b2aad822629f7bb1bd` |
| `trajectory.json` SHA256 | `d8f37f495ca9e511ba83104e530df764d5e78ac19ef5f0baaf5ba53f285d40ca` |
| transcript SHA256 | `327f553c4b1a253041251054d617a4d37a3fce8e971b56ad0236b561e133b769` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `Bash` | 29 |
| `Edit` | 6 |
| `Read` | 6 |
| `mcp__sourcegraph__sg_keyword_search` | 6 |
| `TodoWrite` | 5 |
| `mcp__sourcegraph__sg_list_files` | 4 |
| `Write` | 3 |
| `mcp__sourcegraph__sg_read_file` | 3 |
| `TaskOutput` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `TodoWrite` |
| `mcp__sourcegraph__sg_list_files` |
| `Bash` |
| `Bash` |
| `Bash` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `Bash` |

## Conversation Preview

Parsed from transcript using the same message categories as the dashboard trace parser.

| Seq | Type | Subtype | Tool | Text |
|---:|---|---|---|---|
| 1 | `system` | `init` | `-` | - |
| 2 | `assistant` | `text` | `-` | I'll help you implement a bulk soft-delete manager for Django ORM. Following the evaluation workflow, let me start by understanding the test suite and what's expected. |
| 3 | `assistant` | `tool_use` | `TodoWrite` | - |
| 4 | `user` | `text` | `-` | - |
| 5 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 6 | `user` | `text` | `-` | - |
| 7 | `assistant` | `tool_use` | `Bash` | - |
| 8 | `user` | `text` | `-` | - |
| 9 | `assistant` | `tool_use` | `Bash` | - |
| 10 | `user` | `text` | `-` | - |
| 11 | `assistant` | `tool_use` | `Bash` | - |
| 12 | `user` | `text` | `-` | - |
| 13 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 14 | `user` | `text` | `-` | - |
| 15 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 16 | `user` | `text` | `-` | - |
| 17 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 18 | `user` | `text` | `-` | - |
| 19 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 20 | `user` | `text` | `-` | - |
| 21 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 22 | `user` | `text` | `-` | - |
| 23 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 24 | `user` | `text` | `-` | - |
| 25 | `assistant` | `tool_use` | `Bash` | - |
| 26 | `user` | `text` | `-` | - |
| 27 | `assistant` | `tool_use` | `Bash` | - |
| 28 | `user` | `text` | `-` | - |
| 29 | `assistant` | `tool_use` | `Bash` | - |
| 30 | `user` | `text` | `-` | - |
| 31 | `assistant` | `tool_use` | `Bash` | - |
| 32 | `user` | `text` | `-` | - |
| 33 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 34 | `user` | `text` | `-` | - |
| 35 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 36 | `user` | `text` | `-` | - |
| 37 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 38 | `user` | `text` | `-` | - |
| 39 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 40 | `user` | `text` | `-` | - |
| 41 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 42 | `user` | `text` | `-` | - |
| 43 | `assistant` | `tool_use` | `Bash` | - |
| 44 | `user` | `text` | `-` | - |
| 45 | `assistant` | `tool_use` | `Bash` | - |
| 46 | `user` | `text` | `-` | - |
| 47 | `assistant` | `tool_use` | `Bash` | - |
| 48 | `user` | `text` | `-` | - |
| 49 | `assistant` | `tool_use` | `TaskOutput` | - |
| 50 | `user` | `text` | `-` | - |
| 51 | `assistant` | `tool_use` | `Bash` | - |
| 52 | `user` | `text` | `-` | - |
| 53 | `assistant` | `tool_use` | `Bash` | - |
| 54 | `user` | `text` | `-` | - |
| 55 | `assistant` | `tool_use` | `Bash` | - |
| 56 | `user` | `text` | `-` | - |
| 57 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 58 | `user` | `text` | `-` | - |
| 59 | `assistant` | `tool_use` | `Bash` | - |
| 60 | `user` | `text` | `-` | - |
| 61 | `assistant` | `tool_use` | `Bash` | - |
| 62 | `user` | `text` | `-` | - |
| 63 | `assistant` | `tool_use` | `TodoWrite` | - |
| 64 | `user` | `text` | `-` | - |
| 65 | `assistant` | `tool_use` | `Read` | - |
| 66 | `user` | `text` | `-` | - |
| 67 | `assistant` | `text` | `-` | Now let me implement the SoftDeleteManager. First, I'll understand what the requirements are by looking at existing patterns and then add the new manager class. |
| 68 | `assistant` | `tool_use` | `Read` | - |
| 69 | `user` | `text` | `-` | - |
| 70 | `assistant` | `tool_use` | `TodoWrite` | - |
| 71 | `user` | `text` | `-` | - |
| 72 | `assistant` | `tool_use` | `Edit` | - |
| 73 | `user` | `text` | `-` | - |
| 74 | `assistant` | `tool_use` | `Edit` | - |
| 75 | `user` | `text` | `-` | - |
| 76 | `assistant` | `tool_use` | `Edit` | - |
| 77 | `user` | `text` | `-` | - |
| 78 | `assistant` | `tool_use` | `Edit` | - |
| 79 | `user` | `text` | `-` | - |
| 80 | `assistant` | `tool_use` | `Bash` | - |
