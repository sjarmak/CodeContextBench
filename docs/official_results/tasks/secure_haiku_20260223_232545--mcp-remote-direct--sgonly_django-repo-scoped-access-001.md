# sgonly_django-repo-scoped-access-001 (mcp-remote-direct)

- Run: `secure_haiku_20260223_232545`
- Status: `passed`
- Reward: `0.7000`
- Audit JSON: [link](../audits/secure_haiku_20260223_232545--mcp-remote-direct--sgonly_django-repo-scoped-access-001.json)
- Trajectory available: `True`
- Transcript available: `True`
- Bundled trajectory: [link](../traces/secure_haiku_20260223_232545--mcp-remote-direct--sgonly_django-repo-scoped-access-001/trajectory.json)
- Bundled transcript: [link](../traces/secure_haiku_20260223_232545--mcp-remote-direct--sgonly_django-repo-scoped-access-001/claude-code.txt)

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 431.7 |
| Agent execution seconds | 349.0 |
| Input tokens | 15,237,220 |
| Output tokens | 462 |
| Cache tokens | 15,236,658 |
| Tool calls (total) | 98 |
| Tool calls (MCP) | 55 |
| Tool calls (local) | 43 |
| MCP ratio | 0.561 |
| keyword_search calls | 28 |
| nls_search calls | 3 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `45316721a1aa44ad1d74ebbf2bbe8f9770563dc4fc2f6d4023772cbc14f97fef` |
| `trajectory.json` SHA256 | `db6d186107270b018837b53d65159be70f306ccf064e42b35e81e192cca54f23` |
| transcript SHA256 | `d86516b224391431cb7897479a8e25df67f885e4dd530ddec872bffeddb3f92f` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `Bash` | 29 |
| `mcp__sourcegraph__sg_keyword_search` | 28 |
| `mcp__sourcegraph__sg_read_file` | 20 |
| `Read` | 5 |
| `TodoWrite` | 5 |
| `mcp__sourcegraph__sg_list_files` | 4 |
| `mcp__sourcegraph__sg_nls_search` | 3 |
| `Write` | 2 |
| `Edit` | 1 |
| `Grep` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `Bash` |
| `Bash` |
| `mcp__sourcegraph__sg_read_file` |
| `Grep` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_keyword_search` |

## Conversation Preview

Parsed from transcript using the same message categories as the dashboard trace parser.

| Seq | Type | Subtype | Tool | Text |
|---:|---|---|---|---|
| 1 | `system` | `init` | `-` | - |
| 2 | `assistant` | `text` | `-` | I'll help you fix the admin filter sidebar issue. Let me start by exploring the repository structure and understanding the test suite, as instructed. |
| 3 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 4 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 5 | `user` | `text` | `-` | - |
| 6 | `user` | `text` | `-` | - |
| 7 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 8 | `user` | `text` | `-` | - |
| 9 | `assistant` | `text` | `-` | Let me run the admin filters tests to see the current state: |
| 10 | `assistant` | `tool_use` | `Bash` | - |
| 11 | `user` | `text` | `-` | - |
| 12 | `assistant` | `tool_use` | `Bash` | - |
| 13 | `user` | `text` | `-` | - |
| 14 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 15 | `user` | `text` | `-` | - |
| 16 | `assistant` | `tool_use` | `Grep` | - |
| 17 | `user` | `text` | `-` | - |
| 18 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 19 | `user` | `text` | `-` | - |
| 20 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 21 | `user` | `text` | `-` | - |
| 22 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 23 | `user` | `text` | `-` | - |
| 24 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 25 | `user` | `text` | `-` | - |
| 26 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 27 | `user` | `text` | `-` | - |
| 28 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 29 | `user` | `text` | `-` | - |
| 30 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 31 | `user` | `text` | `-` | - |
| 32 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 33 | `user` | `text` | `-` | - |
| 34 | `assistant` | `text` | `-` | Let me check the `field_choices` method more carefully: |
| 35 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 36 | `user` | `text` | `-` | - |
| 37 | `assistant` | `text` | `-` | Let me look for failing tests related to empty filters by searching the test file more carefully: |
| 38 | `assistant` | `tool_use` | `Bash` | - |
| 39 | `user` | `text` | `-` | - |
| 40 | `assistant` | `tool_use` | `Bash` | - |
| 41 | `user` | `text` | `-` | - |
| 42 | `assistant` | `tool_use` | `Bash` | - |
| 43 | `user` | `text` | `-` | - |
| 44 | `assistant` | `tool_use` | `Bash` | - |
| 45 | `user` | `text` | `-` | - |
| 46 | `assistant` | `tool_use` | `Bash` | - |
| 47 | `user` | `text` | `-` | - |
| 48 | `assistant` | `tool_use` | `Bash` | - |
| 49 | `user` | `text` | `-` | - |
| 50 | `assistant` | `tool_use` | `Bash` | - |
| 51 | `user` | `text` | `-` | - |
| 52 | `assistant` | `tool_use` | `Bash` | - |
| 53 | `user` | `text` | `-` | - |
| 54 | `assistant` | `tool_use` | `Bash` | - |
| 55 | `user` | `text` | `-` | - |
| 56 | `assistant` | `tool_use` | `Bash` | - |
| 57 | `user` | `text` | `-` | - |
| 58 | `assistant` | `tool_use` | `Bash` | - |
| 59 | `user` | `text` | `-` | - |
| 60 | `assistant` | `tool_use` | `Bash` | - |
| 61 | `user` | `text` | `-` | - |
| 62 | `assistant` | `tool_use` | `Bash` | - |
| 63 | `user` | `text` | `-` | - |
| 64 | `assistant` | `tool_use` | `Bash` | - |
| 65 | `user` | `text` | `-` | - |
| 66 | `assistant` | `tool_use` | `Bash` | - |
| 67 | `user` | `text` | `-` | - |
| 68 | `assistant` | `text` | `-` | Let me use TodoWrite to track my progress and then search for test cases related to the bug: |
| 69 | `assistant` | `tool_use` | `TodoWrite` | - |
| 70 | `user` | `text` | `-` | - |
| 71 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 72 | `user` | `text` | `-` | - |
| 73 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_nls_search` | - |
| 74 | `user` | `text` | `-` | - |
| 75 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_nls_search` | - |
| 76 | `user` | `text` | `-` | - |
| 77 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_nls_search` | - |
| 78 | `user` | `text` | `-` | - |
| 79 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 80 | `user` | `text` | `-` | - |
