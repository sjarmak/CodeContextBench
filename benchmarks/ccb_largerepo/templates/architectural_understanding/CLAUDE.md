# {task_id}: {title}

This repository is large (~{loc_estimate} LOC). Use comprehensive search strategies for broad architectural queries rather than narrow, single-directory scopes.

## Task Type: Architectural Understanding

Your goal is to analyze and explain the architecture of a specific subsystem. Focus on:

1. **Component identification**: Find all major components/modules in the subsystem
2. **Dependency mapping**: Trace how components depend on each other
3. **Design pattern recognition**: Identify architectural patterns (factory, observer, strategy, etc.)
4. **Interface boundaries**: Find the public APIs and internal implementation boundaries

## Output Format

Write your analysis to `/logs/agent/solution.md` with these required sections:

```markdown
## Files Examined
- path/to/file.ext — role in the architecture

## Dependency Chain
1. path/to/core.ext (foundational types/interfaces)
2. path/to/impl.ext (implementation layer)
3. path/to/integration.ext (integration/wiring layer)

## Analysis
[Your architectural analysis]
```

## Search Strategy

- Start with high-level entry points (main files, public APIs, package-level docs)
- Use `find_references` to trace how components connect
- Use `go_to_definition` to understand interface implementations
- Search for design pattern keywords relevant to the subsystem
