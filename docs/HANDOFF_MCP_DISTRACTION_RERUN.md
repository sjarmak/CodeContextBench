# Handoff: MCP Distraction Rerun

## Status: BLOCKED on in-flight runs (45 containers active)

## Context

IR analysis on 11 clean SDLC staging runs found **36 tasks where SG_full reward is at least 0.10 below baseline** ("MCP-distracted"). The agent over-reads remote code via Sourcegraph MCP instead of writing local files.

### Root Causes (3 categories)

| Category | Tasks | Root Cause | Fix |
|---|---|---|---|
| Code review Dockerfile bug | 6 | `Dockerfile.sg_only` was write-only (no repo clone, no defect injection) | Already fixed (commit 94cd21db6, Feb 19). Confirmed all 6 have build-requiring Dockerfiles. |
| Genuine MCP distraction | 11 | Agent reads 12-29 remote files via `sg_read_file`, writes few/no local files | V4 preamble "Local File Editing" section added (this session) |
| SG_full=0.0 (infra) | 19 | Rate limits, navprove bugs, misc infra failures | Fresh run + preamble may help |

### Changes Made This Session

1. **V4 preamble updated** (`agents/claude_baseline_agent.py` line 114-121):
   - Added "Local File Editing" section to `V4_PREAMBLE_TEMPLATE`
   - Explains: local files may be truncated, use MCP to read/understand, edit locally, verifier restores full repo
   - Key bullet: "Don't over-read: Reading 20+ remote files without writing code wastes time."

2. **9 new SDLC tasks added** to `configs/selected_benchmark_tasks.json` (157 -> 166 tasks):
   - ccb_build: cgen-deps-install-001
   - ccb_understand: django-composite-field-recover-001, django-template-inherit-recall-001
   - ccb_document: docgen-changelog-001, docgen-changelog-002, docgen-inline-002, docgen-onboard-001
   - ccb_test: test-integration-001, test-unitgen-go-001

3. **Ground truth rebuilt** via `python3 scripts/ir_analysis.py --build-ground-truth` (19 file-level GT entries; the 9 new tasks use rubric scoring, not file-level GT)

4. **Rerun script created** at `configs/rerun_mcp_distracted.sh`

## What to Do Next

### Step 1: Wait for in-flight runs to complete

45 containers are active across build, design, fix, test, secure suites. Check with:
```bash
docker ps --format '{{.Names}}' | grep -c -v 'gitlab\|plane'
```

### Step 2: Run the most impacted suite first (test, --full-only)

The **test** suite is the top priority:
- 7 distracted tasks (most of any suite), including all 6 code review tasks with the Dockerfile fix
- Avg delta: -0.130
- Code review tasks should see the biggest improvement (infra bug, not genuine distraction)

```bash
./configs/rerun_mcp_distracted.sh --suite test --full-only
```

### Step 3: Run debug suite (second priority)

5 distracted tasks, worst avg delta (-0.209). Note: 3 are qutebrowser navprove tasks with known separate bugs (instruction file extension, pytest.ini interference).

```bash
./configs/rerun_mcp_distracted.sh --suite debug --full-only
```

### Step 4: Run remaining suites

```bash
# design: 5 tasks, mild distraction
./configs/rerun_mcp_distracted.sh --suite design --full-only

# document: 5 tasks, doc-gen mild distraction
./configs/rerun_mcp_distracted.sh --suite document --full-only

# secure: 6 tasks, mix of rate-limit failures and genuine distraction
./configs/rerun_mcp_distracted.sh --suite secure --full-only

# build: 3 tasks (includes rust-subtype-relation-refac-001, worst genuine distraction case)
./configs/rerun_mcp_distracted.sh --suite build --full-only

# fix: 1 task
./configs/rerun_mcp_distracted.sh --suite fix --full-only

# understand: 3 tasks
./configs/rerun_mcp_distracted.sh --suite understand --full-only
```

### Step 5: Compare results

After reruns complete:
```bash
# IR analysis on the new run
python3 scripts/ir_analysis.py --runs-dir runs/staging/<new_run_dir> --json

# Compare reward deltas
python3 scripts/compare_configs.py --run runs/staging/<new_run_dir>
```

Key metrics to watch:
- **rust-subtype-relation-refac-001**: Was BL=0.91, SG=0.70 (agent made 1 edit instead of 21). Does the preamble get it to write more?
- **Code review tasks**: Should jump from 0.0 to near-baseline now that Dockerfile.sg_only has defect injection
- **Doc-gen tasks** (k8s-*-doc-gen-001): Mild distraction. Preamble may reduce sg_read_file calls but effect could be small.

## Distracted Tasks Full List (36)

