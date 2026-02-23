# CVE Remediation: Vulnerable `cookie` Package Dependency

## Your Task

Your security team has raised an alert about **CVE-2024-47764**, which affects the
`cookie` npm package in versions prior to `0.7.0`. An attacker can exploit this
vulnerability to send a crafted HTTP request that bypasses cookie security controls.

You need to identify all `package.json` files across your Node.js web stack repos
that declare **`cookie` as a direct runtime dependency** (listed under
`"dependencies"`, not `"devDependencies"`).

For each match, report:
- The repository (e.g., `sg-evals/expressjs-express`)
- The file path within the repository
- The version constraint declared for `cookie`

## Context

You are doing a security audit of your Node.js web stack, which spans multiple repos
across different organizations. The stack includes the runtime, the web framework, a
utility library, and a database ORM.

This is a cross-org audit: you need to check all repos in the stack to ensure no
vulnerable dependency slips through.

## Available Resources

Your ecosystem includes the following repositories:
- `nodejs/node` at v22.13.0
- `expressjs/express` at 4.21.1

## Output Format

Create a file at `/workspace/answer.json` with your findings:

```json
{
  "files": [
    {
      "repo": "sg-evals/expressjs-express",
      "path": "relative/path/to/package.json",
      "version": "the-version-constraint"
    }
  ],
  "text": "Narrative explanation citing the repos and version constraints found."
}
```

**Important**: Use exact repo identifiers as they appear in Sourcegraph. The repos to search are `nodejs/node`, `sg-evals/expressjs-express`, `sg-evals/lodash`, and `sg-evals/prisma-prisma`. Note: the `expressjs/express` repository corresponds to `sg-evals/expressjs-express` in Sourcegraph — use `sg-evals/expressjs-express` as the `repo` value in your answer.
**Note**: Sourcegraph MCP tools return repo names with a `github.com/` prefix (e.g., `github.com/sg-evals/kubernetes-client-go`). Strip this prefix in your answer — use `sg-evals/kubernetes-client-go`, NOT `github.com/sg-evals/kubernetes-client-go`.

Include only entries where `cookie` appears under `"dependencies"` (not `"devDependencies"`
or `"scripts"`). Your answer is evaluated against a closed-world oracle — completeness matters.

## Evaluation

Your answer will be scored on:
- **File recall and precision**: Did you find all package.json files that declare `cookie` as a runtime dependency?
- **Keyword presence**: Does your answer include the exact version constraint found?
