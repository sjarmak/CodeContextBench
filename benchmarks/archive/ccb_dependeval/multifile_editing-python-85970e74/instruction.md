# Multi-File Code Editing Task

**Repository:** Magisk_Manager_Recovery_Tool
**Language:** python
**Difficulty:** MEDIUM
**Task Type:** Multi-file Editing

## Description

You are given source code from the **Magisk_Manager_Recovery_Tool** repository. Your task is to implement a feature modification that requires changes across multiple files.

## Feature to Implement

The new feature involves fetching and displaying app icons alongside app names in the MagiskSU apps list. This is implemented by adding a new function `get_app_icon` in a new file (#file 3) which retrieves the icon for a given package name. The existing function `_get_saved_package_name_uid` in #file 1 is modified to include the icon retrieval logic. The invoking code in #file 2 is updated to use the new functionality for displaying icons.

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
  "path/to/file1.py": "complete modified source code for file1...",
  "path/to/file2.py": "complete modified source code for file2..."
}
```

**Important:**
- Include the **complete** modified source code for each file, not just the changes
- Use relative file paths (without the repository name prefix)
- Include all 2 files that need modifications

## Evaluation

Your submission is scored by average string similarity (per-file) between your modified code and the expected modifications. Higher similarity to the expected output yields a higher score.

**Time Limit:** 10 minutes
