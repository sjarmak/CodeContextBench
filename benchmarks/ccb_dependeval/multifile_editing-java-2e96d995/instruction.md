# Multi-File Code Editing Task

**Repository:** kafka-webview
**Language:** java
**Difficulty:** MEDIUM
**Task Type:** Multi-file Editing

## Description

You are given source code from the **kafka-webview** repository. Your task is to implement a feature modification that requires changes across multiple files.

## Feature to Implement

To implement this feature, we need to add a new field 'confirmPassword' to the ResetPasswordForm class. This field will be validated to ensure it matches the 'password' field. Additionally, the invoking code segment will need to be updated to handle the new field and validate it accordingly.

## Source Code

The source code is available in `/workspace/code_content.txt`. Read it carefully to understand the current implementation before making changes.

## Task

1. Read the source code from `/workspace/code_content.txt`
2. Understand the current code structure and the feature request above
3. Implement the required changes across the relevant files
4. Write your modified files to `/workspace/submission.json`

## Output Format

Write your answer to `/workspace/submission.json` as a JSON object mapping file paths to their complete modified source code:

```json
{
  "path/to/file1.java": "complete modified source code for file1...",
  "path/to/file2.java": "complete modified source code for file2..."
}
```

**Important:**
- Include the **complete** modified source code for each file, not just the changes
- Use relative file paths (without the repository name prefix)
- Include all 2 files that need modifications

## Evaluation

Your submission is scored by average string similarity (per-file) between your modified code and the expected modifications. Higher similarity to the expected output yields a higher score.

**Time Limit:** 10 minutes
