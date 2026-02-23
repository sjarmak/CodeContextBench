# Stack Trace Symbol Resolution: rest.Config

## Your Task

A Kubernetes developer is debugging a production issue and encounters the following in a stack trace:

```
goroutine 1 [running]:
k8s.io/client-go/rest.(*Config).DeepCopyInto(...)
        vendor/k8s.io/client-go/rest/config.go:87
```

The developer is starting from the main `kubernetes/kubernetes` repository.
They need to find where `rest.Config` is actually defined (the authoritative source),
not just a vendored copy.

**Specific question**: Find the repository and file path where the `Config` struct is
**defined** (not vendored) in the `rest` package of `k8s.io/client-go`. What is the
exact Go package import path?

## Context

You are working on a codebase task involving symbol resolution across Kubernetes ecosystem repos.
The `kubernetes/kubernetes` repository vendors many dependencies in its `staging/` or `vendor/`
directories, but the authoritative source lives in separate repositories accessible via MCP tools.

## Available Resources

Your ecosystem includes the following repositories:
- `kubernetes/kubernetes` at v1.32.0
- `kubernetes/client-go` at v0.32.0
- `kubernetes/api` at fa23dd3
- `etcd-io/etcd` at v3.5.17

## Output Format

Create a file at `/workspace/answer.json` with your findings in the following structure:

```json
{
  "symbols": [
    {"repo": "sg-evals/kubernetes-client-go", "path": "relative/path/to/file.go", "symbol": "SymbolName"}
  ],
  "text": "Explanation of where Config is defined, the package import path, and why this is the authoritative source."
}
```

**Important**: The `kubernetes/client-go` repository is indexed in Sourcegraph as `sg-evals/kubernetes-client-go`. Use `sg-evals/kubernetes-client-go` as the `repo` value in your answer — the oracle checks for this exact identifier.
**Note**: Sourcegraph MCP tools return repo names with a `github.com/` prefix (e.g., `github.com/sg-evals/kubernetes-client-go`). Strip this prefix in your answer — use `sg-evals/kubernetes-client-go`, NOT `github.com/sg-evals/kubernetes-client-go`.

Your answer is evaluated against a closed-world oracle — the exact repo, path, and symbol name matter.

## Evaluation

Your answer will be scored on:
- **Symbol resolution**: Did you find the correct repo, file, and symbol name for the `Config` struct definition?
