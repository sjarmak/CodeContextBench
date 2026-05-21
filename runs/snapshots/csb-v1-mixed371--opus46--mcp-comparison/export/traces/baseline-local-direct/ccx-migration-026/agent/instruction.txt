# Envoy Deprecated v2 API References Migration

## Your Task

Find all files in `envoyproxy/envoy` and `envoyproxy/data-plane-api` that still reference the deprecated Envoy v2 API namespace `envoy.api.v2` (the v2 xDS API was replaced by v3 in Envoy 1.19+). Include `.proto` files, C++ source files, and YAML configuration examples. Exclude files that only mention v2 in changelog or migration documentation.

## Context

You are working on a codebase task involving repos from the migration domain.

## Available Resources

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
