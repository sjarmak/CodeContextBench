# Investigation Benchmark Suite

This suite tests your ability to investigate code-level phenomena in large codebases.

## Search Strategy

**This repository is large.** You MUST use Sourcegraph MCP tools for investigation:

- Use `keyword_search` to find all references to specific symbols, configs, or patterns
- Use `find_references` to trace symbol usage across the codebase
- Use `go_to_definition` to understand type hierarchies and function contracts
- Use `commit_search` to find recent changes that may have caused regressions
- Use `diff_search` to find what code was added/removed in recent changes
- Use `deepsearch` for high-level "how does X work?" questions

## Output Requirements

Write your investigation report to `/logs/agent/investigation.md`.

Your report MUST include:
1. **Summary** - 1-2 sentence finding
2. **Root Cause** - Specific file, function, and mechanism
3. **Evidence** - Code references with file paths and line numbers
4. **Affected Components** - List of packages/modules impacted
5. **Recommendation** - Fix strategy or migration path

Do NOT write code fixes. Your job is investigation and analysis only.
