# django-request-factory-refac-001: Rename RequestFactory

## Task Type: Cross-File Refactoring (Rename)

Rename RequestFactory → TestRequestBuilder across Django.

## Key Reference Files
- `django/test/client.py` — class definition
- `django/test/__init__.py` — exports
- `tests/` — 25+ usage sites

## Search Strategy
- Search for `class RequestFactory` to find definition
- Search for `RequestFactory` across codebase for all references
- Search for `from django.test import` for import patterns
