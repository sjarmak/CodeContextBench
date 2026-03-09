# Compliance Audit: Envoy Access Logging Configuration Coverage

## Your Task

Audit the access logging infrastructure in `envoyproxy/envoy`. Find all C++ source files under `source/extensions/access_loggers/` and `source/common/access_log/` that define access log filter implementations or access log sink implementations. Also find the corresponding `.proto` definitions in `envoyproxy/data-plane-api` under `envoy/extensions/access_loggers/`. For each implementation, report whether it supports structured (JSON) logging or only unstructured text logging.

## Context

You are working on a codebase task involving repos from the compliance domain.

## Available Resources

The local `/workspace/` directory contains: sg-evals/envoy--v1.31.2, sg-evals/data-plane-api--84e84367, sg-evals/go-control-plane--71637ad6, sg-evals/grpc--957dba5e.


## Output Format

Use the published task contract:

- `TASK_WORKDIR=/workspace`
- `TASK_REPO_ROOT=/workspace`
- `TASK_OUTPUT=/workspace/answer.json`

Create a file at `TASK_OUTPUT` (`/workspace/answer.json`) with your findings in the following structure:

```json
{
  "files": [
    {"repo": "repo-name", "path": "relative/path/to/file.go"}
  ],
  "symbols": [
    {"repo": "repo-name", "path": "relative/path/to/file.go", "symbol": "SymbolName"}
  ],
  "chain": [
    {"repo": "repo-name", "path": "relative/path/to/file.go", "symbol": "FunctionName"}
  ],
  "text": "Narrative explanation of your findings, citing repos and file paths."
}
```

Include only the fields relevant to this task. Your answer is evaluated against a closed-world oracle — completeness matters.

## Evaluation

Your answer will be scored on:
- **File recall and precision**: Did you find all relevant files?
