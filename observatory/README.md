# Agent Reliability Observatory

The Agent Reliability Observatory is a structured framework for analyzing
_why_ coding agents succeed or fail on benchmark tasks. It provides a
taxonomy of 23 behavioral categories, a JSON schema for machine-readable
annotations, and tooling to extract signals from agent trajectories,
annotate trials, and generate reliability reports.

## Overview

When a coding agent attempts a benchmark task, the raw outcome (pass/fail,
partial score) tells you _what_ happened but not _why_. The Observatory
bridges this gap by:

1. **Extracting signals** from trial artifacts (result.json, trajectory.json,
   task_metrics.json) into a flat feature vector.
2. **Annotating** each trial with one or more taxonomy categories that explain
   the behavioral pattern observed.
3. **Reporting** aggregate reliability findings across runs, models, and
   configurations.

Annotations can be produced by heuristic rules, LLM-assisted analysis,
trained classifiers, or manual review. The schema supports all annotator
types and tracks provenance.

## Taxonomy v1.0.0

The taxonomy organizes agent behaviors into three polarities:

| Polarity    | Count | Purpose                                         |
| ----------- | ----- | ----------------------------------------------- |
| **failure** | 16    | Explains why the agent failed or underperformed |
| **success** | 5     | Explains which strategy led to success          |
| **neutral** | 2     | Contextual factors that affect interpretation   |

### Failure Categories

| Category                   | Description                                                                  |
| -------------------------- | ---------------------------------------------------------------------------- |
| `retrieval_failure`        | Relevant code was not found despite existing in the repository               |
| `query_churn`              | Many search queries issued without converging on relevant code               |
| `wrong_tool_choice`        | Inappropriate tool used for the task (e.g., grep instead of find-references) |
| `missing_code_navigation`  | Failed to use go-to-definition or find-references when needed                |
| `decomposition_failure`    | Failed to decompose a multi-step task into a viable plan                     |
| `edit_verify_loop_failure` | Stuck in an edit-test-fail cycle without converging                          |
| `stale_context`            | Operated on outdated information within the same session                     |
| `multi_repo_scope_failure` | Failed on a task spanning multiple packages or modules                       |
| `local_remote_mismatch`    | Execution environment did not match task requirements                        |
| `verifier_mismatch`        | Test harness produced a misleading result (false positive/negative)          |
| `over_exploration`         | Excessive tool calls without meaningful progress                             |
| `incomplete_solution`      | Partial fix addressing some but not all aspects of the task                  |
| `near_miss`                | Close to full solution (reward >= 0.5) but a final piece is missing          |
| `minimal_progress`         | Some progress but far short of a solution (reward < 0.5)                     |
| `exception_crash`          | Run terminated due to an unhandled exception or crash                        |

### Success Categories

| Category                      | Description                                                          |
| ----------------------------- | -------------------------------------------------------------------- |
| `success_via_code_nav`        | Succeeded using go-to-definition, find-references, or symbol search  |
| `success_via_semantic_search` | Succeeded using NLS or deep search to find relevant code             |
| `success_via_local_exec`      | Succeeded via a tight edit-execute-verify loop                       |
| `success_via_commit_context`  | Succeeded by leveraging git history or blame information             |
| `success_via_decomposition`   | Succeeded by correctly decomposing a complex task into ordered steps |

### Neutral Categories

| Category                  | Description                                                  |
| ------------------------- | ------------------------------------------------------------ |
| `insufficient_provenance` | Correct result but reasoning trace does not clearly show how |
| `rate_limited_run`        | Run degraded by rate limiting or infrastructure issues       |
| `task_ambiguity`          | Task specification was ambiguous or underspecified           |

## Usage

### Reading an Annotation File

Annotation files conform to `annotation_schema.json`. Each file contains a
list of per-trial annotations:

