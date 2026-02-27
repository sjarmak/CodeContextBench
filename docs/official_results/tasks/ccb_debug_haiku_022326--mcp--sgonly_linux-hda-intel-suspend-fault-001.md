# sgonly_linux-hda-intel-suspend-fault-001 (mcp-remote-direct)

- Run: `ccb_debug_haiku_022326`
- Status: `passed`
- Reward: `0.7000`
- Audit JSON: [link](../audits/ccb_debug_haiku_022326--mcp--sgonly_linux-hda-intel-suspend-fault-001.json)
- Trajectory available: `True`
- Transcript available: `True`
- Bundled trajectory: [link](../traces/ccb_debug_haiku_022326--mcp--sgonly_linux-hda-intel-suspend-fault-001/trajectory.json)
- Bundled transcript: [link](../traces/ccb_debug_haiku_022326--mcp--sgonly_linux-hda-intel-suspend-fault-001/claude-code.txt)

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 316.3 |
| Agent execution seconds | 247.4 |
| Input tokens | 5,475,903 |
| Output tokens | 200 |
| Cache tokens | 5,475,346 |
| Tool calls (total) | 49 |
| Tool calls (MCP) | 44 |
| Tool calls (local) | 5 |
| MCP ratio | 0.898 |
| keyword_search calls | 26 |
| nls_search calls | 0 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `7640b5620b36699590eace5a4ec08323b256b20631d0399b0ce5e45905d5e5fd` |
| `trajectory.json` SHA256 | `e991812ff4b03bbe9c166c0fd4a426b441b334c3add820bc5e042caf21730213` |
| transcript SHA256 | `af449a57756b5e2a3cdbe50c843c0218bde02bd036202dafe4cd7983264dd31e` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `mcp__sourcegraph__sg_keyword_search` | 26 |
| `mcp__sourcegraph__sg_read_file` | 15 |
| `Bash` | 3 |
| `Read` | 1 |
| `Write` | 1 |
| `mcp__sourcegraph__sg_commit_search` | 1 |
| `mcp__sourcegraph__sg_diff_search` | 1 |
| `mcp__sourcegraph__sg_list_files` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `Bash` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |

## Conversation Preview

Parsed from transcript using the same message categories as the dashboard trace parser.

| Seq | Type | Subtype | Tool | Text |
|---:|---|---|---|---|
| 1 | `system` | `init` | `-` | - |
| 2 | `assistant` | `text` | `-` | I'll analyze this HDA Intel sound bug systematically. The error messages indicate timeout issues during suspend/resume cycles. Let me start by exploring the kernel source code. |
| 3 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 4 | `user` | `text` | `-` | - |
| 5 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 6 | `user` | `text` | `-` | - |
| 7 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 8 | `user` | `text` | `-` | - |
| 9 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 10 | `user` | `text` | `-` | - |
| 11 | `assistant` | `tool_use` | `Bash` | - |
| 12 | `user` | `text` | `-` | - |
| 13 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 14 | `user` | `text` | `-` | - |
| 15 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 16 | `user` | `text` | `-` | - |
| 17 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 18 | `user` | `text` | `-` | - |
| 19 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 20 | `user` | `text` | `-` | - |
| 21 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 22 | `user` | `text` | `-` | - |
| 23 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 24 | `user` | `text` | `-` | - |
| 25 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 26 | `user` | `text` | `-` | - |
| 27 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 28 | `user` | `text` | `-` | - |
| 29 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 30 | `user` | `text` | `-` | - |
| 31 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 32 | `user` | `text` | `-` | - |
| 33 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 34 | `user` | `text` | `-` | - |
| 35 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 36 | `user` | `text` | `-` | - |
| 37 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 38 | `user` | `text` | `-` | - |
| 39 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 40 | `user` | `text` | `-` | - |
| 41 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 42 | `user` | `text` | `-` | - |
| 43 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 44 | `user` | `text` | `-` | - |
| 45 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 46 | `user` | `text` | `-` | - |
| 47 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 48 | `user` | `text` | `-` | - |
| 49 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 50 | `user` | `text` | `-` | - |
| 51 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 52 | `user` | `text` | `-` | - |
| 53 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 54 | `user` | `text` | `-` | - |
| 55 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 56 | `user` | `text` | `-` | - |
| 57 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 58 | `user` | `text` | `-` | - |
| 59 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_commit_search` | - |
| 60 | `user` | `text` | `-` | - |
| 61 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_diff_search` | - |
| 62 | `user` | `text` | `-` | - |
| 63 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 64 | `user` | `text` | `-` | - |
| 65 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 66 | `user` | `text` | `-` | - |
| 67 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 68 | `user` | `text` | `-` | - |
| 69 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 70 | `user` | `text` | `-` | - |
| 71 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 72 | `user` | `text` | `-` | - |
| 73 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 74 | `user` | `text` | `-` | - |
| 75 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 76 | `user` | `text` | `-` | - |
| 77 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 78 | `user` | `text` | `-` | - |
| 79 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 80 | `user` | `text` | `-` | - |