### test (7 tasks) -- PRIORITY 1
| Task | BL | SG | Delta | Notes |
|---|---|---|---|---|
| terraform-code-review-001 | 0.950 | 0.000 | -0.950 | Dockerfile bug |
| kafka-security-review-001 | 0.900 | 0.000 | -0.900 | Dockerfile bug |
| vscode-code-review-001 | 0.830 | 0.000 | -0.830 | Dockerfile bug |
| ghost-code-review-001 | 0.930 | 0.330 | -0.600 | Dockerfile bug |
| envoy-code-review-001 | 0.920 | 0.470 | -0.450 | Dockerfile bug |
| curl-security-review-001 | 1.000 | 0.720 | -0.280 | Dockerfile bug |
| pandas-groupby-perf-001 | 0.905 | 0.325 | -0.580 | Genuine |
| test-unitgen-py-001 | 0.480 | 0.250 | -0.230 | Genuine |

### debug (5 tasks)
| Task | BL | SG | Delta | Notes |
|---|---|---|---|---|
| envoy-duplicate-headers-debug-001 | 0.970 | 0.000 | -0.970 | Infra? |
| istio-xds-destrul-debug-001 | 0.880 | 0.000 | -0.880 | Infra? |
| qutebrowser-download-regression-prove-001 | 0.500 | 0.000 | -0.500 | Navprove bug |
| qutebrowser-bookmark-regression-prove-001 | 0.500 | 0.000 | -0.500 | Navprove bug |
| qutebrowser-tab-regression-prove-001 | 0.500 | 0.000 | -0.500 | Navprove bug |

### design (5 tasks)
| Task | BL | SG | Delta |
|---|---|---|---|
| django-pre-validate-signal-design-001 | 1.000 | 0.000 | -1.000 |
| k8s-dra-allocation-impact-001 | 1.000 | 0.000 | -1.000 |
| camel-routing-arch-001 | 0.850 | 0.000 | -0.850 |
| kafka-flink-streaming-arch-001 | 0.930 | 0.400 | -0.530 |
| flipt-protobuf-metadata-design-001 | 1.000 | 0.480 | -0.520 |

### document (5 tasks)
| Task | BL | SG | Delta |
|---|---|---|---|
| k8s-controller-mgr-doc-gen-001 | 0.730 | 0.300 | -0.430 |
| k8s-applyconfig-doc-gen-001 | 1.000 | 0.650 | -0.350 |
| envoy-migration-doc-gen-001 | 0.880 | 0.630 | -0.250 |
| k8s-clientgo-doc-gen-001 | 0.650 | 0.480 | -0.170 |
| k8s-fairqueuing-doc-gen-001 | 0.240 | 0.100 | -0.140 |

### secure (6 tasks)
| Task | BL | SG | Delta |
|---|---|---|---|
| django-policy-enforcement-001 | 1.000 | 0.000 | -1.000 |
| curl-cve-triage-001 | 0.940 | 0.000 | -0.940 |
| django-sensitive-file-exclusion-001 | 0.800 | 0.000 | -0.800 |
| grpcurl-transitive-vuln-001 | 0.710 | 0.000 | -0.710 |
| flipt-degraded-context-fix-001 | 0.600 | 0.250 | -0.350 |
| django-cross-team-boundary-001 | 0.300 | 0.000 | -0.300 |

### build (3 tasks)
| Task | BL | SG | Delta |
|---|---|---|---|
| flipt-dep-refactor-001 | 0.700 | 0.150 | -0.550 |
| rust-subtype-relation-refac-001 | 0.910 | 0.700 | -0.210 |
| flink-pricing-window-feat-001 | 0.590 | 0.450 | -0.140 |

### fix (1 task)
| Task | BL | SG | Delta |
|---|---|---|---|
| django-modelchoice-fk-fix-001 | 0.550 | 0.000 | -0.550 |

### understand (3 tasks)
| Task | BL | SG | Delta |
|---|---|---|---|
| kafka-message-lifecycle-qa-001 | 1.000 | 0.000 | -1.000 |
| terraform-state-backend-handoff-001 | 0.650 | 0.000 | -0.650 |
| cilium-ebpf-fault-qa-001 | 1.000 | 0.860 | -0.140 |

## Beads Issues

- **CodeContextBench-bmdu** (P1): Rerun 36 MCP-distracted tasks (blocked on CodeContextBench-84jo)
- **CodeContextBench-r8xj** (P1): MCP distraction investigation (open, preamble fix applied)
- **CodeContextBench-84jo** (P1): Rerun 49 errored staging tasks (in progress)
- **CodeContextBench-kt06** (P2): Rerun 54 rate-limited tasks (overlaps with some of these)

## Files Changed

- `agents/claude_baseline_agent.py` — V4 preamble "Local File Editing" section (line 114-121)
- `configs/selected_benchmark_tasks.json` — 9 new task entries (157 -> 166)
- `configs/ground_truth_files.json` — rebuilt (19 entries, unchanged count)
- `configs/rerun_mcp_distracted.sh` — NEW, rerun script for 36 distracted tasks
