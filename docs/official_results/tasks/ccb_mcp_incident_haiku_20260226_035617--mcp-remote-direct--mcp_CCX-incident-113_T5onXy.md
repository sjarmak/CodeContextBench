# mcp_CCX-incident-113_T5onXy (mcp-remote-direct)

- Run: `csb_org_incident_haiku_20260226_035617`
- Status: `failed`
- Reward: `0.0000`
- Audit JSON: [link](../audits/csb_org_incident_haiku_20260226_035617--mcp-remote-direct--mcp_CCX-incident-113_T5onXy.json)
- Trajectory available: `True`
- Transcript available: `True`
- Bundled trajectory: [link](../traces/csb_org_incident_haiku_20260226_035617--mcp-remote-direct--mcp_CCX-incident-113_T5onXy/trajectory.json)

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 814.0 |
| Agent execution seconds | 276.0 |
| Input tokens | 6,598,383 |
| Output tokens | 16,487 |
| Cache tokens | 6,597,591 |
| Tool calls (total) | 34 |
| Tool calls (MCP) | 28 |
| Tool calls (local) | 6 |
| MCP ratio | 0.824 |
| keyword_search calls | 10 |
| nls_search calls | 4 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `c3c49e3db491ac3e30982b8b2c4d1220aaefb8af958308b78d03be75c4b81f24` |
| `trajectory.json` SHA256 | `60fe62be6f517b106c5a6db9a73849c2a1efe7151aa3d4d9bdbc09d846be3e17` |
| transcript SHA256 | `de3bda870c05b44d98e44aa50bcfdc9e8da484435ee17d998e168ca613595dc0` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `mcp__sourcegraph__sg_read_file` | 12 |
| `mcp__sourcegraph__sg_keyword_search` | 10 |
| `Bash` | 4 |
| `mcp__sourcegraph__sg_nls_search` | 4 |
| `Write` | 2 |
| `mcp__sourcegraph__sg_list_files` | 1 |
| `mcp__sourcegraph__sg_list_repos` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `Bash` |
| `mcp__sourcegraph__sg_list_repos` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_nls_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_nls_search` |
| `mcp__sourcegraph__sg_keyword_search` |
