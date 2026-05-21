# Prometheus Metrics Exposition Pattern Across Kubernetes and Grafana

## Your Task

Find the Go source files in both kubernetes/kubernetes and grafana/grafana that implement the Prometheus metrics exposition pattern: where metrics are registered using the Prometheus client_golang library, how metric collectors are organized, and where the `/metrics` HTTP endpoint is configured to expose them. Compare how both projects structure their metrics infrastructure.

## Context

You are working on a codebase task involving repos from the crossorg domain. Both Kubernetes and Grafana use the Prometheus client_golang library to expose internal metrics, but they organize their metrics registration and exposition differently. Your goal is to map these patterns across both codebases.

## Available Resources

The local `/workspace/` directory contains: sg-evals/kubernetes--v1.32.0, sg-evals/grafana--v11.4.0.


## Output Format

Create a file at `/workspace/answer.json` with your findings in the following structure:

```json
{
  "files": [
    {"repo": "org/repo-name", "path": "relative/path/to/file.go"}
  ],
  "symbols": [
    {"repo": "org/repo-name", "path": "relative/path/to/file.go", "symbol": "SymbolName"}
  ],
  "chain": [],
  "text": "Narrative explanation of your findings, citing repos and file paths."
}
```

Include only the fields relevant to this task. Your answer is evaluated against a closed-world oracle — completeness matters.

## Evaluation

Your answer will be scored on:
- **File recall and precision**: Did you find all relevant files?
- **Symbol identification**: Correct symbol names and locations?
- **Keyword presence**: Did you mention key concepts (metrics registry, collectors, exposition)?
