# Onboarding Audit: scipy.stats API Call Sites in pandas

## Your Task

You are a new engineer joining the pandas-dev team. As part of onboarding, you've been asked
to audit which pandas source files have runtime dependencies on `scipy.stats`. These call sites
are important to document because they determine where pandas degrades gracefully when scipy
is not installed.

**Specific question**: Which Python source files in `pandas-dev/pandas` contain a
`from scipy.stats import` statement (i.e., directly import functions or classes from
`scipy.stats` at runtime)?

Include files in any part of the `pandas-dev/pandas` codebase — production code **and** test
files. Do not include files that only mention `scipy.stats` in docstrings or comments.

## Context

You are onboarding to a polyrepo Python scientific stack. The local `/workspace/` contains
`scikit-learn/scikit-learn` as a reference implementation of a well-maintained scipy consumer.

**Note:** The `pandas-dev/pandas` repository is accessible via Sourcegraph MCP tools:
- `pandas-dev/pandas` (dataframe-library)
- `numpy/numpy` (array-computing)
- `scipy/scipy` (scientific-computing)

## Output Format

Create a file at `/workspace/answer.json` with your findings:

```json
{
  "files": [
    {"repo": "pandas-dev/pandas", "path": "relative/path/to/file.py"}
  ],
  "text": "Narrative summary of your findings, citing the repos and file paths."
}
```

List all files that contain `from scipy.stats import`. Your answer is evaluated against
a closed-world oracle — completeness matters.

## Evaluation

Your answer will be scored on:
- **File recall and precision**: Did you find all pandas files that `from scipy.stats import`?
- **Provenance**: Does your narrative cite the repo and file paths found?
