# Canonical vs Extension Benchmark Policy

## When To Read This

Read this when deciding whether a task belongs in the primary (canonical) benchmark scorecard or the extension set, or when adding new tasks.

## Definitions

- **Canonical core benchmark**: The fixed set of tasks in `configs/core_benchmark_manifest.json` used for all primary harness comparisons and retrieval-impact reporting.
- **Extension benchmark**: All valid tasks in `configs/selected_benchmark_tasks.json` that are NOT in the canonical manifest. Used for secondary analyses, generalization checks, and future promotion.

## Task Classification

| Status | Meaning | Location |
|--------|---------|----------|
| **Canonical** | In `core_benchmark_manifest.json`. Used for primary scorecard. | `configs/core_benchmark_manifest.json` |
| **Extension** | Valid task, not in core manifest. Available for secondary analysis. | `configs/selected_benchmark_tasks.json` minus manifest |
| **Blocked** | Excluded pending verifier remediation (`extension_only` in verifier labels). | `configs/verifier_quality_labels.json` |

## When a Task Is Canonical

A task is canonical when it satisfies all four gates in the Core Inclusion Rubric (`docs/ops/CORE_RETRIEVAL_BENCHMARK_SPEC.md`):

1. **G1** — At least 3 valid paired (baseline + MCP) scored runs
2. **G2** — `repo_approx_loc` populated (cloc-backed)
3. **G3** — `n_repos` populated
4. **G4** — Verifier quality is `core_ready` or `conditional`

AND it was selected into the manifest by `scripts/build_core_manifest.py` based on suite allocation targets and diversity criteria.

## When a Task Is Extension-Only

- Fails any hard gate (G1-G4)
- Verifier quality is `extension_only` (fixed /tmp paths, existence-only checks)
- Not selected during manifest building due to suite cap

Extension tasks are **never deleted**. They remain in the full pool for:
- Secondary analyses and robustness checks
- Future promotion if verifier quality improves
- Exploratory research on new suites or task types

## When a Task Is Blocked

- Verifier has `extension_only` classification in `configs/verifier_quality_labels.json`
- Requires verifier remediation before it can be considered for canonical inclusion
- Remediation path: fix verifier issues, re-run ABC audit, re-generate labels

## Adding New Tasks

New task creation is justified **only** when the current pool cannot satisfy the canonical benchmark goals with sufficient quality. Specifically:

1. A suite's eligible pool is smaller than its allocation target (e.g., `csb_sdlc_understand` has 3/8)
2. A LOC band or n_repos stratum is critically underrepresented
3. A retrieval-sensitive task type has no coverage at all

Do NOT add tasks to:
- Balance abstract category counts
- Increase total task count without quality justification
- Cover suites that are already at or above their allocation target

## Regenerating the Manifest

```bash
# After adding tasks, fixing verifiers, or completing new paired runs:
python3 scripts/generate_verifier_labels.py   # Re-classify verifier quality
python3 scripts/derive_n_repos.py             # Update n_repos metadata
python3 scripts/build_core_manifest.py        # Rebuild the manifest
python3 scripts/validate_core_manifest.py     # Check distribution and power
```

## Related Documents

- `docs/ops/CORE_RETRIEVAL_BENCHMARK_SPEC.md` — Inclusion rubric and allocation targets
- `configs/verifier_quality_scheme.json` — Verifier classification definitions
- `configs/verifier_quality_labels.json` — Per-task verifier labels
- `configs/core_benchmark_manifest.json` — The canonical manifest
- `configs/core_manifest_validation.json` — Distribution and power validation
