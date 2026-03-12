> **Note:** You have access to Sourcegraph MCP tools for code search and navigation.
> Use `sg_keyword_search` and `sg_nls_search` to explore the codebase efficiently.

# Cross-Service Trace: LLM Completions Request Lifecycle

## Your Task

A customer reports intermittent 429 errors when using Cody completions. Trace the complete request path from the GraphQL completions API on the frontend, through the Cody Gateway proxy service, to the downstream LLM provider. Identify every rate limiting layer, authentication check, and provider selection decision point along the way.

## Context

Sourcegraph's LLM completions system spans multiple internal services: the frontend GraphQL API, a completions client abstraction with 8 provider backends, and the Cody Gateway proxy service with its own auth, rate limiting, and HTTP API layer.

## Available Resources

No local repositories are pre-checked out.

## Task Contract

- `TASK_WORKDIR=/workspace`
- `TASK_REPO_ROOT=/workspace`
- `TASK_OUTPUT=/workspace/answer.json`

## Output Format

Create a file at `/workspace/answer.json` (`TASK_OUTPUT`) with your findings in the following structure:

```json
{
  "files": [
    {
      "repo": "sourcegraph/sourcegraph",
      "path": "relative/path/to/file.go"
    }
  ],
  "symbols": [
    {
      "repo": "sourcegraph/sourcegraph",
      "path": "relative/path/to/file.go",
      "symbol": "SymbolName"
    }
  ],
  "chain": [
    {
      "repo": "sourcegraph/sourcegraph",
      "path": "relative/path/to/file.go",
      "symbol": "FunctionName"
    }
  ],
  "summary": "Brief explanation of the completions request lifecycle and rate limiting layers"
}
```

Include ALL files in the request path from GraphQL entry point to downstream provider call. Include every rate limiting and authentication checkpoint.
