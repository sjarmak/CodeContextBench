# Validation Result Schema

Canonical tasks should converge on a structured verifier sidecar at
`/logs/verifier/validation_result.json` in addition to the required
`/logs/verifier/reward.txt`.

This schema standardizes verifier semantics across scalar-only shell verifiers,
answer.json artifact verifiers, repo-state verifiers, and oracle-based promoted
tasks. It is intentionally simple enough to emit from shell or Python.

This schema is the canonical semantic contract for hybrid evaluation. It
applies whether the task is scored from repo state, native `answer.json`,
bridge-mode structured output, or another family-specific artifact contract.
It does not imply that every canonical task uses the same output artifact.

## Required Top-Level Fields

Every canonical `validation_result.json` should emit these keys, even when the
verifier fails or the run is invalid:

| Field | Type | Meaning |
|-------|------|---------|
| `schema_version` | string | Schema identifier. Current proposal: `validation_result.v1alpha1` |
| `status` | string | One of `scored`, `invalid_output`, `verifier_error` |
| `scorable` | boolean | `true` when the verifier had enough task output to score the run |
| `scorer_family` | string | Normalized verifier family (`oracle_checks`, `test_ratio`, `f1_hybrid`, etc.) |
| `reward` | number | Canonical scalar reward in `[0.0, 1.0]` |
| `pass_threshold` | number | Family/task policy threshold associated with `passed` |
| `passed` | boolean | Authoritative pass/fail flag for the task outcome |
| `output_contract` | object | Published verifier-facing output mode and primary artifact path |
| `sub_scores` | object | Per-check or per-component scores. Use `{}` when the family is scalar-only |
| `failure` | object or `null` | Structured failure/error context. `null` for scored runs |

Downstream consumers should treat `passed` as authoritative. `pass_threshold`
is included so reporting can preserve task policy, but parsers should not
recompute `passed` from `reward` alone.

Likewise, consumers should not infer artifact policy from `reward` or from the
presence of `validation_result.json`; the authoritative artifact semantics live
under `output_contract`.

## Required `output_contract` Fields

`output_contract` should always contain:

| Field | Type | Meaning |
|-------|------|---------|
| `mode` | string | One of `answer_json_native`, `answer_json_bridge`, `repo_state`, `solution_json`, `report_markdown`, `unspecified` |
| `primary_path` | string or `null` | Primary artifact path the verifier expected, if any |
| `required_artifact` | boolean | Whether a missing primary artifact makes the run unscorable |

`output_contract` is the bridge between the universal verifier contract and
family-specific task IO. Reporting and validation should use it instead of
assuming that every canonical task expects `/workspace/answer.json`.

## Failure Object

When `status != "scored"`, `failure` should be populated with:

| Field | Type | Meaning |
|-------|------|---------|
| `code` | string | Stable machine-readable error code (`missing_required_output`, `invalid_json`, `verifier_exception`, etc.) |
| `message` | string | Human-readable summary |
| `stage` | string | Usually `output_validation`, `scoring`, or `verifier_runtime` |

`reward` should still be written as `0.0` so existing Harbor/reporting flows do
not break while migration is in progress.

## Optional Fields

These fields are recommended when available:

- `details`: family-specific raw verifier data or diagnostics
- `artifacts`: paths to helper files emitted by the verifier
- `timing`: verifier-local timing if a family captures it
- `legacy`: compatibility payloads preserved for existing readers

## Family Mapping

Current canonical verifier families should map into the schema as follows:

| Family | Canonical `reward` | Recommended `sub_scores` |
|-------|---------------------|--------------------------|
| `oracle_checks` | suite-weighted composite | one entry per oracle check (`file_set_match`, `symbol_resolution`, `dependency_chain`, `keyword_presence`, `provenance`, `json_schema_match`, `test_ratio`) |
| `semantic_retrieval_qa` | primary QA correctness score | `correct_function`, `correct_path`, `justification_score` |
| `f1_hybrid` | blended detection/fix score | `detection_f1`, `fix_score` |
| `f1` | F1 score | `precision`, `recall`, `f1` |
| `test_ratio` | pass ratio | `tests_passed_ratio` plus counts in `details` |
| `diff_similarity` | diff similarity composite | `file_recall`, `line_recall`, `line_precision` |
| `semantic_similarity` | similarity score | `similarity` |
| `checklist` | weighted checklist score | stable check ids under `sub_scores.checks.*` |
| `ir_checklist` | blended retrieval/checklist score | retrieval-oriented check ids under `sub_scores.checks.*` |
| `find_and_prove` | composite regression-proof score | stable assertion ids under `sub_scores.checks.*` |
| `repo_state_heuristic` | repo-state score | stable assertion ids under `sub_scores.checks.*` |
| `continuous` | family-defined continuous score | `continuous_score` or family-specific metric key |
| `binary` | `0.0` or `1.0` | `binary_pass` |

The family determines the expected `sub_scores` shape, but not the top-level
contract. The top-level keys stay fixed across all families.

## Migration Rules

Normalize current canonical tasks using these rules:

1. Existing `validation_result.json` payloads:
   Preserve legacy fields if needed, but add the canonical required keys.
2. Existing `reward.json` payloads:
   Wrap the scalar score into the canonical schema and keep the old file only as
   a temporary compatibility artifact.
3. `reward.txt`-only tasks:
   Keep `reward.txt`, add `validation_result.json`, and emit `sub_scores={}` if
   the family has no natural breakdown today.
4. Missing required task output:
   Emit `status="invalid_output"`, `scorable=false`, `reward=0.0`,
   `passed=false`, and a populated `failure` object.
5. Verifier exceptions:
   Emit `status="verifier_error"`, `scorable=false`, `reward=0.0`,
   `passed=false`, and a populated `failure` object.

## Minimal Scored Example

```json
{
  "schema_version": "validation_result.v1alpha1",
  "status": "scored",
  "scorable": true,
  "scorer_family": "test_ratio",
  "reward": 0.75,
  "pass_threshold": 0.0,
  "passed": true,
  "output_contract": {
    "mode": "repo_state",
    "primary_path": null,
    "required_artifact": false
  },
  "sub_scores": {},
  "failure": null
}
```

## Minimal Invalid-Output Example

```json
{
  "schema_version": "validation_result.v1alpha1",
  "status": "invalid_output",
  "scorable": false,
  "scorer_family": "oracle_checks",
  "reward": 0.0,
  "pass_threshold": 0.0,
  "passed": false,
  "output_contract": {
    "mode": "answer_json_native",
    "primary_path": "/workspace/answer.json",
    "required_artifact": true
  },
  "sub_scores": {},
  "failure": {
    "code": "missing_required_output",
    "message": "answer.json not found at /workspace/answer.json",
    "stage": "output_validation"
  }
}
```
