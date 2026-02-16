# {task_id}: {title}

## Task

{task_prompt}

## Context

- **Repository**: {repo} ({language}, ~{loc_estimate} LOC)
- **Category**: Cross-File Refactoring
- **Difficulty**: {difficulty}
- **Subsystem Focus**: {subsystem}

## Requirements

1. Identify ALL files that need modification for this refactoring
2. Document the complete dependency chain showing why each file is affected
3. Implement the changes (or describe them precisely if the scope is too large)
4. Verify that no references to the old API/name remain

## Expected Output

Write your analysis to `/logs/agent/solution.md` with the following structure:

```markdown
## Files Examined
- path/to/file1.ext — why this file needs changes
- path/to/file2.ext — why this file needs changes
...

## Dependency Chain
1. Definition: path/to/definition.ext (original definition)
2. Direct usage: path/to/user1.ext (imports/references the symbol)
3. Transitive: path/to/user2.ext (uses a type that depends on the symbol)
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
[Explanation of the refactoring strategy, affected areas, and verification approach]
```

## Evaluation Criteria

- File coverage: Did you identify ALL files that need modification?
- Completeness: Were all references updated (no stale references)?
- Compilation: Does the code still compile after changes?
- Correctness: Do the changes preserve the intended behavior?
