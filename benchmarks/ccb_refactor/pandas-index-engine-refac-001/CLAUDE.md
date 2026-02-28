# pandas-index-engine-refac-001: Rename _engine property

## Task Type: Cross-File Refactoring (Rename)

Rename _engine → _index_engine across pandas Index hierarchy.

## Key Reference Files
- `pandas/core/indexes/base.py` — base definition
- `pandas/core/indexes/range.py` — RangeIndex
- `pandas/core/indexes/multi.py` — MultiIndex

## Search Strategy
- Search for `_engine` in `pandas/core/indexes/` for all references
- Search for `def _engine` for property definitions
