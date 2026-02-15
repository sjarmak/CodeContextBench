# Transitive Dependency Ordering: evaluation.go

**Repository:** flipt-io/flipt
**Access Scope:** You may read any file. Write your results to `/workspace/submission.json`.

## Context

Flipt is a feature flag platform built with Go. The evaluation server at `internal/server/evaluation/evaluation.go` is a critical component that depends on several internal packages. Understanding the full transitive dependency graph is essential for planning refactors, estimating blast radius, and ordering build steps.

## Task

Identify all internal packages that `internal/server/evaluation/evaluation.go` transitively depends on, and list them in topological dependency order (leaf packages first, the target package last).

**YOU MUST CREATE A submission.json FILE.**

### Requirements

1. **Start at the target file** — Read `internal/server/evaluation/evaluation.go` and identify all import paths that start with the module prefix (`go.flipt.io/flipt/`)
2. **Trace transitively** — For each internal import, read that package's source files and find its own internal imports. Continue recursively until you reach packages with no internal imports (leaf nodes)
3. **Build the dependency graph** — Track which packages depend on which other packages
4. **Topologically sort** — Order the packages so that every package appears after all packages it depends on. Leaf packages (no internal dependencies) come first, the root package (`internal/server/evaluation`) comes last
5. **Write submission** — Create `/workspace/submission.json` containing a JSON array of package paths in topological order

### Internal Packages

"Internal" means packages within the flipt module — import paths starting with `go.flipt.io/flipt/`. Strip the module prefix and version to get relative paths. For example:
- `go.flipt.io/flipt/v2/internal/storage` → `internal/storage`
- `go.flipt.io/flipt/rpc/flipt` → `rpc/flipt`
- `go.flipt.io/flipt/errors` → `errors`

Exclude all external dependencies (standard library, `google.golang.org/`, `go.uber.org/`, etc.).

### Output Format

Create `/workspace/submission.json` with a JSON array of package paths in dependency order:
```json
[
  "leaf/package/a",
  "leaf/package/b",
  "mid/level/package",
  "internal/server/evaluation"
]
```

### Hints

- The target file imports approximately 6 internal packages directly
- The total transitive closure is approximately 9 packages (including the target itself)
- Use `go_to_definition` to quickly navigate from import paths to their source files
- Leaf packages typically only import standard library or external packages
- When multiple valid topological orderings exist, any correct ordering is accepted
- Some internal packages like `errors` and `internal/containers` are common leaf nodes
- Check ALL `.go` files in each package directory — imports may be split across multiple files

## Success Criteria

- `/workspace/submission.json` exists and is valid JSON
- The file contains a JSON array of package path strings
- All transitively-imported internal packages are included
- The ordering is topologically valid (dependencies before dependents)
- Scoring: 0.6 * position_exact_match + 0.4 * Kendall_tau_rank_correlation
