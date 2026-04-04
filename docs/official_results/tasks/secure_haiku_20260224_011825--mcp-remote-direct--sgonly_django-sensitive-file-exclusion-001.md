# sgonly_django-sensitive-file-exclusion-001 (mcp-remote-direct)

- Run: `secure_haiku_20260224_011825`
- Status: `passed`
- Reward: `1.0000`
- Audit JSON: [link](../audits/secure_haiku_20260224_011825--mcp-remote-direct--sgonly_django-sensitive-file-exclusion-001.json)
- Trajectory available: `True`
- Transcript available: `True`
- Bundled trajectory: [link](../traces/secure_haiku_20260224_011825--mcp-remote-direct--sgonly_django-sensitive-file-exclusion-001/trajectory.json)
- Bundled transcript: [link](../traces/secure_haiku_20260224_011825--mcp-remote-direct--sgonly_django-sensitive-file-exclusion-001/claude-code.txt)

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 923.1 |
| Agent execution seconds | 645.4 |
| Input tokens | 14,926,678 |
| Output tokens | 425 |
| Cache tokens | 14,925,976 |
| Tool calls (total) | 76 |
| Tool calls (MCP) | 28 |
| Tool calls (local) | 48 |
| MCP ratio | 0.368 |
| keyword_search calls | 7 |
| nls_search calls | 0 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `f7d99fa048961f3186507d584c0de9a6b8390808f35bc7fde1f1eecec69e7940` |
| `trajectory.json` SHA256 | `559814f6d5c284ef5e617c19dd4e391580ee3f6ec6fc62f0249ee0111f7f1b86` |
| transcript SHA256 | `c24b4e3cc62e44bd63490bd175299e8df926a269105f97c105503714e1f05d80` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `Bash` | 41 |
| `mcp__sourcegraph__sg_read_file` | 13 |
| `mcp__sourcegraph__sg_keyword_search` | 7 |
| `mcp__sourcegraph__sg_list_files` | 6 |
| `Write` | 5 |
| `Edit` | 2 |
| `mcp__sourcegraph__sg_find_references` | 2 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_find_references` |

## Conversation Preview

Parsed from transcript using the same message categories as the dashboard trace parser.

| Seq | Type | Subtype | Tool | Text |
|---:|---|---|---|---|
| 1 | `system` | `init` | `-` | - |
| 2 | `assistant` | `text` | `-` | I'll help you fix the persistent database connections bug in Django. Let me start by understanding the repository structure and running the tests to see what's failing. |
| 3 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 4 | `user` | `text` | `-` | - |
| 5 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 6 | `user` | `text` | `-` | - |
| 7 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 8 | `user` | `text` | `-` | - |
| 9 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 10 | `user` | `text` | `-` | - |
| 11 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 12 | `user` | `text` | `-` | - |
| 13 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 14 | `user` | `text` | `-` | - |
| 15 | `assistant` | `text` | `-` | Let me search for test files related to database connections: |
| 16 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 17 | `user` | `text` | `-` | - |
| 18 | `assistant` | `text` | `-` | Now let me search for tests related to persistent connections or connection lifecycle: |
| 19 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 20 | `user` | `text` | `-` | - |
| 21 | `assistant` | `text` | `-` | Now let me read the base database backend file where the connection lifecycle is managed: |
| 22 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 23 | `user` | `text` | `-` | - |
| 24 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 25 | `user` | `text` | `-` | - |
| 26 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 27 | `user` | `text` | `-` | - |
| 28 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_find_references` | - |
| 29 | `user` | `text` | `-` | - |
| 30 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 31 | `user` | `text` | `-` | - |
| 32 | `assistant` | `text` | `-` | Let me run the test suite first to see what's failing: |
| 33 | `assistant` | `tool_use` | `Bash` | - |
| 34 | `user` | `text` | `-` | - |
| 35 | `assistant` | `tool_use` | `Bash` | - |
| 36 | `user` | `text` | `-` | - |
| 37 | `assistant` | `tool_use` | `Bash` | - |
| 38 | `user` | `text` | `-` | - |
| 39 | `assistant` | `tool_use` | `Bash` | - |
| 40 | `user` | `text` | `-` | - |
| 41 | `assistant` | `tool_use` | `Bash` | - |
| 42 | `user` | `text` | `-` | - |
| 43 | `assistant` | `tool_use` | `Bash` | - |
| 44 | `user` | `text` | `-` | - |
| 45 | `assistant` | `tool_use` | `Bash` | - |
| 46 | `user` | `text` | `-` | - |
| 47 | `assistant` | `tool_use` | `Bash` | - |
| 48 | `user` | `text` | `-` | - |
| 49 | `assistant` | `tool_use` | `Bash` | - |
| 50 | `user` | `text` | `-` | - |
| 51 | `assistant` | `tool_use` | `Bash` | - |
| 52 | `user` | `text` | `-` | - |
| 53 | `assistant` | `tool_use` | `Bash` | - |
| 54 | `user` | `text` | `-` | - |
| 55 | `assistant` | `tool_use` | `Bash` | - |
| 56 | `user` | `text` | `-` | - |
| 57 | `assistant` | `tool_use` | `Bash` | - |
| 58 | `user` | `text` | `-` | - |
| 59 | `assistant` | `tool_use` | `Bash` | - |
| 60 | `user` | `text` | `-` | - |
| 61 | `assistant` | `tool_use` | `Bash` | - |
| 62 | `user` | `text` | `-` | - |
| 63 | `assistant` | `tool_use` | `Bash` | - |
| 64 | `user` | `text` | `-` | - |
| 65 | `assistant` | `tool_use` | `Bash` | - |
| 66 | `user` | `text` | `-` | - |
| 67 | `assistant` | `text` | `-` | Let me search for where else `close_at` might be getting modified: |
| 68 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 69 | `user` | `text` | `-` | - |
| 70 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_find_references` | - |
| 71 | `user` | `text` | `-` | - |
| 72 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 73 | `user` | `text` | `-` | - |
| 74 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 75 | `user` | `text` | `-` | - |
| 76 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 77 | `user` | `text` | `-` | - |
| 78 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 79 | `user` | `text` | `-` | - |
| 80 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
