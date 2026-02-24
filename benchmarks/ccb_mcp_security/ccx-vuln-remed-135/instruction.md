# Chromium Renderer Process Sandbox Audit

## Your Task

Audit the security sandbox implementation for Chromium's renderer processes. Find all C++ source files in `chromium/chromium` that implement the sandbox: 1. The file under `sandbox/linux/seccomp-bpf-helpers/` that implements `BaselinePolicy` — the seccomp-BPF baseline policy for Linux sandboxing. 2. The file under `sandbox/win/src/` that implements `PolicyBase` — the Windows sandbox policy configuration (concrete implementation of `TargetPolicy`). 3. The file under `sandbox/policy/linux/` that implements `RendererProcessPolicy` — the BPF policy specific to renderer process sandboxing (look for `EvaluateSyscall`). 4. The file under `sandbox/policy/` that declares sandbox type utilities and the `SandboxType` enum mapping. Report each file path and key class/function.

## Context

You are working on a codebase task involving repos from the security domain.

## Available Resources

No local repositories are pre-checked out.

**Note:** Additional repositories are accessible via Sourcegraph MCP tools:
- `sg-evals/chromium--2d05e315` (chromium/chromium)

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
