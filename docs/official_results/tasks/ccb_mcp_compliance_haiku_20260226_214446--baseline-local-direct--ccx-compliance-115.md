# ccx-compliance-115 (baseline-local-direct)

- Run: `csb_org_compliance_haiku_20260226_214446`
- Status: `passed`
- Reward: `0.6667`
- Audit JSON: [link](../audits/csb_org_compliance_haiku_20260226_214446--baseline-local-direct--ccx-compliance-115.json)
- Trajectory available: `True`
- Transcript available: `True`
- Bundled trajectory: [link](../traces/csb_org_compliance_haiku_20260226_214446--baseline-local-direct--ccx-compliance-115/trajectory.json)
- Bundled transcript: [link](../traces/csb_org_compliance_haiku_20260226_214446--baseline-local-direct--ccx-compliance-115/claude-code.txt)

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 94.0 |
| Agent execution seconds | 54.0 |
| Input tokens | 677,400 |
| Output tokens | 5,088 |
| Cache tokens | 677,104 |
| Tool calls (total) | 11 |
| Tool calls (MCP) | 0 |
| Tool calls (local) | 11 |
| MCP ratio | 0.000 |
| keyword_search calls | - |
| nls_search calls | - |
| deepsearch calls | - |
| `result.json` SHA256 | `1649a892eae00b328ce61fabf1d046d472611752bc138cdb84b525f6064b8be8` |
| `trajectory.json` SHA256 | `759aa46f0dd2e6b741657c22e5a0db7229a041b68b10511c826b41ee1c72780c` |
| transcript SHA256 | `d3c37af36e9ae62edf62ea8d21ceb5b9898b077139377caed43bb87be2279453` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `Read` | 6 |
| `Bash` | 3 |
| `Grep` | 1 |
| `Write` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `Bash` |
| `Bash` |
| `Bash` |
| `Grep` |
| `Read` |
| `Read` |
| `Read` |
| `Read` |
| `Read` |
| `Read` |
| `Write` |

## Conversation Preview

Parsed from transcript using the same message categories as the dashboard trace parser.

| Seq | Type | Subtype | Tool | Text |
|---:|---|---|---|---|
| 1 | `system` | `init` | `-` | - |
| 2 | `assistant` | `text` | `-` | I'll help you audit Django's session framework for concurrency safety in the session key rotation path. Let me start by exploring the codebase structure. |
| 3 | `assistant` | `tool_use` | `Bash` | - |
| 4 | `user` | `text` | `-` | - |
| 5 | `assistant` | `tool_use` | `Bash` | - |
| 6 | `user` | `text` | `-` | - |
| 7 | `assistant` | `tool_use` | `Bash` | - |
| 8 | `user` | `text` | `-` | - |
| 9 | `assistant` | `tool_use` | `Grep` | - |
| 10 | `user` | `text` | `-` | - |
| 11 | `assistant` | `tool_use` | `Read` | - |
| 12 | `user` | `text` | `-` | - |
| 13 | `assistant` | `tool_use` | `Read` | - |
| 14 | `user` | `text` | `-` | - |
| 15 | `assistant` | `tool_use` | `Read` | - |
| 16 | `user` | `text` | `-` | - |
| 17 | `assistant` | `tool_use` | `Read` | - |
| 18 | `user` | `text` | `-` | - |
| 19 | `assistant` | `tool_use` | `Read` | - |
| 20 | `user` | `text` | `-` | - |
| 21 | `assistant` | `text` | `-` | Now let me check the base_session.py file to see the model definition: |
| 22 | `assistant` | `tool_use` | `Read` | - |
| 23 | `user` | `text` | `-` | - |
| 24 | `assistant` | `text` | `-` | Perfect! Now I have all the information needed. Let me create the answer file: |
| 25 | `assistant` | `tool_use` | `Write` | - |
| 26 | `user` | `text` | `-` | - |
| 27 | `assistant` | `text` | `-` | Perfect! I've completed the compliance audit of Django's session framework for concurrency safety in the session key rotation path. Here's a summary of my findings:  ## Key Findings:  ### 1. **cycle_key() Implementation*... |
