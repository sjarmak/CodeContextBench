# Cross-Org gRPC Service Definition Discovery

## Your Task

Find the gRPC service definitions that are shared between `envoyproxy/envoy` and `grpc/grpc`. Specifically: 1. In `envoyproxy/data-plane-api`, find all `.proto` files that define `service` declarations using `rpc` methods (the xDS service definitions). 2. In `grpc/grpc`, find the source files that implement the `grpc_health_v1.Health` service (the standard gRPC health checking protocol). Report the repo, file path, and service name for each.

## Context

You are working on a codebase task involving repos from the crossorg domain.

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
