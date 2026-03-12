> **Note:** You have access to Sourcegraph MCP tools for code search and navigation.
> Use `sg_keyword_search` and `sg_nls_search` to explore the codebase efficiently.

# Prevent Image Decompression Bomb DoS in Deep Search

**Repository:** sourcegraph/sourcegraph
**Language:** Go

## Problem

The Deep Search image processing pipeline calls `image.Decode` without first checking the image dimensions. A crafted PNG can compress to a small file size but decompress to hundreds of megabytes of pixel data, causing out-of-memory crashes (decompression bomb attack).

## Task Contract

- `TASK_WORKDIR=/workspace`
- `TASK_REPO_ROOT=/workspace`

## Task

1. Enforce a reasonable upper bound on decoded image size.
2. Return an appropriate error for oversized images
3. Add tests verifying that oversized images are rejected and normal images still process correctly

## Success Criteria

- Oversized images are rejected before full decode.
- Normal-sized images continue to process correctly

- Tests cover both the rejection case and the happy path
