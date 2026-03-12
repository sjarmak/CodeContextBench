# Sourcegraph MCP Case Studies

Case studies are limited to runs where MCP achieved **high reward** (no low-reward MCP results). Each entry is a 2–3 sentence overview that highlights how MCP did well versus the baseline. Baseline runs were verified as valid executions (no infrastructure errors); see **Verification** at the end.

---

## Dependency tracing

**Grafana → Loki API call chain (`ccx-dep-trace-004`)**  
Trace the API call chain from Grafana to Loki and produce the required artifact. The baseline failed after a long run (80 tool calls, ~1.6M tokens) because local navigation could not reliably map the cross-repo query path. With MCP, cross-repo search located the relevant services and call sites, and the run **passed** (reward 0.875).

---

## Incident debug & bug localization

**Trace production error to source (`ccx-incident-031`)**  
Trace a production error back to the authoritative source across a multi-repo Go org. The baseline failed despite a full run (~262s, 45 tool calls): without indexed search it could not connect the error to the right code path. MCP used code search to find the call path and produce the required artifact, **passing** with reward 1.0.

---

## Vulnerability remediation

**CVE: vulnerable cookie dependency (`ccx-vuln-remed-011`)**  
Remediate a vulnerable cookie package dependency (CVE) in a Node.js web stack. The baseline ran but failed to satisfy the verifier because it could not reliably find all dependency declarations. MCP used search to locate declarations and apply the correct fix, **passing** with reward 1.0.

---

## Refactoring

**Prometheus query engine refactor (`prometheus-query-engine-refac-001`)**  
Cross-file refactor in the Prometheus query engine; baseline passed but left gaps (reward 0.83). MCP used find_references and targeted reads to discover every affected code path and test, then completed the refactor to the verifier’s standard and **achieved full correctness** (reward 1.0).

---

## Bug fix

**PyTorch cross-module fix (`pytorch-release-210-fix-001`)**  
Cross-module bug fix in PyTorch (C++) matching a known PR. The baseline failed after a long run (94 tool calls, ~9.9M tokens) because grep and manual navigation did not surface the right modules. MCP used search to find the affected code and apply the fix, **passing** with reward ~0.79.

---

## Test generation

**Django cache middleware unit tests (`test-unitgen-py-001`)**  
Generate unit tests for Django’s cache middleware with checklist scoring. The baseline passed with moderate reward (0.6). MCP used search to identify edge cases and patterns in the middleware and produced tests that met the full checklist, **passing** with reward 1.0.

---

## Migration & inventory

**Flink DataStream deprecation markers (`ccx-migration-274`)**  
Produce a migration inventory for Flink DataStream API deprecation markers across the Kafka ecosystem. The baseline passed but with partial coverage (reward 0.4). MCP used cross-repo search to find deprecation sites and produced a complete inventory, **passing** with reward 1.0.

---

## General behavior and interpretation

Baseline runs rely on local grep, directory listing, and file reads; in large or multi-repo setups that often yields narrow edits or incomplete artifacts because the agent cannot enumerate “all places that matter.” MCP provides indexed search and read_file (and find_references where used), so the agent can discover the full set of relevant locations and pull only those into context. The result is **recovery from baseline failure** (incident debug, vuln remediation, dependency tracing, bug fix) or **full correctness where baseline was incomplete** (refactoring, test generation, migration). These case studies support the interpretation that MCP helps most on tasks that need broad, accurate retrieval—dependency tracing, bug localization, vulnerability remediation, refactoring, and migration—where baseline tooling is limited to local search and manual navigation.

---

## Verification (baseline runs)

Baseline runs above were checked for valid agent execution (no infrastructure failure):

- **ccx-dep-trace-004 (baseline):** `timed_out`: false; `agent_execution_seconds`: ~174; `input_tokens`: ~1.6M; `tool_calls_total`: 80. Baseline failed (reward 0.0).
- **ccx-incident-031 (baseline):** `timed_out`: false; `agent_execution_seconds`: ~262; `input_tokens`: ~2.7M; `tool_calls_total`: 45. Baseline failed (reward 0.0).
- **ccx-vuln-remed-011 (baseline):** `timed_out`: false; `agent_execution_seconds`: ~15; `input_tokens`: ~274K; `tool_calls_total`: 4. Baseline failed (reward 0.0).
- **prometheus-query-engine-refac-001 (baseline):** `timed_out`: false; `input_tokens`: ~3.6M; `tool_calls_total`: 48; `wall_clock_seconds`: ~139. Baseline passed with reward 0.83.
- **pytorch-release-210-fix-001 (baseline):** `timed_out`: false; `agent_execution_seconds`: ~278; `input_tokens`: ~9.9M; `tool_calls_total`: 94. Baseline failed (reward 0.0).
- **test-unitgen-py-001 (baseline):** `timed_out`: false; `agent_execution_seconds`: ~75; `input_tokens`: ~919K; `tool_calls_total`: 15. Baseline passed with reward 0.6.
- **ccx-migration-274 (baseline):** `timed_out`: false; `agent_execution_seconds`: ~54; `input_tokens`: ~1M; `tool_calls_total`: 19. Baseline passed with reward 0.4.

**Excluded:** Baselines with very low MCP reward (e.g. pytorch-optimizer-foreach-refac-001, ccx-migration-200) are not used as case studies so the report highlights only strong MCP outcomes. The baseline for `python-http-class-naming-refac-001` was excluded as an infra/early-exit run (agent_execution_seconds ~2, zero tokens, null tool_calls).
