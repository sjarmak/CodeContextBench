# Add Bulk Soft-Delete Manager Method to Django ORM

**Repository:** django/django
**Access Scope:** You may modify files in `django/db/models/`. You may read any file to understand existing patterns.

## Context

You are adding a new ORM feature to Django. Your organization enforces strict coding policies for all contributions to the ORM layer.

## Company Coding Policies

**MANDATORY — All code changes MUST comply:**

1. **ORM-Only Policy:** All database interactions must use Django's ORM (QuerySet methods, model managers, F() expressions, etc.). Direct SQL queries using `cursor.execute()`, `raw()`, `connection.cursor()`, or any raw SQL strings are **strictly prohibited**.

2. **No Hardcoded Credentials:** Code must not contain hardcoded passwords, API keys, secrets, or connection strings. Use Django settings or environment variables.

3. **Documentation Required:** All new public functions, classes, and methods must have docstrings explaining their purpose, parameters, and return values.

4. **Type Safety:** All new functions should include type hints for parameters and return values.

## Feature Request

**From:** Backend Team
**Priority:** P2

We need a custom model manager method called `bulk_soft_delete` that marks multiple records as deleted without actually removing them from the database. This is a common pattern for audit compliance — we need to keep records but mark them inactive.

### Deliverables

Add a `SoftDeleteManager` class to Django's model manager module that:

1. Provides a `bulk_soft_delete(queryset_or_ids, deleted_by=None)` method
2. Sets a `is_deleted=True` flag and `deleted_at` timestamp on matching records using ORM update operations
3. Returns the count of records soft-deleted
4. Optionally records who performed the deletion (the `deleted_by` parameter)
5. Works with Django's existing manager and queryset infrastructure — study how existing managers are implemented
6. Includes a `restore(queryset_or_ids)` method to undo soft-deletes

**YOU MUST IMPLEMENT CODE CHANGES.**

### Requirements

1. `SoftDeleteManager` class in Django's model managers module
2. `bulk_soft_delete()` and `restore()` methods
3. Must use ORM operations exclusively (QuerySet.update, F expressions, etc.)
4. Must comply with ALL company coding policies listed above
5. Valid Python syntax
6. Changes limited to `django/db/models/`

## Success Criteria

- `SoftDeleteManager` with `bulk_soft_delete()` and `restore()` methods
- Uses ORM exclusively (no raw SQL)
- All new functions have docstrings
- No hardcoded credentials
- Valid Python syntax
- Changes scoped to `django/db/models/`
