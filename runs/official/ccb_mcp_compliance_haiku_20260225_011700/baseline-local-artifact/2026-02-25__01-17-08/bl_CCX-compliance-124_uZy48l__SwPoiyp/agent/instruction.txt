# Firefox Content Security Policy Enforcement Audit

## Your Task

Audit the Content Security Policy (CSP) enforcement infrastructure in Firefox. Find all C++ source files in `mozilla-firefox/firefox` under `dom/security/` that implement CSP parsing, evaluation, and violation reporting. Specifically: 1. The file that defines `nsCSPParser` — the CSP directive parser. 2. The file that implements `nsCSPContext` — the main CSP context that holds policies. 3. The file that implements CSP violation reporting (`nsCSPUtils` or similar). 4. The header file that declares the `nsIContentSecurityPolicy` XPCOM interface. 5. The file under `dom/security/` that performs script-src evaluation for inline scripts. Report each file path and its primary class or function.

## Context

You are working on a codebase task involving repos from the compliance domain.

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
