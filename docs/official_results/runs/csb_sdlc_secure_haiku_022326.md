# csb_sdlc_secure_haiku_022326

## baseline-local-direct

- Valid tasks: `18`
- Mean reward: `0.688`
- Pass rate: `0.944`

| Task | Status | Reward | MCP Ratio | Tool Calls | Trace |
|---|---|---:|---:|---:|---|
| [grpcurl-transitive-vuln-001](../tasks/csb_sdlc_secure_haiku_022326--baseline--grpcurl-transitive-vuln-001--ef65f28ed6.html) | `failed` | 0.000 | 0.000 | 37 | traj, tx |
| [curl-cve-triage-001](../tasks/csb_sdlc_secure_haiku_022326--baseline--curl-cve-triage-001--669a3e74ff.html) | `passed` | 0.940 | 0.000 | 27 | traj, tx |
| [curl-vuln-reachability-001](../tasks/csb_sdlc_secure_haiku_022326--baseline--curl-vuln-reachability-001--c473c2a092.html) | `passed` | 0.910 | 0.000 | 50 | traj, tx |
| [django-audit-trail-implement-001](../tasks/csb_sdlc_secure_haiku_022326--baseline--django-audit-trail-implement-001--293403a235.html) | `passed` | 0.550 | 0.000 | 73 | traj, tx |
| [django-cross-team-boundary-001](../tasks/csb_sdlc_secure_haiku_022326--baseline--django-cross-team-boundary-001--20936254cb.html) | `passed` | 0.300 | 0.000 | 83 | traj, tx |
| [django-csrf-session-audit-001](../tasks/csb_sdlc_secure_haiku_022326--baseline--django-csrf-session-audit-001--7801793bfd.html) | `passed` | 0.800 | 0.000 | 14 | traj, tx |
| [django-legacy-dep-vuln-001](../tasks/csb_sdlc_secure_haiku_022326--baseline--django-legacy-dep-vuln-001--45a962f902.html) | `passed` | 0.900 | 0.000 | 31 | traj, tx |
| [django-policy-enforcement-001](../tasks/csb_sdlc_secure_haiku_022326--baseline--django-policy-enforcement-001--c36adca521.html) | `passed` | 0.750 | 0.000 | 31 | traj, tx |
| [django-repo-scoped-access-001](../tasks/csb_sdlc_secure_haiku_022326--baseline--django-repo-scoped-access-001--ba7eb48d39.html) | `passed` | 0.500 | 0.000 | 44 | traj, tx |
| [envoy-cve-triage-001](../tasks/csb_sdlc_secure_haiku_022326--baseline--envoy-cve-triage-001--34613f6463.html) | `passed` | 0.900 | 0.000 | 31 | traj, tx |
| [envoy-vuln-reachability-001](../tasks/csb_sdlc_secure_haiku_022326--baseline--envoy-vuln-reachability-001--402442636d.html) | `passed` | 0.620 | 0.000 | 40 | traj, tx |
| [flipt-degraded-context-fix-001](../tasks/csb_sdlc_secure_haiku_022326--baseline--flipt-degraded-context-fix-001--55c974b98d.html) | `passed` | 0.600 | 0.000 | 54 | traj, tx |
| [flipt-repo-scoped-access-001](../tasks/csb_sdlc_secure_haiku_022326--baseline--flipt-repo-scoped-access-001--a1ffeb1981.html) | `passed` | 0.600 | 0.000 | 26 | traj, tx |
| [golang-net-cve-triage-001](../tasks/csb_sdlc_secure_haiku_022326--baseline--golang-net-cve-triage-001--ab32c83aa7.html) | `passed` | 0.800 | 0.000 | 27 | traj, tx |
| [kafka-sasl-auth-audit-001](../tasks/csb_sdlc_secure_haiku_022326--baseline--kafka-sasl-auth-audit-001--263ec912ab.html) | `passed` | 0.860 | 0.000 | 57 | traj, tx |
| [kafka-vuln-reachability-001](../tasks/csb_sdlc_secure_haiku_022326--baseline--kafka-vuln-reachability-001--67a1b9e3fa.html) | `passed` | 0.860 | 0.000 | 31 | traj, tx |
| [postgres-client-auth-audit-001](../tasks/csb_sdlc_secure_haiku_022326--baseline--postgres-client-auth-audit-001--011b3bb5a4.html) | `passed` | 0.740 | 0.000 | 38 | traj, tx |
| [wish-transitive-vuln-001](../tasks/csb_sdlc_secure_haiku_022326--baseline--wish-transitive-vuln-001--6a8f8292ff.html) | `passed` | 0.760 | 0.000 | 24 | traj, tx |

## mcp-remote-direct

- Valid tasks: `18`
- Mean reward: `0.705`
- Pass rate: `1.000`

