# Fix Admin List Filter Display for Empty Querysets

**Repository:** django/django
**Your Team:** Admin UI Team
**Access Scope:** You are assigned to the `django/contrib/admin/` package only.

## Context

You are a developer on the Django Admin UI team. Your access is limited to the `django/contrib/admin/` package. Other contrib packages (`django/contrib/auth/`, `django/contrib/sessions/`, etc.) belong to other teams — you may understand their public APIs by reading documentation and type signatures, but you must not modify or directly inspect their internal implementation files.

## Bug Report

When a `ModelAdmin` uses `list_filter` with a `RelatedFieldListFilter` and the related model's queryset is empty, the filter sidebar still renders the filter widget with a "All" option but no other choices. This causes confusion because:

1. The filter title still appears in the sidebar even when there are no choices to filter by
2. Clicking "All" triggers an unnecessary page reload

## Task

Fix the `RelatedFieldListFilter` in `django/contrib/admin/filters.py` so that when the related queryset has no items (empty choices), the filter's `has_output()` method returns `False`, hiding the filter from the sidebar entirely.

**YOU MUST IMPLEMENT CODE CHANGES.**

### Requirements

1. Modify `RelatedFieldListFilter.has_output()` in `django/contrib/admin/filters.py` to return `False` when choices (excluding the "All" option) are empty
2. The fix must not break existing filter behavior when choices exist
3. You may need to trace how `FieldListFilter` and its subclasses work — use search to find the class hierarchy and understand the `choices()` method contract
4. The admin filter system uses lookups defined across multiple files (`filters.py`, `options.py`, `views/main.py`) — you'll need to understand how they connect

### Hints

- `RelatedFieldListFilter` is defined in `django/contrib/admin/filters.py`
- The `has_output()` method on the base `ListFilter` class returns `True` by default
- The `choices()` method yields dicts with display values — the first is always "All"
- Understanding the `ChangeList` in `django/contrib/admin/views/main.py` helps understand how filters are rendered
- The related field's queryset comes through Django's ORM — you need to check if `self.lookup_choices` is empty

## Success Criteria

- `RelatedFieldListFilter.has_output()` returns `False` when no filter choices exist (beyond "All")
- Existing filters with choices continue to display correctly
- Changes are limited to `django/contrib/admin/` files only
