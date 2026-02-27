# bl_CCX-compliance-124_uZy48l (baseline-local-artifact)

- Run: `ccb_mcp_compliance_haiku_20260225_011700`
- Status: `passed`
- Reward: `0.3750`
- Audit JSON: [link](../audits/ccb_mcp_compliance_haiku_20260225_011700--baseline-local-artifact--bl_CCX-compliance-124_uZy48l.json)
- Trajectory available: `True`
- Transcript available: `True`
- Bundled trajectory: [link](../traces/ccb_mcp_compliance_haiku_20260225_011700--baseline-local-artifact--bl_CCX-compliance-124_uZy48l/trajectory.json)
- Bundled transcript: [link](../traces/ccb_mcp_compliance_haiku_20260225_011700--baseline-local-artifact--bl_CCX-compliance-124_uZy48l/claude-code.txt)

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 2218.6 |
| Agent execution seconds | 1958.1 |
| Input tokens | 1,914,384 |
| Output tokens | 133 |
| Cache tokens | 1,913,314 |
| Tool calls (total) | 29 |
| Tool calls (MCP) | 0 |
| Tool calls (local) | 29 |
| MCP ratio | 0.000 |
| keyword_search calls | - |
| nls_search calls | - |
| deepsearch calls | - |
| `result.json` SHA256 | `a29ee19b5ef24ca90a1019d2423aa3eb846f8553e39de3260c1fb750e4865bd5` |
| `trajectory.json` SHA256 | `b4b9897e5b375a1db9e8ec9209ba2bf4566ed1227092b2614ef61e0dd9ffa592` |
| transcript SHA256 | `df887eacf446e7b61228b4d83ec1005e19a6a1174d71a46216f605797a56d2cd` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `Bash` | 15 |
| `Read` | 12 |
| `Grep` | 1 |
| `Write` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `Bash` |
| `Bash` |
| `Bash` |
| `Bash` |
| `Bash` |
| `Read` |
| `Read` |
| `Read` |
| `Read` |
| `Read` |
| `Read` |
| `Grep` |

## Conversation Preview

Parsed from transcript using the same message categories as the dashboard trace parser.

| Seq | Type | Subtype | Tool | Text |
|---:|---|---|---|---|
| 1 | `system` | `init` | `-` | - |
| 2 | `assistant` | `text` | `-` | I'll help you audit the Content Security Policy (CSP) enforcement infrastructure in Firefox. Let me start by exploring the repository structure to locate the relevant files in the `dom/security/` directory. |
| 3 | `assistant` | `tool_use` | `Bash` | - |
| 4 | `assistant` | `tool_use` | `Bash` | - |
| 5 | `user` | `text` | `-` | - |
| 6 | `user` | `text` | `-` | - |
| 7 | `assistant` | `text` | `-` | Great! The Firefox repository is available. Now let me explore the `dom/security/` directory to find the CSP implementation files. |
| 8 | `assistant` | `tool_use` | `Bash` | - |
| 9 | `user` | `text` | `-` | - |
| 10 | `assistant` | `text` | `-` | Perfect! I can see several CSP-related files. Let me search for more files, particularly the XPCOM interface file and other relevant CSP files. |
| 11 | `assistant` | `tool_use` | `Bash` | - |
| 12 | `user` | `text` | `-` | - |
| 13 | `assistant` | `tool_use` | `Bash` | - |
| 14 | `user` | `text` | `-` | - |
| 15 | `assistant` | `text` | `-` | Excellent! Now let me examine the key files to understand their structure and identify the primary classes and functions: |
| 16 | `assistant` | `tool_use` | `Read` | - |
| 17 | `user` | `text` | `-` | - |
| 18 | `assistant` | `tool_use` | `Read` | - |
| 19 | `user` | `text` | `-` | - |
| 20 | `assistant` | `tool_use` | `Read` | - |
| 21 | `user` | `text` | `-` | - |
| 22 | `assistant` | `tool_use` | `Read` | - |
| 23 | `user` | `text` | `-` | - |
| 24 | `assistant` | `text` | `-` | Now let me check the CSPEvalChecker which handles script-src evaluation: |
| 25 | `assistant` | `tool_use` | `Read` | - |
| 26 | `user` | `text` | `-` | - |
| 27 | `assistant` | `tool_use` | `Read` | - |
| 28 | `user` | `text` | `-` | - |
| 29 | `assistant` | `text` | `-` | Let me check nsContentSecurityManager for inline script evaluation: |
| 30 | `assistant` | `tool_use` | `Grep` | - |
| 31 | `user` | `text` | `-` | - |
| 32 | `assistant` | `tool_use` | `Read` | - |
| 33 | `user` | `text` | `-` | - |
| 34 | `assistant` | `tool_use` | `Bash` | - |
| 35 | `user` | `text` | `-` | - |
| 36 | `assistant` | `tool_use` | `Bash` | - |
| 37 | `user` | `text` | `-` | - |
| 38 | `assistant` | `tool_use` | `Bash` | - |
| 39 | `user` | `text` | `-` | - |
| 40 | `assistant` | `tool_use` | `Bash` | - |
| 41 | `user` | `text` | `-` | - |
| 42 | `assistant` | `tool_use` | `Bash` | - |
| 43 | `user` | `text` | `-` | - |
| 44 | `assistant` | `tool_use` | `Bash` | - |
| 45 | `user` | `text` | `-` | - |
| 46 | `assistant` | `tool_use` | `Read` | - |
| 47 | `user` | `text` | `-` | - |
| 48 | `assistant` | `tool_use` | `Bash` | - |
| 49 | `user` | `text` | `-` | - |
| 50 | `assistant` | `tool_use` | `Bash` | - |
| 51 | `user` | `text` | `-` | - |
| 52 | `assistant` | `tool_use` | `Bash` | - |
| 53 | `user` | `text` | `-` | - |
| 54 | `assistant` | `tool_use` | `Bash` | - |
| 55 | `user` | `text` | `-` | - |
| 56 | `assistant` | `tool_use` | `Read` | - |
| 57 | `user` | `text` | `-` | - |
| 58 | `assistant` | `tool_use` | `Read` | - |
| 59 | `user` | `text` | `-` | - |
| 60 | `assistant` | `tool_use` | `Read` | - |
| 61 | `user` | `text` | `-` | - |
| 62 | `assistant` | `text` | `-` | Now let me verify the structure of the files I found and look at the violation reporting: |
| 63 | `assistant` | `tool_use` | `Read` | - |
| 64 | `user` | `text` | `-` | - |
| 65 | `assistant` | `text` | `-` | Perfect! Now I have comprehensive information about the CSP enforcement infrastructure. Let me create the answer file with all the findings: |
| 66 | `assistant` | `tool_use` | `Write` | - |
| 67 | `user` | `text` | `-` | - |
| 68 | `assistant` | `text` | `-` | Perfect! I have successfully completed the audit of the Content Security Policy (CSP) enforcement infrastructure in Firefox. Here's a summary of my findings:  ## CSP Enforcement Files Found  ### Core Implementation Files... |
