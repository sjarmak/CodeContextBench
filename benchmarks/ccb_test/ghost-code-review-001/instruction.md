# Code Review: Ghost Comment Likes Feature

- **Repository**: TryGhost/Ghost
- **Difficulty**: hard
- **Category**: code-review
- **Task Type**: repo-clone

## Description

You are reviewing a recently merged pull request that adds a "comment likes" feature to the Ghost blogging platform. The PR introduces a new API endpoint for browsing comment likes, along with supporting controller and service methods. However, several defects were introduced during the merge — both functional bugs and compliance violations.

Your task is to **find the defects, fix them in the code, and produce a structured review report**.

## Context

The comment likes feature spans three backend files:

1. **`ghost/core/core/server/services/comments/comments-service.js`** — Service layer: `getCommentLikes()` method that queries the database for likes on a given comment.
2. **`ghost/core/core/server/services/comments/comments-controller.js`** — Controller layer: `getCommentLikes()` method that extracts the comment ID from the request frame and delegates to the service.
3. **`ghost/core/core/server/api/endpoints/comment-likes.js`** — API endpoint definition: `browse` action configuration including HTTP headers and query options.

## Task

YOU MUST IMPLEMENT CODE CHANGES to complete this task.

Review the three files listed above for the following types of defects:

- **Functional bugs**: Logic errors that cause incorrect behavior (e.g., missing error handling, wrong variable references, broken data loading).
- **Compliance violations**: Deviations from Ghost's API conventions (e.g., incorrect cache control headers on read-only endpoints).

For each defect you find:

1. **Fix the code** by editing the affected file in `/workspace/`.
2. **Record the defect** in your review report.

### Expected Output

After completing your review, write a JSON file at `/workspace/review.json` containing an array of defect objects:

```json
[
  {
    "file": "ghost/core/core/server/services/comments/comments-service.js",
    "line": 263,
    "severity": "critical",
    "description": "Brief description of what is wrong and why",
    "fix_applied": true
  }
]
```

Each entry must include:
- `file` — Relative path from repository root
- `line` — Approximate line number where the defect occurs
- `severity` — One of: `critical`, `high`, `medium`, `low`
- `description` — What the defect is and what impact it has
- `fix_applied` — Boolean indicating whether you committed a fix

## Evaluation

Your review will be evaluated on detection accuracy and fix quality.

## Testing

- **Time limit**: 1200 seconds
- Run `bash /workspace/tests/test.sh` to verify your changes
