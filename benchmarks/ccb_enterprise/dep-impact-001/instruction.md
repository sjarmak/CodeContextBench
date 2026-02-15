# Impact Analysis: ModelAdmin.get_list_filter()

**Repository:** django/django
**Access Scope:** You may read any file. Write your results to `/workspace/submission.json`.

## Context

Django's admin framework allows customization via `ModelAdmin` subclasses. The method `get_list_filter()` in `django/contrib/admin/options.py` controls which filters appear in the admin list view. It is defined on the `ModelAdmin` class and can be overridden by subclasses.

A developer is planning to change the signature of `get_list_filter()` to accept an additional parameter. Before making this change, they need a complete impact analysis: which files in the Django codebase would be affected?

## Task

Identify all files in the Django repository that define, override, call, or reference `get_list_filter`. Write your findings as a JSON array of file paths to `/workspace/submission.json`.

**YOU MUST CREATE A submission.json FILE.**

### Requirements

1. **Find the definition** — Locate where `get_list_filter` is defined in `django/contrib/admin/options.py`
2. **Find all overrides** — Search for classes that override `get_list_filter` (subclasses of `ModelAdmin` that define their own `get_list_filter` method)
3. **Find all callers** — Search for code that calls `get_list_filter()` or `.get_list_filter(`
4. **Find documentation references** — Search docs/ for mentions of `get_list_filter`
5. **Find test references** — Search tests/ for `get_list_filter` usage
6. **Write submission** — Create `/workspace/submission.json` containing a JSON array of all affected file paths, relative to the repository root

### Output Format

Create `/workspace/submission.json` with a JSON array of file paths:
```json
[
  "django/contrib/admin/options.py",
  "tests/some_test/test_file.py",
  "docs/some_doc.txt"
]
```

### Hints

- `get_list_filter` is defined as a method on `ModelAdmin` in `django/contrib/admin/options.py`
- There are test files in `tests/admin_changelist/` that test list filter behavior
- Documentation files (`.txt` format in `docs/`) may reference `get_list_filter`
- Use `find_references("get_list_filter")` for instant comprehensive results
- Check both `.py` files (code) and `.txt` files (docs) in your search
- The complete list has approximately 5 files

## Success Criteria

- `/workspace/submission.json` exists and is valid JSON
- The file contains a JSON array of file path strings
- High precision: all listed files actually reference `get_list_filter`
- High recall: no files that reference `get_list_filter` are missed
- Scoring uses F1 measure (harmonic mean of precision and recall)
