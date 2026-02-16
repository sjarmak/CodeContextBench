# {task_id}: {title}

## Task

{task_prompt}

## Context

- **Repository**: {repo} ({language}, ~{loc_estimate} LOC)
- **Category**: Architectural Understanding
- **Difficulty**: {difficulty}
- **Subsystem Focus**: {subsystem}

## Requirements

1. Identify all files involved in the subsystem described above
2. Trace the dependency chain from entry point through all layers
3. Document the architectural patterns used (e.g., MVC, layered, pipeline, observer)
4. Explain how components interact and data flows between them

## Expected Output

Write your analysis to `/logs/agent/solution.md` with the following structure:

```markdown
## Files Examined
- path/to/file1.ext — role in architecture
- path/to/file2.ext — role in architecture
...

## Dependency Chain
1. Entry point: path/to/entry.ext
2. Calls: path/to/next.ext (via function/method name)
3. Delegates to: path/to/impl.ext
...

## Analysis
[Detailed architectural analysis including:
- Design patterns identified
- Component responsibilities
- Data flow description
- Interface contracts between components]

## Summary
[Concise 2-3 sentence summary answering the task question]
```

## Evaluation Criteria

- File recall: Did you find the correct set of architecturally relevant files?
- Dependency accuracy: Did you trace the correct dependency/call chain?
- Architectural coherence: Did you correctly identify the design patterns and component relationships?
