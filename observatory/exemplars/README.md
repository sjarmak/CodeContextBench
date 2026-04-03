# Observatory Exemplars

Hand-annotated example annotations demonstrating each taxonomy category.
Each file is a valid annotation document conforming to `annotation_schema.json`.

## Exemplar Index

| File                                  | Categories Demonstrated                                                       |
| ------------------------------------- | ----------------------------------------------------------------------------- |
| `01_retrieval_failure.json`           | `retrieval_failure`                                                           |
| `02_query_churn.json`                 | `query_churn`, `retrieval_failure`                                            |
| `03_wrong_tool_choice.json`           | `wrong_tool_choice`                                                           |
| `04_missing_code_navigation.json`     | `missing_code_navigation`, `incomplete_solution`                              |
| `05_decomposition_failure.json`       | `decomposition_failure`                                                       |
| `06_edit_verify_loop_failure.json`    | `edit_verify_loop_failure`                                                    |
| `07_stale_context.json`               | `stale_context`                                                               |
| `08_multi_repo_scope_failure.json`    | `multi_repo_scope_failure`                                                    |
| `09_local_remote_mismatch.json`       | `local_remote_mismatch`                                                       |
| `10_verifier_mismatch.json`           | `verifier_mismatch`                                                           |
| `11_over_exploration.json`            | `over_exploration`                                                            |
| `12_incomplete_solution.json`         | `incomplete_solution`                                                         |
| `13_near_miss.json`                   | `near_miss`                                                                   |
| `14_minimal_progress.json`            | `minimal_progress`                                                            |
| `15_exception_crash.json`             | `exception_crash`                                                             |
| `16_success_via_code_nav.json`        | `success_via_code_nav`                                                        |
| `17_success_via_semantic_search.json` | `success_via_semantic_search`                                                 |
| `18_success_via_local_exec.json`      | `success_via_local_exec`                                                      |
| `19_success_via_commit_context.json`  | `success_via_commit_context`                                                  |
| `20_success_via_decomposition.json`   | `success_via_decomposition`                                                   |
| `21_insufficient_provenance.json`     | `insufficient_provenance`                                                     |
| `22_rate_limited_run.json`            | `rate_limited_run`                                                            |
| `23_task_ambiguity.json`              | `task_ambiguity`                                                              |
| `24_multi_category_failure.json`      | `decomposition_failure`, `multi_repo_scope_failure`, `over_exploration`       |
| `25_multi_category_success.json`      | `success_via_code_nav`, `success_via_local_exec`, `success_via_decomposition` |

## Category Coverage

All 23 taxonomy categories are covered across the exemplar set:

**Failure categories (16):** retrieval_failure, query_churn, wrong_tool_choice,
missing_code_navigation, decomposition_failure, edit_verify_loop_failure,
stale_context, multi_repo_scope_failure, local_remote_mismatch,
verifier_mismatch, over_exploration, incomplete_solution, near_miss,
minimal_progress, exception_crash

**Success categories (5):** success_via_code_nav, success_via_semantic_search,
success_via_local_exec, success_via_commit_context, success_via_decomposition

**Neutral categories (3):** insufficient_provenance, rate_limited_run,
task_ambiguity

## Usage

Validate all exemplars against the schema:

```bash
for f in observatory/exemplars/*.json; do
  python -m observatory validate --annotations "$f"
done
```
