# ccx-compliance-118 (baseline-local-direct)

- Run: `csb_org_compliance_haiku_20260226_214446`
- Status: `passed`
- Reward: `0.8889`
- Audit JSON: [link](../audits/csb_org_compliance_haiku_20260226_214446--baseline-local-direct--ccx-compliance-118.json)
- Trajectory available: `True`
- Transcript available: `True`
- Bundled trajectory: [link](../traces/csb_org_compliance_haiku_20260226_214446--baseline-local-direct--ccx-compliance-118/trajectory.json)
- Bundled transcript: [link](../traces/csb_org_compliance_haiku_20260226_214446--baseline-local-direct--ccx-compliance-118/claude-code.txt)

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 116.8 |
| Agent execution seconds | 74.0 |
| Input tokens | 1,468,427 |
| Output tokens | 5,849 |
| Cache tokens | 1,467,978 |
| Tool calls (total) | 19 |
| Tool calls (MCP) | 0 |
| Tool calls (local) | 19 |
| MCP ratio | 0.000 |
| keyword_search calls | - |
| nls_search calls | - |
| deepsearch calls | - |
| `result.json` SHA256 | `a0c22b6d285512e17bdb35d245938a4f8261379c7b9a5e1996f9230cdd397336` |
| `trajectory.json` SHA256 | `1c947caf1f80a7202d1f6d22f6222db4a0454f41150c80ca6ecb20fee680e09d` |
| transcript SHA256 | `f4d33c237ff11a56071ef990c144cecc39f67c66ad24d5bc4be9380611794a2b` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `Bash` | 9 |
| `Read` | 6 |
| `Grep` | 3 |
| `Write` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `Bash` |
| `Bash` |
| `Grep` |
| `Grep` |
| `Read` |
| `Grep` |
| `Bash` |
| `Bash` |
| `Read` |
| `Bash` |
| `Bash` |
| `Bash` |

## Conversation Preview

Parsed from transcript using the same message categories as the dashboard trace parser.

| Seq | Type | Subtype | Tool | Text |
|---:|---|---|---|---|
| 1 | `system` | `init` | `-` | - |
| 2 | `assistant` | `text` | `-` | I'll help you audit Django's admin filter rendering pipeline. Let me start by exploring the workspace structure and then locate the relevant files. |
| 3 | `assistant` | `tool_use` | `Bash` | - |
| 4 | `user` | `text` | `-` | - |
| 5 | `assistant` | `tool_use` | `Bash` | - |
| 6 | `user` | `text` | `-` | - |
| 7 | `assistant` | `tool_use` | `Grep` | - |
| 8 | `user` | `text` | `-` | - |
| 9 | `assistant` | `tool_use` | `Grep` | - |
| 10 | `user` | `text` | `-` | - |
| 11 | `assistant` | `tool_use` | `Read` | - |
| 12 | `user` | `text` | `-` | - |
| 13 | `assistant` | `text` | `-` | Now let me find the ChangeList class in options.py: |
| 14 | `assistant` | `tool_use` | `Grep` | - |
| 15 | `user` | `text` | `-` | - |
| 16 | `assistant` | `tool_use` | `Bash` | - |
| 17 | `user` | `text` | `-` | - |
| 18 | `assistant` | `tool_use` | `Bash` | - |
| 19 | `user` | `text` | `-` | - |
| 20 | `assistant` | `tool_use` | `Read` | - |
| 21 | `user` | `text` | `-` | - |
| 22 | `assistant` | `text` | `-` | Now let me find the template tag that renders filters in the sidebar: |
| 23 | `assistant` | `tool_use` | `Bash` | - |
| 24 | `user` | `text` | `-` | - |
| 25 | `assistant` | `tool_use` | `Bash` | - |
| 26 | `user` | `text` | `-` | - |
| 27 | `assistant` | `tool_use` | `Bash` | - |
| 28 | `user` | `text` | `-` | - |
| 29 | `assistant` | `tool_use` | `Read` | - |
| 30 | `user` | `text` | `-` | - |
| 31 | `assistant` | `tool_use` | `Bash` | - |
| 32 | `user` | `text` | `-` | - |
| 33 | `assistant` | `tool_use` | `Read` | - |
| 34 | `user` | `text` | `-` | - |
| 35 | `assistant` | `tool_use` | `Bash` | - |
| 36 | `user` | `text` | `-` | - |
| 37 | `assistant` | `tool_use` | `Read` | - |
| 38 | `user` | `text` | `-` | - |
| 39 | `assistant` | `text` | `-` | Perfect! I have found all the necessary components. Let me create the comprehensive answer file: |
| 40 | `assistant` | `tool_use` | `Write` | - |
| 41 | `user` | `text` | `-` | - |
| 42 | `assistant` | `tool_use` | `Read` | - |
| 43 | `user` | `text` | `-` | - |
| 44 | `assistant` | `text` | `-` | Perfect! I have successfully completed the compliance audit of Django's admin filter rendering pipeline. Here's a summary of my findings:  ## Audit Findings  I've identified all four components you requested in the Djang... |
