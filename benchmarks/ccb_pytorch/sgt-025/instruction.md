# Continue to build nightly CUDA 12.9 for internal

**Repository:** pytorch  
**Difficulty:** HARD  
**Category:** cross_module_bug_fix



## Description

This task partially reverts PR #161916 (which removed CUDA 12.9 builds in favor of CUDA 13.0) to restore nightly CUDA 12.9 builds for internal PyTorch consumers who still depend on that CUDA version. Removing CUDA 12.9 prematurely would break internal CI pipelines and prevent teams from testing against that CUDA toolkit version during the transition period to CUDA 13.0.

The fix re-adds the CUDA 12.9 entries to the binary build matrix in `.github/scripts/generate_binary_build_matrix.py` and regenerates the GitHub Actions workflow files for Linux manywheel, Linux aarch64, Linux libtorch, and Windows wheel/libtorch nightly builds. The large line count is because the generated workflow YAML files contain full build/test job definitions for each CUDA version.

## Task

Changes:
- 9 files modified (generate_binary_build_matrix.py + generated workflow YAMLs)
- 3525 additions, 501 deletions

Tasks:
1. Re-add CUDA 12.9 entries to `.github/scripts/generate_binary_build_matrix.py`
2. Regenerate affected workflow files (Linux manywheel, aarch64, libtorch, Windows)
3. Verify CUDA 12.9 appears in nightly build matrix
4. Verify: run "make test" successfully

## Success Criteria

All tests pass: run "make test" successfully.
Code follows repository conventions.
No regressions in existing functionality.
All 9 modified files updated correctly.

## Testing

Run the test command to verify your implementation:

```bash
make test
```

**Time Limit:** 10 minutes  
**Estimated Context:** 8000 tokens
