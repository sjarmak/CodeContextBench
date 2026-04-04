# mcp_CCX-compliance-115_TuPA0J (mcp-remote-direct)

- Run: `csb_org_compliance_haiku_20260226_035617`
- Status: `failed`
- Reward: `0.0000`
- Audit JSON: [link](../audits/csb_org_compliance_haiku_20260226_035617--mcp-remote-direct--mcp_CCX-compliance-115_TuPA0J.json)
- Trajectory available: `True`
- Transcript available: `True`
- Bundled trajectory: [link](../traces/csb_org_compliance_haiku_20260226_035617--mcp-remote-direct--mcp_CCX-compliance-115_TuPA0J/trajectory.json)

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 1520.5 |
| Agent execution seconds | 162.1 |
| Input tokens | 757,146 |
| Output tokens | 1,773 |
| Cache tokens | 756,953 |
| Tool calls (total) | 8 |
| Tool calls (MCP) | 7 |
| Tool calls (local) | 1 |
| MCP ratio | 0.875 |
| keyword_search calls | 2 |
| nls_search calls | 1 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `9a0427165ac0eb77f4ddce76773944336cc9275ee2216e4a1761c952222dfdcf` |
| `trajectory.json` SHA256 | `d4584eb59facbbb8766a40882c82692549baf53734324fd72ffb3f63fd5d357b` |
| transcript SHA256 | `de57c925b82421d76b32625841ffe37c21e43a3afa302f4b65363ad9f618ea0d` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `mcp__sourcegraph__sg_read_file` | 4 |
| `mcp__sourcegraph__sg_keyword_search` | 2 |
| `Write` | 1 |
| `mcp__sourcegraph__sg_nls_search` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_nls_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `Write` |
