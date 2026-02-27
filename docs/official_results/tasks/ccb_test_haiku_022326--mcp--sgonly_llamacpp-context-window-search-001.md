# sgonly_llamacpp-context-window-search-001 (mcp-remote-direct)

- Run: `ccb_test_haiku_022326`
- Status: `failed`
- Reward: `0.0000`
- Audit JSON: [link](../audits/ccb_test_haiku_022326--mcp--sgonly_llamacpp-context-window-search-001.json)
- Trajectory available: `True`
- Transcript available: `True`
- Bundled trajectory: [link](../traces/ccb_test_haiku_022326--mcp--sgonly_llamacpp-context-window-search-001/trajectory.json)
- Bundled transcript: [link](../traces/ccb_test_haiku_022326--mcp--sgonly_llamacpp-context-window-search-001/claude-code.txt)

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 93.3 |
| Agent execution seconds | 18.4 |
| Input tokens | 302,718 |
| Output tokens | 26 |
| Cache tokens | 302,614 |
| Tool calls (total) | 4 |
| Tool calls (MCP) | 4 |
| Tool calls (local) | 0 |
| MCP ratio | 1.000 |
| keyword_search calls | 2 |
| nls_search calls | 0 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `b483c21fb73d055f4441096271055cdcade2f8678f8ee170cf2b46670b5a929c` |
| `trajectory.json` SHA256 | `234154d3d341dc98926f9ec92f599196307e9122cb04737551cc9366fb4253f1` |
| transcript SHA256 | `0fb2cae5ef6e9e02c81f99c01274416cdc007c020f56022b07098bfc9bdce731` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `mcp__sourcegraph__sg_commit_search` | 2 |
| `mcp__sourcegraph__sg_keyword_search` | 2 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_commit_search` |
| `mcp__sourcegraph__sg_commit_search` |
| `mcp__sourcegraph__sg_keyword_search` |

## Conversation Preview

Parsed from transcript using the same message categories as the dashboard trace parser.

| Seq | Type | Subtype | Tool | Text |
|---:|---|---|---|---|
| 1 | `system` | `init` | `-` | - |
| 2 | `assistant` | `text` | `-` | I'll help you find the pull request that improved the context window for llama3.1 series models. Let me search the repository for this information. |
| 3 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 4 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_commit_search` | - |
| 5 | `user` | `text` | `-` | - |
| 6 | `user` | `text` | `-` | - |
| 7 | `assistant` | `text` | `-` | Let me try broader search terms: |
| 8 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_commit_search` | - |
| 9 | `assistant` | `tool_use` | `mcp__sourcegraph__sg_keyword_search` | - |
| 10 | `user` | `text` | `-` | - |
| 11 | `user` | `text` | `-` | - |
| 12 | `assistant` | `text` | `-` | Perfect! I found the pull request that improved the context window for llama3.1 series models.  **PR #8676: "llama : add support for llama 3.1 rope scaling factors"**  From the commit message, this PR: - Adds llama 3.1 r... |
