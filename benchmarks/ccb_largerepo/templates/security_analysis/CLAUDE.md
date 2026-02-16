# {task_id}: {title}

This repository is large (~{loc_estimate} LOC). Use targeted search to trace data flows from entry points to sensitive operations.

## Task Type: Security Analysis

Your goal is to analyze a subsystem for security vulnerabilities by tracing data flow. Focus on:

1. **Entry point identification**: Find where untrusted data enters the subsystem
2. **Data flow tracing**: Follow data through transformations to sensitive operations (sinks)
3. **Mitigation assessment**: Identify existing security controls and their gaps
4. **Vulnerability classification**: Name the specific vulnerability class (OWASP category)

## Output Format

Write your analysis to `/logs/agent/solution.md` with these required sections:

```markdown
## Files Examined
- path/to/file.ext — role in the attack surface

## Entry Points
1. path/to/entry.ext:function_name — accepts [type of untrusted input]

## Data Flow
### Flow 1: [name]
1. Source: path/to/source.ext (untrusted input enters)
2. Transform: path/to/transform.ext (data processed/validated)
3. Sink: path/to/sink.ext (sensitive operation)

## Dependency Chain
[Ordered list of files from entry to sink]

## Analysis
[Vulnerability class, existing mitigations, gaps, attack scenarios, remediation]

## Summary
[Concise vulnerability description and impact]
```

## Search Strategy

- Search for input handling functions (HTTP handlers, parsers, deserializers)
- Use `find_references` to trace how input data flows through the codebase
- Search for sensitive operations (SQL queries, file I/O, exec, crypto)
- Look for validation/sanitization functions between sources and sinks
