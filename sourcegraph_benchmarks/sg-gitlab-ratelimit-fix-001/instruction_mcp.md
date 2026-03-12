> **Note:** You have access to Sourcegraph MCP tools for code search and navigation.
> Use `sg_keyword_search` and `sg_nls_search` to explore the codebase efficiently.

# Fix GitLab allowGroups Membership Check Rate Limiting

**Repository:** sourcegraph/sourcegraph
**Language:** Go

## Problem

When `allowGroups` is configured for GitLab OAuth, the membership check iterates through all user groups via pagination (`ListGroups`). For users who are members of hundreds of subgroups, this triggers GitLab API rate limiting, causing authentication failures.

## Task Contract

- `TASK_WORKDIR=/workspace`
- `TASK_REPO_ROOT=/workspace`

## Task

1. Update the calling path to use the new flow.
2. Update existing tests to reflect the new behavior

## Success Criteria

- The `allowGroups` check uses targeted API calls instead of paginating all groups
- Supporting client functionality exists for the new membership-check flow.
- Tests pass and cover the new membership check logic
- No regressions in the GitLab OAuth flow