```json
{
  "schema_version": "observatory-annotation-v1",
  "taxonomy_version": "1.0.0",
  "generated_at": "2026-03-15T10:30:00+00:00",
  "annotator": {
    "type": "heuristic",
    "identity": "observatory.annotator v0.1"
  },
  "annotations": [
    {
      "task_id": "django__django-16527",
      "trial_path": "runs/official/_raw/csb_swebench_sonnet_20260310/baseline/2026-03-10__14-22-01/django__django-16527__a1b2c3d",
      "reward": 0.0,
      "passed": false,
      "categories": [
        {
          "name": "retrieval_failure",
          "confidence": 0.6,
          "evidence": "reward=0.0, total_search_calls=5 (>3), ttfr=None (never found relevant file)"
        },
        {
          "name": "query_churn",
          "confidence": 0.6,
          "evidence": "query_churn_count=7 (>=4 distinct queries)"
        }
      ]
    }
  ]
}
```

Each annotation in the `annotations` array has:

- **task_id**: The benchmark task identifier.
- **trial_path**: Path to the trial directory containing raw artifacts.
- **reward**: Final verifier score (0.0 to 1.0).
- **passed**: Whether the trial passed (reward > 0).
- **categories**: List of assigned taxonomy categories, each with a `name`,
  `confidence` (0-1), and optional `evidence` string.

### CLI Commands

```bash
# Extract signals from trial directories
python -m observatory extract --runs-dir runs/official/_raw --output signals.json

# Generate heuristic annotations
python -m observatory annotate --signals signals.json --output annotations.json

# Validate an annotation file against the schema
python -m observatory validate --annotations annotations.json

# Generate a reliability report
python -m observatory report --annotations annotations.json --output reports/
```

### Python API

```python
from observatory.taxonomy import load_taxonomy, valid_category_names
from observatory.signals import extract_signals
from observatory.annotator import annotate_trial

# Load the taxonomy
taxonomy = load_taxonomy()
print(f"Taxonomy v{taxonomy['version']} with {len(taxonomy['categories'])} categories")

# Get all valid category names
names = valid_category_names()
print(f"Valid categories: {sorted(names)}")

# Extract signals from a trial and annotate
signals = extract_signals(Path("runs/official/_raw/.../trial_dir"))
categories = annotate_trial(signals)
for cat in categories:
    print(f"  {cat['name']} (confidence={cat['confidence']:.1f}): {cat['evidence']}")
```

## Exemplars

The `exemplars/` directory contains hand-annotated example annotations
that demonstrate each taxonomy category. These serve as:

- **Reference examples** for annotator calibration
- **Test fixtures** for schema validation
- **Documentation** of what each category looks like in practice

See `exemplars/README.md` for a listing of all exemplars and the categories
they cover.

## Schema Validation

All annotation files should validate against `annotation_schema.json`:

```python
import json
import jsonschema

with open("observatory/annotation_schema.json") as f:
    schema = json.load(f)

with open("my_annotations.json") as f:
    annotations = json.load(f)

jsonschema.validate(instance=annotations, schema=schema)
```

## Citation

If you use the Observatory taxonomy or tooling in your research, please cite:

```bibtex
@misc{codescalebench_observatory_2026,
  title        = {{CodeScaleBench} Agent Reliability Observatory: A Taxonomy of
                  Coding Agent Behavioral Patterns},
  author       = {{CodeScaleBench Team}},
  year         = {2026},
  howpublished = {\url{https://github.com/sourcegraph/CodeScaleBench}},
  note         = {Taxonomy v1.0.0}
}
```

## File Reference

| File                     | Purpose                                                                       |
| ------------------------ | ----------------------------------------------------------------------------- |
| `taxonomy_v1.yaml`       | Category definitions (name, description, polarity, detection_hints, examples) |
| `annotation_schema.json` | JSON Schema for annotation files                                              |
| `taxonomy.py`            | Taxonomy loader and validator                                                 |
| `annotator.py`           | Heuristic rule-based annotator                                                |
| `llm_annotator.py`       | LLM-assisted annotator (Claude)                                               |
| `classifier.py`          | Trained per-category classifier                                               |
| `ensemble.py`            | Two-tier ensemble (heuristic + classifier)                                    |
| `signals.py`             | Signal extraction from trial artifacts                                        |
| `report.py`              | Reliability report generator                                                  |
| `cli.py`                 | Command-line interface                                                        |
| `exemplars/`             | Hand-annotated example annotations                                            |
