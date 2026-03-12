> **Note:** You have access to Sourcegraph MCP tools for code search and navigation.
> Use `sg_keyword_search` and `sg_nls_search` to explore the codebase efficiently.

# Fix @-Anchor Detection in Deep Search Prompt Editor

**Repository:** sourcegraph/sourcegraph
**Language:** TypeScript

## Problem

The @-mention suggestion trigger in the Deep Search prompt editor incorrectly detects the anchor position for the `@` character. The current implementation reconstructs the position from a flattened string representation of the editor content, which produces wrong offsets when line breaks (multiple paragraphs/nodes) are present. This causes suggestions to be inserted at incorrect positions.

## Task Contract

- `TASK_WORKDIR=/workspace`
- `TASK_REPO_ROOT=/workspace`

## Task

1. Ensure the anchor position is correct when the editor contains multiple paragraphs/nodes with line breaks
2. Add a test file (the relevant module) with test cases covering:
 - Single-line @-mention detection
 - Multi-line/multi-paragraph @-mention detection
 - Edge cases (@ at start of line, @ after whitespace)

## Success Criteria

- @-mention suggestions are inserted at the correct position regardless of line breaks
- The anchor position is derived from ProseMirror state, not a flattened string
- Tests cover single-line and multi-line scenarios
