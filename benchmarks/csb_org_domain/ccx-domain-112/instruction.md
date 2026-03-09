# Firefox Servo CSS Style System Integration

## Your Task

Trace how Firefox's Servo-based CSS style system resolves and applies styles to DOM elements. Find all C++ source files in `mozilla-firefox/firefox` under `layout/style/` that form the core style resolution pipeline: 1. The header and source files for `ServoStyleSet` — the main entry point for style resolution. 2. The header for `ServoBindings` — the Gecko-to-Servo FFI declarations. 3. The header for `RestyleManager` — the component that schedules and manages style recalculation. 4. The header for `ServoUtils` — utility functions for Servo traversal state. 5. The `moz.build` file for `layout/style/` that lists all the style system source files. Report the repo, file path, and key class or FFI function name for each file.

## Context

You are working on a codebase task involving repos from the domain domain.

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