| Task | Status | Reward | MCP Ratio | Tool Calls | Trace |
|---|---|---:|---:|---:|---|
| [sgonly_curl-cve-triage-001](../tasks/csb_sdlc_secure_haiku_022326--mcp--sgonly_curl-cve-triage-001--6e67ffc3b4.html) | `passed` | 0.940 | 0.889 | 9 | traj, tx |
| [sgonly_curl-vuln-reachability-001](../tasks/csb_sdlc_secure_haiku_022326--mcp--sgonly_curl-vuln-reachability-001--315fdc1ea9.html) | `passed` | 0.850 | 0.960 | 25 | traj, tx |
| [sgonly_django-audit-trail-implement-001](../tasks/csb_sdlc_secure_haiku_022326--mcp--sgonly_django-audit-trail-implement-001--ac2b4b1513.html) | `passed` | 0.550 | 0.351 | 57 | traj, tx |
| [sgonly_django-cross-team-boundary-001](../tasks/csb_sdlc_secure_haiku_022326--mcp--sgonly_django-cross-team-boundary-001--fb68744896.html) | `passed` | 0.500 | 0.232 | 56 | traj, tx |
| [sgonly_django-csrf-session-audit-001](../tasks/csb_sdlc_secure_haiku_022326--mcp--sgonly_django-csrf-session-audit-001--183736e43b.html) | `passed` | 0.760 | 0.947 | 19 | traj, tx |
| [sgonly_django-legacy-dep-vuln-001](../tasks/csb_sdlc_secure_haiku_022326--mcp--sgonly_django-legacy-dep-vuln-001--e25ab28c91.html) | `passed` | 0.650 | 0.227 | 44 | traj, tx |
| [sgonly_django-policy-enforcement-001](../tasks/csb_sdlc_secure_haiku_022326--mcp--sgonly_django-policy-enforcement-001--b14ee4d8ef.html) | `passed` | 0.750 | 0.206 | 63 | traj, tx |
| [sgonly_django-repo-scoped-access-001](../tasks/csb_sdlc_secure_haiku_022326--mcp--sgonly_django-repo-scoped-access-001--bef227e7cc.html) | `passed` | 0.700 | 0.561 | 98 | traj, tx |
| [sgonly_envoy-cve-triage-001](../tasks/csb_sdlc_secure_haiku_022326--mcp--sgonly_envoy-cve-triage-001--796ba64d70.html) | `passed` | 1.000 | 0.963 | 27 | traj, tx |
| [sgonly_envoy-vuln-reachability-001](../tasks/csb_sdlc_secure_haiku_022326--mcp--sgonly_envoy-vuln-reachability-001--69bb83024f.html) | `passed` | 0.560 | 0.923 | 26 | traj, tx |
| [sgonly_flipt-degraded-context-fix-001](../tasks/csb_sdlc_secure_haiku_022326--mcp--sgonly_flipt-degraded-context-fix-001--b8c8e37905.html) | `passed` | 0.250 | 0.333 | 36 | traj, tx |
| [sgonly_flipt-repo-scoped-access-001](../tasks/csb_sdlc_secure_haiku_022326--mcp--sgonly_flipt-repo-scoped-access-001--82886973c6.html) | `passed` | 0.600 | 0.184 | 38 | traj, tx |
| [sgonly_golang-net-cve-triage-001](../tasks/csb_sdlc_secure_haiku_022326--mcp--sgonly_golang-net-cve-triage-001--f0b38f3257.html) | `passed` | 0.800 | 0.852 | 27 | traj, tx |
| [sgonly_grpcurl-transitive-vuln-001](../tasks/csb_sdlc_secure_haiku_022326--mcp--sgonly_grpcurl-transitive-vuln-001--73cbd8bd4d.html) | `passed` | 0.670 | 0.952 | 21 | traj, tx |
| [sgonly_kafka-sasl-auth-audit-001](../tasks/csb_sdlc_secure_haiku_022326--mcp--sgonly_kafka-sasl-auth-audit-001--387d204a82.html) | `passed` | 0.760 | 0.960 | 25 | traj, tx |
| [sgonly_kafka-vuln-reachability-001](../tasks/csb_sdlc_secure_haiku_022326--mcp--sgonly_kafka-vuln-reachability-001--b1edbc8b52.html) | `passed` | 0.920 | 0.667 | 18 | traj, tx |
| [sgonly_postgres-client-auth-audit-001](../tasks/csb_sdlc_secure_haiku_022326--mcp--sgonly_postgres-client-auth-audit-001--504c8a1659.html) | `passed` | 0.770 | 0.974 | 38 | traj, tx |
| [sgonly_wish-transitive-vuln-001](../tasks/csb_sdlc_secure_haiku_022326--mcp--sgonly_wish-transitive-vuln-001--0359f1760f.html) | `passed` | 0.660 | 0.938 | 16 | traj, tx |
