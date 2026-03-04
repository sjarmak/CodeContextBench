# Cross-Org WebIDL to DOM Binding Discovery

## Your Task

Find all WebIDL interface files in `mozilla-firefox/firefox` under `dom/webidl/` that define DOM interfaces for the Fetch API (Request, Response, Headers, FetchEvent). Then find the corresponding C++ binding implementation files under `dom/fetch/` that implement these WebIDL interfaces. Report the WebIDL file, the C++ header, and the C++ implementation file for each Fetch API type.

## Context

You are working on a codebase task involving repos from the crossorg domain.

## Available Resources

No local repositories are pre-checked out.

**Note:** Additional repositories may be relevant to this task:
- `sg-evals/firefox--871325b8` (mozilla-firefox/firefox)

## Output Format

Create a file at `/workspace/answer.json` with your findings in the following structure:

```json
{
  "files": [
    {"repo": "org/repo-name", "path": "relative/path/to/file.cpp"}
  ],
  "symbols": [
    {"repo": "org/repo-name", "path": "relative/path/to/file.cpp", "symbol": "SymbolName"}
  ],
  "chain": [
    {"repo": "org/repo-name", "path": "relative/path/to/file.cpp", "symbol": "FunctionName"}
  ],
  "text": "Narrative explanation of your findings, citing repos and file paths."
}
```

Include only the fields relevant to this task. Your answer is evaluated against a closed-world oracle — completeness matters.

## Evaluation

Your answer will be scored on:
- **File recall and precision**: Did you find all relevant files?
