# File Dependency Ordering Task

**Repository:** predicates
**Language:** typescript
**Difficulty:** MEDIUM
**Task Type:** Dependency Recognition (File Ordering)

## Description

You are given source code from the **predicates** repository. Your task is to determine the correct dependency ordering of the files listed below. Files that are depended upon (callees) should come before files that depend on them (callers).

## Files to Order

The following files need to be arranged in dependency order (dependencies first):

- `predicates/src/typeToPredicate.ts`
- `predicates/src/any.ts`
- `predicates/test/anyTest.ts`
- `predicates/src/weakSet.ts`
- `predicates/src/utils/assertPredicates.ts`
- `predicates/src/arrayOf.ts`

## Source Code

The source code is available in `/workspace/code_content.txt`. Read it carefully to understand the import/dependency relationships between files.

## Task

1. Read the source code from `/workspace/code_content.txt`
2. Analyze the import statements and dependency relationships between files
3. Determine the correct ordering where each file appears after all files it depends on
4. Write the ordered list to `/workspace/submission.json`

## Output Format

Write your answer to `/workspace/submission.json` as a JSON array of file paths in dependency order (dependencies first, dependents last):

```json
[
  "'repo_name/path/to/base_file.ts'",
  "'repo_name/path/to/dependent_file.ts'"
]
```

**Important:** Use the exact file path strings as listed above, including the surrounding single quotes.

## Evaluation

Your submission is scored by element-wise exact match averaged across positions. Each position where your file matches the correct ordering scores 1/N, where N is the total number of files.

**Time Limit:** 10 minutes
