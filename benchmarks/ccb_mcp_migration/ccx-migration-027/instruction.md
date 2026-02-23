# Deprecated API Detection: Express req.host

## Your Task

Your team is auditing the Express.js ecosystem for deprecated API usage before a major
version bump. The `req.host` property was deprecated in Express 4.3.0 in favor of
`req.hostname`. You need to find all source files in the Express repository that define
or test the deprecated `req.host` property (not `req.hostname`).

**Specific question**: Which source files in `sg-evals/expressjs-express` reference
the deprecated `req.host` property specifically (the definition, tests, and changelog)?

**IMPORTANT precision trap**: `req.host` is a substring of `req.hostname` — you must
verify each hit actually uses `req.host` as a standalone deprecated property, not just
as part of the non-deprecated `req.hostname`.

## Context

Express 4.3.0 introduced `req.hostname` as the correct replacement for `req.host`.
The old `req.host` property was deprecated with a deprecation notice. Your audit must
distinguish between:
- Files that reference the **deprecated** `req.host` property (definition, tests, changelog)
- Files that merely use the **current** `req.hostname` property (not deprecated)

This is a common substring-matching pitfall in migration audits.

## Available Resources

Your ecosystem includes the following repositories:
- `expressjs/express` at 4.21.1
- `nodejs/node` at v22.13.0
- `lodash/lodash` (optional, not needed for this task)
- `prisma/prisma` (optional, not needed for this task)

## Output Format

Create a file at `/workspace/answer.json` with your findings:

```json
{
  "files": [
    {"repo": "sg-evals/expressjs-express", "path": "relative/path/to/file.js"}
  ],
  "text": "Narrative explanation of your findings, citing repos and file paths."
}
```

**Important**: Use repo name `sg-evals/expressjs-express` or `expressjs/express`.
**Note**: Sourcegraph MCP tools return repo names with a `github.com/` prefix. Strip this prefix in your answer.

Include only files that specifically reference the deprecated `req.host` property. Your answer is evaluated against a closed-world oracle — both completeness and precision matter.

## Evaluation

Your answer will be scored on:
- **File recall and precision**: Did you find all files that reference the deprecated `req.host`? Did you avoid false positives from `req.hostname` matches?
- **Keyword presence**: Does your narrative mention key terms like `req.host`, `req.hostname`, and `deprecated`?
