# sgonly_test-unitgen-py-001 (mcp-remote-direct)

- Run: `ccb_test_haiku_022326`
- Status: `passed`
- Reward: `1.0000`
- Audit JSON: [link](../audits/ccb_test_haiku_022326--mcp--sgonly_test-unitgen-py-001.json)
- Trajectory available: `True`
- Transcript available: `True`
- Bundled trajectory: [link](../traces/ccb_test_haiku_022326--mcp--sgonly_test-unitgen-py-001/trajectory.json)
- Bundled transcript: [link](../traces/ccb_test_haiku_022326--mcp--sgonly_test-unitgen-py-001/claude-code.txt)

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 373.2 |
| Agent execution seconds | 55.5 |
| Input tokens | 382,339 |
| Output tokens | 11 |
| Cache tokens | 382,227 |
| Tool calls (total) | 3 |
| Tool calls (MCP) | 1 |
| Tool calls (local) | 2 |
| MCP ratio | 0.333 |
| keyword_search calls | - |
| nls_search calls | - |
| deepsearch calls | - |
| `result.json` SHA256 | `012662a5b4edc896bccb4713c6cb7db74e62d9d968439ebf3726b33fcb8dcacb` |
| `trajectory.json` SHA256 | `2e7d7c5e5730c0ab2137e6e01fbac55307ab59665758c356ce01ab9a253bafd1` |
| transcript SHA256 | `c043e03cfda5dccfe57d8b50ddcfbe93506948c84534a2f1c8a874ed24f810ee` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `Read` | 1 |
| `Write` | 1 |
| `mcp__sourcegraph__sg_read_file` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_read_file` |
| `Write` |
| `Read` |

## Conversation Preview

Parsed from transcript using the same message categories as the dashboard trace parser.

| Seq | Type | Subtype | Tool | Text |
|---:|---|---|---|---|
| 1 | `system` | `init` | `-` | - |
| 2 | `assistant` | `text` | `-` | I'll help you generate comprehensive unit tests for Django's cache middleware. Let me start by reading the cache middleware code to understand the implementation. |
| 3 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_read_file` | - |
| 4 | `user` | `text` | `-` | - |
| 5 | `assistant` | `text` | `-` | Now I'll create comprehensive unit tests for the Django cache middleware. Let me write the test file: |
| 6 | `assistant` | `tool_use` | `Write` | - |
| 7 | `user` | `text` | `-` | - |
| 8 | `assistant` | `text` | `-` | Perfect! I've created a comprehensive unit test file for Django's cache middleware. Let me verify the file was created correctly: |
| 9 | `assistant` | `tool_use` | `Read` | - |
| 10 | `user` | `text` | `-` | - |
| 11 | `assistant` | `text` | `-` | Excellent! I've successfully created a comprehensive unit test file for Django's cache middleware at `/workspace/tests/test_cache_middleware.py`. Here's a summary of what I've generated:  ## Test Coverage Overview  ### *... |
