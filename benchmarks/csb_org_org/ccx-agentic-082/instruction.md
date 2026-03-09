# Agentic Correctness: Implement Kubernetes Custom Resource Client

## Your Task

Write a Go file `crd_client.go` that implements a typed client for a custom resource `Widget` (group `example.com`, version `v1`). Your implementation must follow the patterns established in the Kubernetes client-go codebase: 1. Embed or use the `rest.Interface` client from `k8s.io/client-go/rest`. 2. Implement `Create`, `Get`, `List`, and `Delete` methods following the same parameter conventions as `k8s.io/client-go/kubernetes/typed/` clients. 3. Use proper `context.Context` propagation. Write your implementation to `/workspace/crd_client.go`. Also write `/workspace/answer.json` listing the client-go source files you referenced.

## Context

You are working on a codebase task involving repos from the org domain.

## Available Resources

The local `/workspace/` directory contains: sg-evals/kubernetes--v1.32.0, sg-evals/client-go--v0.32.0, sg-evals/api--v0.32.0, sg-evals/etcd-io-etcd.


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
- **Keyword presence**: Are required terms present in your explanation?
