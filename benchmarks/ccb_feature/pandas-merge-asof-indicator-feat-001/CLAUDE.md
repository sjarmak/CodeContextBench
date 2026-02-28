# pandas-merge-asof-indicator-feat-001: merge_asof indicator

## Task Type: Feature Implementation (API Extension)

Add indicator support to merge_asof following existing merge patterns.

## Key Reference Files
- `pandas/core/reshape/merge.py` — merge_asof, _AsOfMerge, _MergeOperation
- `pandas/tests/reshape/merge/test_merge_asof.py` — existing tests

## Search Strategy
- Search for `def merge_asof` to find function signature
- Search for `class _AsOfMerge` to find class definition
- Search for `indicator` in merge.py to see how pd.merge handles it
