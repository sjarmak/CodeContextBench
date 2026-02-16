# {task_id}: {title}

This repository is large (~{loc_estimate} LOC). Use comprehensive search to find ALL references before making changes.

## Task Type: Cross-File Refactoring

Your goal is to perform a refactoring that touches multiple files across the codebase. Focus on:

1. **Complete identification**: Find ALL files that reference the symbol/pattern being refactored
2. **Dependency ordering**: Understand which files depend on which, and change them in the right order
3. **Consistency**: Ensure no stale references remain after the refactoring
4. **Compilation**: Verify the code still compiles after changes

## Output Format

Write your analysis to `/logs/agent/solution.md` with these required sections:

```markdown
## Files Examined
- path/to/file.ext — why this file needs changes

## Dependency Chain
1. path/to/definition.ext (original definition)
2. path/to/user1.ext (direct reference)
3. path/to/user2.ext (transitive dependency)

## Code Changes
### path/to/file1.ext
\`\`\`diff
- old code
+ new code
\`\`\`

## Analysis
[Refactoring strategy and verification approach]
```

## Search Strategy

- Use `find_references` on the symbol being refactored to find ALL usages
- Use `keyword_search` to catch string references (comments, configs, docs)
- Check import/include statements for transitive dependencies
- After changes, search again to verify no stale references remain
