# sgonly_envoy-ext-authz-handoff-001 (mcp-remote-direct)

- Run: `understand_haiku_20260225_211346`
- Status: `passed`
- Reward: `0.8300`
- Audit JSON: [link](../audits/understand_haiku_20260225_211346--mcp-remote-direct--sgonly_envoy-ext-authz-handoff-001.json)
- Trajectory available: `True`
- Transcript available: `True`
- Bundled trajectory: [link](../traces/understand_haiku_20260225_211346--mcp-remote-direct--sgonly_envoy-ext-authz-handoff-001/trajectory.json)
- Bundled transcript: [link](../traces/understand_haiku_20260225_211346--mcp-remote-direct--sgonly_envoy-ext-authz-handoff-001/claude-code.txt)

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 219.3 |
| Agent execution seconds | 117.0 |
| Input tokens | 2,232,684 |
| Output tokens | 66 |
| Cache tokens | 2,232,222 |
| Tool calls (total) | 25 |
| Tool calls (MCP) | 24 |
| Tool calls (local) | 1 |
| MCP ratio | 0.960 |
| keyword_search calls | 1 |
| nls_search calls | 1 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `b1beaba051f8a53fac19ba1043d7a58c95699a875f3dec89c2f3abf3d60e3635` |
| `trajectory.json` SHA256 | `513a9342260f47d18e2d82fe3d9cd6d910e118854164e17375fc3884ebb10262` |
| transcript SHA256 | `73af9fc8e16db41516bf4dedde1061398b9daa7029f653f22859649b455e6aa0` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `mcp__sourcegraph__sg_read_file` | 17 |
| `mcp__sourcegraph__sg_list_files` | 5 |
| `Write` | 1 |
| `mcp__sourcegraph__sg_keyword_search` | 1 |
| `mcp__sourcegraph__sg_nls_search` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_nls_search` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |

## Conversation Preview

Parsed from transcript using the same message categories as the dashboard trace parser.

| Seq | Type | Subtype | Tool | Text |
|---:|---|---|---|---|
| 1 | `system` | `init` | `-` | - |
| 2 | `assistant` | `text` | `-` | I'll help you build a comprehensive handoff document for the ext_authz filter. Let me start by exploring the Envoy codebase to understand this component. |
| 3 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 4 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_nls_search` | - |
| 5 | `user` | `text` | `-` | - |
| 6 | `user` | `text` | `-` | - |
| 7 | `assistant` | `text` | `-` | Let me explore the directory structure and read key implementation files. |
| 8 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 9 | `user` | `text` | `-` | - |
| 10 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 11 | `user` | `text` | `-` | - |
| 12 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
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
| 24 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 25 | `user` | `text` | `-` | - |
| 26 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 27 | `user` | `text` | `-` | - |
| 28 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 29 | `user` | `text` | `-` | - |
| 30 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 31 | `user` | `text` | `-` | - |
| 32 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 33 | `user` | `text` | `-` | - |
| 34 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_list_files` | - |
| 35 | `user` | `text` | `-` | - |
| 36 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 37 | `user` | `text` | `-` | - |
| 38 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 39 | `user` | `text` | `-` | - |
| 40 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 41 | `user` | `text` | `-` | - |
| 42 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 43 | `user` | `text` | `-` | - |
| 44 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 45 | `user` | `text` | `-` | - |
| 46 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 47 | `user` | `text` | `-` | - |
| 48 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 49 | `user` | `text` | `-` | - |
| 50 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 51 | `user` | `text` | `-` | - |
| 52 | `assistant` | `text` | `-` | Now let me create the comprehensive handoff document with all the information I've gathered. |
| 53 | `assistant` | `tool_use` | `Write` | - |
| 54 | `user` | `text` | `-` | - |
| 55 | `assistant` | `text` | `-` | Perfect! I've created a comprehensive handoff document for the **ext_authz filter** at `/logs/agent/onboarding.md`. Here's what I've covered:  ## Document Summary  ### 1. **Purpose** (3 sections) - What it does: intercep... |
