# sgonly_vscode-ext-host-qa-001 (mcp-remote-direct)

- Run: `understand_haiku_20260225_211346`
- Status: `passed`
- Reward: `0.9600`
- Audit JSON: [link](../audits/understand_haiku_20260225_211346--mcp-remote-direct--sgonly_vscode-ext-host-qa-001.json)
- Trajectory available: `True`
- Transcript available: `True`
- Bundled trajectory: [link](../traces/understand_haiku_20260225_211346--mcp-remote-direct--sgonly_vscode-ext-host-qa-001/trajectory.json)
- Bundled transcript: [link](../traces/understand_haiku_20260225_211346--mcp-remote-direct--sgonly_vscode-ext-host-qa-001/claude-code.txt)

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 175.6 |
| Agent execution seconds | 89.4 |
| Input tokens | 2,414,327 |
| Output tokens | 65 |
| Cache tokens | 2,413,784 |
| Tool calls (total) | 27 |
| Tool calls (MCP) | 26 |
| Tool calls (local) | 1 |
| MCP ratio | 0.963 |
| keyword_search calls | 7 |
| nls_search calls | 2 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `ea78f235a02df2714ead5a36b4cf2e6ceb093c4134bdd99244090473d0bf7d96` |
| `trajectory.json` SHA256 | `d46c73bcf6870bec208fbce349546b3f3df3ab459b5ec2d95a2894490a9ae47c` |
| transcript SHA256 | `a087d641d731e59bdbe5bfecc51afa31062030fdd5a38cb3006eb714ef6bec0c` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `mcp__sourcegraph__sg_read_file` | 12 |
| `mcp__sourcegraph__sg_keyword_search` | 7 |
| `mcp__sourcegraph__sg_list_files` | 5 |
| `mcp__sourcegraph__sg_nls_search` | 2 |
| `Write` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_nls_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_nls_search` |

## Conversation Preview

Parsed from transcript using the same message categories as the dashboard trace parser.

| Seq | Type | Subtype | Tool | Text |
|---:|---|---|---|---|
| 1 | `system` | `init` | `-` | - |
| 2 | `assistant` | `text` | `-` | I'll investigate VS Code's extension host isolation architecture by exploring the codebase. Let me start with structured searches to understand the key components. |
| 3 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 4 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 5 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 6 | `user` | `text` | `-` | - |
| 7 | `user` | `text` | `-` | - |
| 8 | `user` | `text` | `-` | - |
| 9 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 10 | `user` | `text` | `-` | - |
| 11 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 12 | `user` | `text` | `-` | - |
| 13 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_nls_search` | - |
| 14 | `user` | `text` | `-` | - |
| 15 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 16 | `user` | `text` | `-` | - |
| 17 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 18 | `user` | `text` | `-` | - |
| 19 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 20 | `user` | `text` | `-` | - |
| 21 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 22 | `user` | `text` | `-` | - |
| 23 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 24 | `user` | `text` | `-` | - |
| 25 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_nls_search` | - |
| 26 | `user` | `text` | `-` | - |
| 27 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 28 | `user` | `text` | `-` | - |
| 29 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 30 | `user` | `text` | `-` | - |
| 31 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 32 | `user` | `text` | `-` | - |
| 33 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 34 | `user` | `text` | `-` | - |
| 35 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 36 | `user` | `text` | `-` | - |
| 37 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 38 | `user` | `text` | `-` | - |
| 39 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 40 | `user` | `text` | `-` | - |
| 41 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 42 | `user` | `text` | `-` | - |
| 43 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 44 | `user` | `text` | `-` | - |
| 45 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 46 | `user` | `text` | `-` | - |
| 47 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 48 | `user` | `text` | `-` | - |
| 49 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 50 | `user` | `text` | `-` | - |
| 51 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 52 | `user` | `text` | `-` | - |
| 53 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 54 | `user` | `text` | `-` | - |
| 55 | `assistant` | `text` | `-` | Now I have enough information to provide a comprehensive investigation. Let me write the findings: |
| 56 | `assistant` | `tool_use` | `Write` | - |
| 57 | `user` | `text` | `-` | - |
| 58 | `assistant` | `text` | `-` | I've completed a comprehensive investigation of VS Code's extension host isolation architecture. Here's what I found:  ## Summary of Findings  **The answer is: VS Code uses process isolation at the OS level combined with... |
