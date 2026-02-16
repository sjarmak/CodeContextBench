# {task_id}: {title}

This repository is large (~{loc_estimate} LOC). Use comprehensive search to understand existing patterns before implementing.

## Task Type: Feature Implementation

Your goal is to implement a new feature that touches multiple subsystems. Focus on:

1. **Pattern discovery**: Find existing similar features to understand conventions
2. **File identification**: Identify ALL files that need modification
3. **Implementation**: Write code that follows existing patterns and conventions
4. **Verification**: Ensure the implementation compiles and doesn't break existing tests

## Output Format

Write your analysis to `/logs/agent/solution.md` with these required sections:

```markdown
## Files Examined
- path/to/file.ext — examined to understand [pattern/API/convention]

## Dependency Chain
1. Define types/interfaces: path/to/types.ext
2. Implement core logic: path/to/impl.ext
3. Wire up integration: path/to/integration.ext
4. Add tests: path/to/tests.ext

## Code Changes
### path/to/file1.ext
\`\`\`diff
- old code
+ new code
\`\`\`

## Analysis
[Implementation strategy, design decisions, integration approach]
```

## Search Strategy

- Search for similar features or patterns to follow as examples
- Use `find_references` to understand how existing features are wired together
- Use `go_to_definition` to understand types and interfaces you need to implement
- Search for test patterns to write tests that match the existing style
