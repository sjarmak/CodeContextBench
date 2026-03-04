# csb_sdlc_secure_haiku_20260302_221730

## baseline-local-direct

- Valid tasks: `10`
- Mean reward: `0.499`
- Pass rate: `0.800`

| Task | Status | Reward | MCP Ratio | Tool Calls | Trace |
|---|---|---:|---:|---:|---|
| [curl-vuln-reachability-001](../tasks/csb_sdlc_secure_haiku_20260302_221730--baseline-local-direct--curl-vuln-reachability-001--95450f43bb.html) | `failed` | 0.000 | - | - | traj, tx |
| [grpcurl-transitive-vuln-001](../tasks/csb_sdlc_secure_haiku_20260302_221730--baseline-local-direct--grpcurl-transitive-vuln-001--1667ab6fc3.html) | `failed` | 0.000 | - | - | traj, tx |
| [curl-cve-triage-001](../tasks/csb_sdlc_secure_haiku_20260302_221730--baseline-local-direct--curl-cve-triage-001--e9b3a0cf0b.html) | `passed` | 0.940 | 0.000 | 9 | traj, tx |
| [django-audit-trail-implement-001](../tasks/csb_sdlc_secure_haiku_20260302_221730--baseline-local-direct--django-audit-trail-implement-001--dae896746b.html) | `passed` | 0.800 | 0.000 | 67 | traj, tx |
| [django-cross-team-boundary-001](../tasks/csb_sdlc_secure_haiku_20260302_221730--baseline-local-direct--django-cross-team-boundary-001--2063cd0a54.html) | `passed` | 0.300 | 0.000 | 52 | traj, tx |
| [django-repo-scoped-access-001](../tasks/csb_sdlc_secure_haiku_20260302_221730--baseline-local-direct--django-repo-scoped-access-001--d162b6accd.html) | `passed` | 1.000 | 0.000 | 55 | traj, tx |
| [django-role-based-access-001](../tasks/csb_sdlc_secure_haiku_20260302_221730--baseline-local-direct--django-role-based-access-001--ca6995e8a4.html) | `passed` | 0.400 | 0.000 | 94 | traj, tx |
| [flipt-degraded-context-fix-001](../tasks/csb_sdlc_secure_haiku_20260302_221730--baseline-local-direct--flipt-degraded-context-fix-001--680669c94a.html) | `passed` | 0.250 | 0.000 | 107 | traj, tx |
| [flipt-repo-scoped-access-001](../tasks/csb_sdlc_secure_haiku_20260302_221730--baseline-local-direct--flipt-repo-scoped-access-001--6c3beedc27.html) | `passed` | 0.500 | 0.000 | 32 | traj, tx |
| [kafka-sasl-auth-audit-001](../tasks/csb_sdlc_secure_haiku_20260302_221730--baseline-local-direct--kafka-sasl-auth-audit-001--6a05fae4ae.html) | `passed` | 0.800 | 0.000 | 30 | traj, tx |

## mcp-remote-direct

- Valid tasks: `8`
- Mean reward: `0.805`
- Pass rate: `1.000`

| Task | Status | Reward | MCP Ratio | Tool Calls | Trace |
|---|---|---:|---:|---:|---|
| [mcp_curl-cve-triage-001_nkn2ep](../tasks/csb_sdlc_secure_haiku_20260302_221730--mcp-remote-direct--mcp_curl-cve-triage-001_nkn2ep--2736b005bc.html) | `passed` | 0.940 | 0.833 | 6 | traj, tx |
| [mcp_curl-vuln-reachability-001_bzcvms](../tasks/csb_sdlc_secure_haiku_20260302_221730--mcp-remote-direct--mcp_curl-vuln-reachability-001_bzcvms--12128ee680.html) | `passed` | 0.710 | 0.892 | 37 | traj, tx |
| [mcp_django-cross-team-boundary-001_oxflgu](../tasks/csb_sdlc_secure_haiku_20260302_221730--mcp-remote-direct--mcp_django-cross-team-boundary-001_oxflgu--4ed2dceb0d.html) | `passed` | 0.800 | 0.244 | 78 | traj, tx |
| [mcp_django-legacy-dep-vuln-001_kgnuuj](../tasks/csb_sdlc_secure_haiku_20260302_221730--mcp-remote-direct--mcp_django-legacy-dep-vuln-001_kgnuuj--b46744d897.html) | `passed` | 1.000 | 0.262 | 42 | traj, tx |
| [mcp_django-role-based-access-001_3ryxq7](../tasks/csb_sdlc_secure_haiku_20260302_221730--mcp-remote-direct--mcp_django-role-based-access-001_3ryxq7--99e8cc2f75.html) | `passed` | 0.900 | 0.323 | 93 | traj, tx |
| [mcp_django-sensitive-file-exclusion-001_c7krv8](../tasks/csb_sdlc_secure_haiku_20260302_221730--mcp-remote-direct--mcp_django-sensitive-file-exclusion-001_c7krv8--b5b2cd5409.html) | `passed` | 1.000 | 0.178 | 101 | traj, tx |
| [mcp_flipt-repo-scoped-access-001_prpacb](../tasks/csb_sdlc_secure_haiku_20260302_221730--mcp-remote-direct--mcp_flipt-repo-scoped-access-001_prpacb--3dbe6f3466.html) | `passed` | 0.500 | 0.212 | 52 | traj, tx |
| [mcp_grpcurl-transitive-vuln-001_6gpxwc](../tasks/csb_sdlc_secure_haiku_20260302_221730--mcp-remote-direct--mcp_grpcurl-transitive-vuln-001_6gpxwc--308e238252.html) | `passed` | 0.590 | 0.952 | 21 | traj, tx |
