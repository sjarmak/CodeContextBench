# Cross-Compiler Sanitizer Tracing: ASan in LLVM vs GCC

## Your Task

AddressSanitizer (ASan) is implemented in both LLVM and GCC. Find the key source files that implement ASan instrumentation in each compiler. In `llvm/llvm-project`: 1. The C++ source file under `compiler-rt/lib/asan/` that implements ASan interceptors for standard library functions. 2. The C++ source file under `compiler-rt/lib/asan/` that implements the ASan runtime initialization. 3. The LLVM pass that inserts ASan instrumentation at the IR level (look for `AddressSanitizer` in `llvm/lib/Transforms/Instrumentation/`). In `gcc-mirror/gcc`: 4. The C++ source file that implements ASan instrumentation in GCC (`gcc/asan.cc`). 5. The header file for ASan in GCC (`gcc/asan.h`). Report the repo, file path, and primary class or function name for each file.

## Context

You are working on a codebase task involving repos from the crossrepo tracing domain.

## Available Resources

The local `/workspace/` directory contains: sg-evals/llvm-project--a8f3c97d, sg-evals/gcc--96dfb333.


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
