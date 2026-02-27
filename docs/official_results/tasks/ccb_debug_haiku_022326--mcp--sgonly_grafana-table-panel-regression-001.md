# sgonly_grafana-table-panel-regression-001 (mcp-remote-direct)

- Run: `ccb_debug_haiku_022326`
- Status: `passed`
- Reward: `0.9000`
- Audit JSON: [link](../audits/ccb_debug_haiku_022326--mcp--sgonly_grafana-table-panel-regression-001.json)
- Trajectory available: `True`
- Transcript available: `True`
- Bundled trajectory: [link](../traces/ccb_debug_haiku_022326--mcp--sgonly_grafana-table-panel-regression-001/trajectory.json)
- Bundled transcript: [link](../traces/ccb_debug_haiku_022326--mcp--sgonly_grafana-table-panel-regression-001/claude-code.txt)

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 166.1 |
| Agent execution seconds | 109.2 |
| Input tokens | 1,839,708 |
| Output tokens | 67 |
| Cache tokens | 1,839,363 |
| Tool calls (total) | 14 |
| Tool calls (MCP) | 13 |
| Tool calls (local) | 1 |
| MCP ratio | 0.929 |
| keyword_search calls | 4 |
| nls_search calls | 0 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `2111ecdb6c682a172e97d6354a3407ea8f7fe9fce6a2fac32d026c426751b94d` |
| `trajectory.json` SHA256 | `23b8cf4c713903b14d8ebbf7c527437bcd14cd42195785c285e30320173d8d52` |
| transcript SHA256 | `d0c169e00ac21316d2e85bcd5c8ee5f6228ddd90e9f2be45d5d0b8c4a7235cb8` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `mcp__sourcegraph__sg_read_file` | 9 |
| `mcp__sourcegraph__sg_keyword_search` | 4 |
| `Write` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |

## Conversation Preview

Parsed from transcript using the same message categories as the dashboard trace parser.

| Seq | Type | Subtype | Tool | Text |
|---:|---|---|---|---|
| 1 | `system` | `init` | `-` | - |
| 2 | `assistant` | `text` | `-` | I'll investigate this Grafana dashboard migration regression. Let me start by searching for the dashboard migration pipeline and table panel schema handling. |
| 3 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 4 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 5 | `user` | `text` | `-` | - |
| 6 | `user` | `text` | `-` | - |
| 7 | `assistant` | `text` | `-` | Let me read the v38 migration file and related code to understand the exact regression. |
| 8 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 9 | `user` | `text` | `-` | - |
| 10 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 11 | `user` | `text` | `-` | - |
| 12 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 13 | `user` | `text` | `-` | - |
| 14 | `assistant` | `text` | `-` | Let me now check how the migration functions are called and what the main migration orchestration looks like. |
| 15 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 16 | `user` | `text` | `-` | - |
| 17 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 18 | `user` | `text` | `-` | - |
| 19 | `assistant` | `text` | `-` | Let me read one of the v38 test files to understand the exact scenario better: |
| 20 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 21 | `user` | `text` | `-` | - |
| 22 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 23 | `user` | `text` | `-` | - |
| 24 | `assistant` | `text` | `-` | Let me search for test cases or scenarios related to tables without explicit defaults.custom: |
| 25 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 26 | `user` | `text` | `-` | - |
| 27 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 28 | `user` | `text` | `-` | - |
| 29 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 30 | `user` | `text` | `-` | - |
| 31 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 32 | `user` | `text` | `-` | - |
| 33 | `assistant` | `text` | `-` | Now I have the full picture. Let me create the investigation report. |
| 34 | `assistant` | `tool_use` | `Write` | - |
| 35 | `user` | `text` | `-` | - |
| 36 | `assistant` | `text` | `-` | Perfect! I've completed the investigation and written the report to `/logs/agent/investigation.md`.  ## Summary of Findings  **The regression is in the v38 migration function** (`apps/dashboard/pkg/migration/schemaversio... |
