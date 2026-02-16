# {task_id}: {title}

## Task

{task_prompt}

## Context

- **Repository**: {repo} ({language}, ~{loc_estimate} LOC)
- **Category**: Bug Investigation
- **Difficulty**: {difficulty}
- **Entry Point**: {entry_point}

## Symptom

{symptom_description}

## Requirements

1. Starting from the entry point, trace the execution path to the root cause
2. Identify the specific file(s) and line(s) where the bug originates
3. Explain WHY the bug occurs (not just WHERE)
4. Propose a fix with specific code changes

## Expected Output

Write your analysis to `/logs/agent/solution.md` with the following structure:

```markdown
## Files Examined
- path/to/file1.ext — examined for [reason]
- path/to/file2.ext — examined for [reason]
...

## Dependency Chain
1. Symptom observed in: path/to/symptom.ext
2. Called from: path/to/caller.ext (function name)
3. Bug triggered by: path/to/buggy.ext (function name, line ~N)
...

## Root Cause
- **File**: path/to/root_cause.ext
- **Function**: function_name()
- **Line**: ~N
- **Explanation**: [Why this code is buggy]

## Proposed Fix
```diff
- buggy code
+ fixed code
```

## Analysis
[Detailed trace from symptom to root cause, explaining each step]
```

## Evaluation Criteria

- Root cause identification: Did you find the correct file(s) where the bug originates?
- Call chain accuracy: Did you trace the correct path from symptom to root cause?
- Fix quality: Is the proposed fix correct and minimal?
