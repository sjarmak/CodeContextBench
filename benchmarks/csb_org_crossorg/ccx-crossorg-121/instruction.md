# Cross-Org WebIDL to DOM Binding Discovery

## Your Task

Find all WebIDL interface files in `mozilla-firefox/firefox` under `dom/webidl/` that define DOM interfaces for the Fetch API (Request, Response, Headers, FetchEvent). Then find the corresponding C++ binding implementation files under `dom/fetch/` that implement these WebIDL interfaces. Report the WebIDL file, the C++ header, and the C++ implementation file for each Fetch API type.

## Context

You are working on a codebase task involving repos from the crossorg domain.

## Available Resources

The local `/workspace/` directory contains: sg-evals/firefox--871325b8.


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
