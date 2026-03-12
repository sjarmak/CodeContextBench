> **Note:** You have access to Sourcegraph MCP tools for code search and navigation.
> Use `sg_keyword_search` and `sg_nls_search` to explore the codebase efficiently.

# Security Compliance Audit: Authentication and Authorization Chain

## Your Task

Map the complete authentication and authorization middleware chain in Sourcegraph's frontend service. Identify all authentication provider middlewares, how they register and create sessions, and how the authorization layer enforces repository-level access permissions across all supported code hosts.

## Context

You are auditing Sourcegraph's authentication architecture for a compliance review. The codebase is a Go monorepo with 12+ authentication providers and 8 code host authorization providers.

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
  "summary": "Brief explanation of the auth chain architecture"
}
```

Include ALL files that define, register, or enforce authentication and authorization. Both middleware registration files and provider implementations are required.
