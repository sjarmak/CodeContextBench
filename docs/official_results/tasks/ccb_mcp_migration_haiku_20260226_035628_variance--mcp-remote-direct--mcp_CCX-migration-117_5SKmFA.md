# mcp_CCX-migration-117_5SKmFA (mcp-remote-direct)

- Run: `csb_org_migration_haiku_20260226_035628_variance`
- Status: `failed`
- Reward: `0.0000`
- Audit JSON: [link](../audits/csb_org_migration_haiku_20260226_035628_variance--mcp-remote-direct--mcp_CCX-migration-117_5SKmFA.json)
- Trajectory available: `True`
- Transcript available: `True`
- Bundled trajectory: [link](../traces/csb_org_migration_haiku_20260226_035628_variance--mcp-remote-direct--mcp_CCX-migration-117_5SKmFA/trajectory.json)

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 428.0 |
| Agent execution seconds | 103.4 |
| Input tokens | 762,693 |
| Output tokens | 3,819 |
| Cache tokens | 762,484 |
| Tool calls (total) | 6 |
| Tool calls (MCP) | 5 |
| Tool calls (local) | 1 |
| MCP ratio | 0.833 |
| keyword_search calls | - |
| nls_search calls | - |
| deepsearch calls | - |
| `result.json` SHA256 | `3963a194043705eebc3e311e144103e927ea62c37bd42d0e8ae0eef21355bb98` |
| `trajectory.json` SHA256 | `59d119764d200bfb57a51e379dc97f48d6dab6267ecc763393bbfec1ed331e28` |
| transcript SHA256 | `c8530b145f775be2a760fbfaaeae71259f895781ae0b0bfc74ca23736aa3481b` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `mcp__sourcegraph__sg_keyword_search` | 3 |
| `Write` | 1 |
| `mcp__sourcegraph__sg_nls_search` | 1 |
| `mcp__sourcegraph__sg_read_file` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_nls_search` |
| `Write` |
