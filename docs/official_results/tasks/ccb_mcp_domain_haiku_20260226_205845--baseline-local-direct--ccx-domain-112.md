# ccx-domain-112 (baseline-local-direct)

- Run: `csb_org_domain_haiku_20260226_205845`
- Status: `passed`
- Reward: `0.7083`
- Audit JSON: [link](../audits/csb_org_domain_haiku_20260226_205845--baseline-local-direct--ccx-domain-112.json)
- Trajectory available: `True`
- Transcript available: `True`
- Bundled trajectory: [link](../traces/csb_org_domain_haiku_20260226_205845--baseline-local-direct--ccx-domain-112/trajectory.json)
- Bundled transcript: [link](../traces/csb_org_domain_haiku_20260226_205845--baseline-local-direct--ccx-domain-112/claude-code.txt)

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 135.5 |
| Agent execution seconds | 91.4 |
| Input tokens | 791,638 |
| Output tokens | 3,614 |
| Cache tokens | 791,329 |
| Tool calls (total) | 12 |
| Tool calls (MCP) | 0 |
| Tool calls (local) | 12 |
| MCP ratio | 0.000 |
| keyword_search calls | - |
| nls_search calls | - |
| deepsearch calls | - |
| `result.json` SHA256 | `6f73ed06b114210ae9ed67f4c32cc5c3d4d8e16816c2d4d22bf0de59ed8e4a12` |
| `trajectory.json` SHA256 | `c8149ca6619b6c43f9e094dc36293188c3d2c1327d13bc7d7ba09d1f7a0b7037` |
| transcript SHA256 | `3356aa6d0a659238a527385be7b35b1868b1f1ee6c79c2790d91d82426a927ba` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `Bash` | 6 |
| `Read` | 5 |
| `Write` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `Bash` |
| `Bash` |
| `Bash` |
| `Read` |
| `Bash` |
| `Read` |
| `Bash` |
| `Read` |
| `Read` |
| `Read` |
| `Bash` |
| `Write` |

## Conversation Preview

Parsed from transcript using the same message categories as the dashboard trace parser.

| Seq | Type | Subtype | Tool | Text |
|---:|---|---|---|---|
| 1 | `system` | `init` | `-` | - |
| 2 | `assistant` | `text` | `-` | I'll help you trace the Firefox Servo CSS style system integration by finding the core style resolution pipeline files. Let me start by exploring the workspace structure. |
| 3 | `assistant` | `tool_use` | `Bash` | - |
| 4 | `user` | `text` | `-` | - |
| 5 | `assistant` | `tool_use` | `Bash` | - |
| 6 | `user` | `text` | `-` | - |
| 7 | `assistant` | `tool_use` | `Bash` | - |
| 8 | `user` | `text` | `-` | - |
| 9 | `assistant` | `text` | `-` | Now let me examine each file to extract the key class and function names: |
| 10 | `assistant` | `tool_use` | `Read` | - |
| 11 | `user` | `text` | `-` | - |
| 12 | `assistant` | `tool_use` | `Bash` | - |
| 13 | `user` | `text` | `-` | - |
| 14 | `assistant` | `tool_use` | `Read` | - |
| 15 | `user` | `text` | `-` | - |
| 16 | `assistant` | `tool_use` | `Bash` | - |
| 17 | `user` | `text` | `-` | - |
| 18 | `assistant` | `tool_use` | `Read` | - |
| 19 | `user` | `text` | `-` | - |
| 20 | `assistant` | `tool_use` | `Read` | - |
| 21 | `user` | `text` | `-` | - |
| 22 | `assistant` | `tool_use` | `Read` | - |
| 23 | `user` | `text` | `-` | - |
| 24 | `assistant` | `tool_use` | `Bash` | - |
| 25 | `user` | `text` | `-` | - |
| 26 | `assistant` | `text` | `-` | Now let me create the comprehensive answer.json file: |
| 27 | `assistant` | `tool_use` | `Write` | - |
| 28 | `user` | `text` | `-` | - |
| 29 | `assistant` | `text` | `-` | Perfect! I've created the `/workspace/answer.json` file with a comprehensive analysis of Firefox's Servo CSS style system integration.  ## Summary of Findings  I've identified all **6 core files** in `mozilla-firefox/fir... |
