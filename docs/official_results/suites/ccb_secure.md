# ccb_secure

## Run/Config Summary

| Run | Config | Valid Tasks | Mean Reward | Pass Rate |
|---|---|---:|---:|---:|
| [ccb_secure_haiku_20260224_213146](../runs/ccb_secure_haiku_20260224_213146.md) | `baseline-local-direct` | 2 | 0.500 | 1.000 |
| [ccb_secure_haiku_20260224_213146](../runs/ccb_secure_haiku_20260224_213146.md) | `mcp-remote-direct` | 2 | 0.250 | 0.500 |
| [secure_haiku_20260223_232545](../runs/secure_haiku_20260223_232545.md) | `baseline-local-direct` | 18 | 0.688 | 0.944 |
| [secure_haiku_20260223_232545](../runs/secure_haiku_20260223_232545.md) | `mcp-remote-direct` | 18 | 0.705 | 1.000 |
| [secure_haiku_20260224_011825](../runs/secure_haiku_20260224_011825.md) | `mcp-remote-direct` | 2 | 0.500 | 0.500 |

## Tasks

| Task | Benchmark | Config | Status | Reward | Runs | MCP Ratio |
|---|---|---|---|---:|---:|---:|
| [curl-cve-triage-001](../tasks/secure_haiku_20260223_232545--baseline-local-direct--curl-cve-triage-001.md) | [source](../../benchmarks/ccb_secure/curl-cve-triage-001) | `baseline-local-direct` | `passed` | 0.940 | 2 | 0.000 |
| [sgonly_curl-cve-triage-001](../tasks/secure_haiku_20260223_232545--mcp-remote-direct--sgonly_curl-cve-triage-001.md) | [source](../../benchmarks/ccb_secure/curl-cve-triage-001) | `mcp-remote-direct` | `passed` | 0.940 | 2 | 0.889 |
| [curl-vuln-reachability-001](../tasks/secure_haiku_20260223_232545--baseline-local-direct--curl-vuln-reachability-001.md) | [source](../../benchmarks/ccb_secure/curl-vuln-reachability-001) | `baseline-local-direct` | `passed` | 0.910 | 2 | 0.000 |
| [sgonly_curl-vuln-reachability-001](../tasks/secure_haiku_20260223_232545--mcp-remote-direct--sgonly_curl-vuln-reachability-001.md) | [source](../../benchmarks/ccb_secure/curl-vuln-reachability-001) | `mcp-remote-direct` | `passed` | 0.850 | 2 | 0.960 |
| [django-audit-trail-implement-001](../tasks/secure_haiku_20260223_232545--baseline-local-direct--django-audit-trail-implement-001.md) | [source](../../benchmarks/ccb_secure/django-audit-trail-implement-001) | `baseline-local-direct` | `passed` | 0.550 | 2 | 0.000 |
| [sgonly_django-audit-trail-implement-001](../tasks/secure_haiku_20260223_232545--mcp-remote-direct--sgonly_django-audit-trail-implement-001.md) | [source](../../benchmarks/ccb_secure/django-audit-trail-implement-001) | `mcp-remote-direct` | `passed` | 0.550 | 2 | 0.351 |
| [django-cross-team-boundary-001](../tasks/secure_haiku_20260223_232545--baseline-local-direct--django-cross-team-boundary-001.md) | [source](../../benchmarks/ccb_secure/django-cross-team-boundary-001) | `baseline-local-direct` | `passed` | 0.300 | 2 | 0.000 |
| [sgonly_django-cross-team-boundary-001](../tasks/secure_haiku_20260223_232545--mcp-remote-direct--sgonly_django-cross-team-boundary-001.md) | [source](../../benchmarks/ccb_secure/django-cross-team-boundary-001) | `mcp-remote-direct` | `passed` | 0.500 | 2 | 0.232 |
| [django-csrf-session-audit-001](../tasks/secure_haiku_20260223_232545--baseline-local-direct--django-csrf-session-audit-001.md) | [source](../../benchmarks/ccb_secure/django-csrf-session-audit-001) | `baseline-local-direct` | `passed` | 0.800 | 2 | 0.000 |
| [sgonly_django-csrf-session-audit-001](../tasks/secure_haiku_20260223_232545--mcp-remote-direct--sgonly_django-csrf-session-audit-001.md) | [source](../../benchmarks/ccb_secure/django-csrf-session-audit-001) | `mcp-remote-direct` | `passed` | 0.760 | 2 | 0.947 |
| [django-legacy-dep-vuln-001](../tasks/secure_haiku_20260223_232545--baseline-local-direct--django-legacy-dep-vuln-001.md) | [source](../../benchmarks/ccb_secure/django-legacy-dep-vuln-001) | `baseline-local-direct` | `passed` | 0.900 | 2 | 0.000 |
| [sgonly_django-legacy-dep-vuln-001](../tasks/secure_haiku_20260223_232545--mcp-remote-direct--sgonly_django-legacy-dep-vuln-001.md) | [source](../../benchmarks/ccb_secure/django-legacy-dep-vuln-001) | `mcp-remote-direct` | `passed` | 0.650 | 2 | 0.227 |
| [django-policy-enforcement-001](../tasks/secure_haiku_20260223_232545--baseline-local-direct--django-policy-enforcement-001.md) | [source](../../benchmarks/ccb_secure/django-policy-enforcement-001) | `baseline-local-direct` | `passed` | 0.750 | 2 | 0.000 |
| [sgonly_django-policy-enforcement-001](../tasks/secure_haiku_20260223_232545--mcp-remote-direct--sgonly_django-policy-enforcement-001.md) | [source](../../benchmarks/ccb_secure/django-policy-enforcement-001) | `mcp-remote-direct` | `passed` | 0.750 | 2 | 0.206 |
| [django-repo-scoped-access-001](../tasks/secure_haiku_20260223_232545--baseline-local-direct--django-repo-scoped-access-001.md) | [source](../../benchmarks/ccb_secure/django-repo-scoped-access-001) | `baseline-local-direct` | `passed` | 0.500 | 2 | 0.000 |
| [sgonly_django-repo-scoped-access-001](../tasks/secure_haiku_20260223_232545--mcp-remote-direct--sgonly_django-repo-scoped-access-001.md) | [source](../../benchmarks/ccb_secure/django-repo-scoped-access-001) | `mcp-remote-direct` | `passed` | 0.700 | 2 | 0.561 |
| [django-role-based-access-001](../tasks/ccb_secure_haiku_20260224_213146--baseline-local-direct--django-role-based-access-001.md) | [source](../../benchmarks/ccb_secure/django-role-based-access-001) | `baseline-local-direct` | `passed` | 0.200 | 2 | 0.000 |
| [mcp_django-role-based-access-001_2ERzmK](../tasks/ccb_secure_haiku_20260224_213146--mcp-remote-direct--mcp_django-role-based-access-001_2ERzmK.md) | [source](../../benchmarks/ccb_secure/django-role-based-access-001) | `mcp-remote-direct` | `failed` | 0.000 | 2 | 0.452 |
| [sgonly_django-role-based-access-001](../tasks/secure_haiku_20260224_011825--mcp-remote-direct--sgonly_django-role-based-access-001.md) | [source](../../benchmarks/ccb_secure/django-role-based-access-001) | `mcp-remote-direct` | `failed` | 0.000 | 2 | - |
| [django-sensitive-file-exclusion-001](../tasks/ccb_secure_haiku_20260224_213146--baseline-local-direct--django-sensitive-file-exclusion-001.md) | [source](../../benchmarks/ccb_secure/django-sensitive-file-exclusion-001) | `baseline-local-direct` | `passed` | 0.800 | 2 | 0.000 |
| [mcp_django-sensitive-file-exclusion-001_I216lD](../tasks/ccb_secure_haiku_20260224_213146--mcp-remote-direct--mcp_django-sensitive-file-exclusion-001_I216lD.md) | [source](../../benchmarks/ccb_secure/django-sensitive-file-exclusion-001) | `mcp-remote-direct` | `passed` | 0.500 | 2 | 0.352 |
| [sgonly_django-sensitive-file-exclusion-001](../tasks/secure_haiku_20260224_011825--mcp-remote-direct--sgonly_django-sensitive-file-exclusion-001.md) | [source](../../benchmarks/ccb_secure/django-sensitive-file-exclusion-001) | `mcp-remote-direct` | `passed` | 1.000 | 2 | 0.368 |
| [envoy-cve-triage-001](../tasks/secure_haiku_20260223_232545--baseline-local-direct--envoy-cve-triage-001.md) | [source](../../benchmarks/ccb_secure/envoy-cve-triage-001) | `baseline-local-direct` | `passed` | 0.900 | 2 | 0.000 |
| [sgonly_envoy-cve-triage-001](../tasks/secure_haiku_20260223_232545--mcp-remote-direct--sgonly_envoy-cve-triage-001.md) | [source](../../benchmarks/ccb_secure/envoy-cve-triage-001) | `mcp-remote-direct` | `passed` | 1.000 | 2 | 0.963 |
| [envoy-vuln-reachability-001](../tasks/secure_haiku_20260223_232545--baseline-local-direct--envoy-vuln-reachability-001.md) | [source](../../benchmarks/ccb_secure/envoy-vuln-reachability-001) | `baseline-local-direct` | `passed` | 0.620 | 2 | 0.000 |
| [sgonly_envoy-vuln-reachability-001](../tasks/secure_haiku_20260223_232545--mcp-remote-direct--sgonly_envoy-vuln-reachability-001.md) | [source](../../benchmarks/ccb_secure/envoy-vuln-reachability-001) | `mcp-remote-direct` | `passed` | 0.560 | 2 | 0.923 |
| [flipt-degraded-context-fix-001](../tasks/secure_haiku_20260223_232545--baseline-local-direct--flipt-degraded-context-fix-001.md) | [source](../../benchmarks/ccb_secure/flipt-degraded-context-fix-001) | `baseline-local-direct` | `passed` | 0.600 | 2 | 0.000 |
| [sgonly_flipt-degraded-context-fix-001](../tasks/secure_haiku_20260223_232545--mcp-remote-direct--sgonly_flipt-degraded-context-fix-001.md) | [source](../../benchmarks/ccb_secure/flipt-degraded-context-fix-001) | `mcp-remote-direct` | `passed` | 0.250 | 2 | 0.333 |
| [flipt-repo-scoped-access-001](../tasks/secure_haiku_20260223_232545--baseline-local-direct--flipt-repo-scoped-access-001.md) | [source](../../benchmarks/ccb_secure/flipt-repo-scoped-access-001) | `baseline-local-direct` | `passed` | 0.600 | 2 | 0.000 |
| [sgonly_flipt-repo-scoped-access-001](../tasks/secure_haiku_20260223_232545--mcp-remote-direct--sgonly_flipt-repo-scoped-access-001.md) | [source](../../benchmarks/ccb_secure/flipt-repo-scoped-access-001) | `mcp-remote-direct` | `passed` | 0.600 | 2 | 0.184 |
| [golang-net-cve-triage-001](../tasks/secure_haiku_20260223_232545--baseline-local-direct--golang-net-cve-triage-001.md) | [source](../../benchmarks/ccb_secure/golang-net-cve-triage-001) | `baseline-local-direct` | `passed` | 0.800 | 2 | 0.000 |
| [sgonly_golang-net-cve-triage-001](../tasks/secure_haiku_20260223_232545--mcp-remote-direct--sgonly_golang-net-cve-triage-001.md) | [source](../../benchmarks/ccb_secure/golang-net-cve-triage-001) | `mcp-remote-direct` | `passed` | 0.800 | 2 | 0.852 |
| [grpcurl-transitive-vuln-001](../tasks/secure_haiku_20260223_232545--baseline-local-direct--grpcurl-transitive-vuln-001.md) | [source](../../benchmarks/ccb_secure/grpcurl-transitive-vuln-001) | `baseline-local-direct` | `failed` | 0.000 | 2 | 0.000 |
| [sgonly_grpcurl-transitive-vuln-001](../tasks/secure_haiku_20260223_232545--mcp-remote-direct--sgonly_grpcurl-transitive-vuln-001.md) | [source](../../benchmarks/ccb_secure/grpcurl-transitive-vuln-001) | `mcp-remote-direct` | `passed` | 0.670 | 2 | 0.952 |
| [kafka-sasl-auth-audit-001](../tasks/secure_haiku_20260223_232545--baseline-local-direct--kafka-sasl-auth-audit-001.md) | [source](../../benchmarks/ccb_secure/kafka-sasl-auth-audit-001) | `baseline-local-direct` | `passed` | 0.860 | 2 | 0.000 |
| [sgonly_kafka-sasl-auth-audit-001](../tasks/secure_haiku_20260223_232545--mcp-remote-direct--sgonly_kafka-sasl-auth-audit-001.md) | [source](../../benchmarks/ccb_secure/kafka-sasl-auth-audit-001) | `mcp-remote-direct` | `passed` | 0.760 | 2 | 0.960 |
| [kafka-vuln-reachability-001](../tasks/secure_haiku_20260223_232545--baseline-local-direct--kafka-vuln-reachability-001.md) | [source](../../benchmarks/ccb_secure/kafka-vuln-reachability-001) | `baseline-local-direct` | `passed` | 0.860 | 2 | 0.000 |
| [sgonly_kafka-vuln-reachability-001](../tasks/secure_haiku_20260223_232545--mcp-remote-direct--sgonly_kafka-vuln-reachability-001.md) | [source](../../benchmarks/ccb_secure/kafka-vuln-reachability-001) | `mcp-remote-direct` | `passed` | 0.920 | 2 | 0.667 |
| [postgres-client-auth-audit-001](../tasks/secure_haiku_20260223_232545--baseline-local-direct--postgres-client-auth-audit-001.md) | [source](../../benchmarks/ccb_secure/postgres-client-auth-audit-001) | `baseline-local-direct` | `passed` | 0.740 | 2 | 0.000 |
| [sgonly_postgres-client-auth-audit-001](../tasks/secure_haiku_20260223_232545--mcp-remote-direct--sgonly_postgres-client-auth-audit-001.md) | [source](../../benchmarks/ccb_secure/postgres-client-auth-audit-001) | `mcp-remote-direct` | `passed` | 0.770 | 2 | 0.974 |
| [wish-transitive-vuln-001](../tasks/secure_haiku_20260223_232545--baseline-local-direct--wish-transitive-vuln-001.md) | [source](../../benchmarks/ccb_secure/wish-transitive-vuln-001) | `baseline-local-direct` | `passed` | 0.760 | 2 | 0.000 |
| [sgonly_wish-transitive-vuln-001](../tasks/secure_haiku_20260223_232545--mcp-remote-direct--sgonly_wish-transitive-vuln-001.md) | [source](../../benchmarks/ccb_secure/wish-transitive-vuln-001) | `mcp-remote-direct` | `passed` | 0.660 | 2 | 0.938 |

## Multi-Run Variance

Tasks with multiple valid runs (3 task/config pairs).

| Task | Benchmark | Config | Runs | Mean | Std | Individual Rewards |
|---|---|---|---:|---:|---:|---|
| django-role-based-access-001 | [source](../../benchmarks/ccb_secure/django-role-based-access-001) | `baseline-local-direct` | 2 | 0.200 | 0.000 | 0.200, 0.200 |
| django-sensitive-file-exclusion-001 | [source](../../benchmarks/ccb_secure/django-sensitive-file-exclusion-001) | `baseline-local-direct` | 2 | 0.800 | 0.000 | 0.800, 0.800 |
| django-sensitive-file-exclusion-001 | [source](../../benchmarks/ccb_secure/django-sensitive-file-exclusion-001) | `mcp-remote-direct` | 2 | 0.750 | 0.354 | 1.000, 0.500 |
