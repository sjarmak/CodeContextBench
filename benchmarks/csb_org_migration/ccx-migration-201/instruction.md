# Envoy xDS v2 to v3 API Migration

## Your Task

Find all C++ source files in envoyproxy/envoy that implement both xDS v2 and v3 API handling: the versioned proto type conversion, the v2-to-v3 field renames (e.g., DiscoveryRequest), and the dual-version subscription handling in the ADS gRPC server.

## Context

You are working on a codebase task involving repos from the migration domain.

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
    {"repo": "org/repo-name", "path": "relative/path/to/file.go"}
  ],
  "symbols": [
    {"repo": "org/repo-name", "path": "relative/path/to/file.go", "symbol": "SymbolName"}
  ],
  "chain": [
    {"repo": "org/repo-name", "path": "relative/path/to/file.go", "symbol": "FunctionName"}
  ],
  "text": "Narrative explanation of your findings, citing repos and file paths."
}
```

Include only the fields relevant to this task. Your answer is evaluated against a closed-world oracle — completeness matters.

## Evaluation

Your answer will be scored on:
- **File recall and precision**: Did you find all relevant files?
