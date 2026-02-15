# {task_id}: {title}

## Task

{task_prompt}

## Context

- **Repository**: {repo} ({language}, ~{loc_estimate} LOC)
- **Category**: Feature Implementation
- **Difficulty**: {difficulty}
- **Subsystem Focus**: {subsystem}

## Requirements

1. Identify all files that need modification to implement this feature
2. Follow existing patterns and conventions in the codebase
3. Implement the feature with actual code changes
4. Ensure the implementation compiles and doesn't break existing functionality

## Expected Output

Write your analysis to `/logs/agent/solution.md` with the following structure:

```markdown
## Files Examined
- path/to/file1.ext — examined to understand [pattern/API/convention]
- path/to/file2.ext — modified to add [feature component]
...

## Dependency Chain
1. Define types/interfaces: path/to/types.ext
2. Implement core logic: path/to/impl.ext
3. Wire up integration: path/to/integration.ext
4. Add tests: path/to/tests.ext
...

## Code Changes
### path/to/file1.ext
```diff
- old code
+ new code
```

### path/to/file2.ext
```diff
- old code
+ new code
```

## Analysis
[Explanation of implementation strategy, design decisions, and how the feature
integrates with existing architecture]
```

## Evaluation Criteria

- Compilation: Does the code compile after changes?
- File coverage: Did you modify all necessary files?
- Pattern adherence: Do changes follow existing codebase conventions?
- Feature completeness: Is the feature fully implemented?
