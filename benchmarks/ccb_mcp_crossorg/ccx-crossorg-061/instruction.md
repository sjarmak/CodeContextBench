# Cross-Org Interface Implementation Discovery

## Your Task

Your platform team is conducting a cross-organization audit to find all implementations
of a core Kubernetes storage abstraction. The `k8s.io/apiserver/pkg/storage.Interface`
is the standard backend abstraction used by the Kubernetes API server — any project that
embeds a Kubernetes-compatible API layer must implement it.

**Specific question**: Find all Go source files across the repos in this ecosystem that
contain an explicit interface compliance check for `storage.Interface` using the
Go pattern `var _ storage.Interface = (*StructName)(nil)`. For each match, report
the repo, file path, and the struct name that implements the interface.

## Context

This pattern (`var _ InterfaceName = (*TypeName)(nil)`) is used in Go to verify at
compile time that a type implements an interface. Finding all such declarations across
repos from different organizations reveals who has independently implemented the same
storage abstraction — a key signal for platform compatibility audits.

The search should be **exhaustive across all repos in the ecosystem**, not just the
local repo. The interface is defined in the Kubernetes ecosystem but can be implemented
by projects from entirely different organizations.

## Available Resources

The local `/workspace/` directory contains: kubernetes/kubernetes.

**Note:** Additional repositories are accessible via Sourcegraph MCP tools:
- `etcd-io/etcd` (distributed-kv-store)
- `grafana/grafana` (observability-platform)

## Output Format

Create a file at `/workspace/answer.json` with your findings:

```json
{
  "symbols": [
    {
      "repo": "org/repo-name",
      "path": "relative/path/to/file.go",
      "symbol": "StructName"
    }
  ],
  "text": "Narrative explanation citing which repos and orgs implement storage.Interface and where."
}
```

## Evaluation

Your answer is evaluated on:
- **Symbol recall and precision**: Did you find all structs that explicitly implement `storage.Interface` via the `var _` pattern?
- The oracle expects implementations from at least 2 different GitHub organizations.
