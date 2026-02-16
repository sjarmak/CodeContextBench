# {task_id}: {title}

## Task

{task_prompt}

## Context

- **Repository**: {repo} ({language}, ~{loc_estimate} LOC)
- **Category**: Security Analysis
- **Difficulty**: {difficulty}
- **Subsystem Focus**: {subsystem}

## Requirements

1. Identify all entry points where untrusted data enters the subsystem
2. Trace data flow from each entry point through transformations to sensitive operations (sinks)
3. Identify all files in the attack surface
4. Document any existing mitigations and where they may be insufficient

## Expected Output

Write your analysis to `/logs/agent/solution.md` with the following structure:

```markdown
## Files Examined
- path/to/file1.ext — role in attack surface
- path/to/file2.ext — role in attack surface
...

## Entry Points
1. path/to/entry1.ext:function_name — accepts [type of untrusted input]
2. path/to/entry2.ext:function_name — accepts [type of untrusted input]
...

## Data Flow
### Flow 1: [name]
1. Source: path/to/source.ext (untrusted input enters here)
2. Transform: path/to/transform.ext (data is [processed/validated/not validated])
3. Sink: path/to/sink.ext (sensitive operation: [db query/file write/exec/etc.])

## Dependency Chain
[Ordered list of files from entry to sink]

## Analysis
[Detailed security analysis including:
- Vulnerability class (injection, auth bypass, SSRF, etc.)
- Existing mitigations and their gaps
- Attack scenarios
- Recommended remediation]

## Summary
[Concise description of the vulnerability and its impact]
```

## Evaluation Criteria

- Attack surface coverage: Did you identify all files in the vulnerable data flow?
- Entry point identification: Did you find the correct entry points?
- Data flow completeness: Did you trace the full path from source to sink?
- Analysis quality: Is the vulnerability class correctly identified?
