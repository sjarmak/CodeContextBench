# Add Encoding-Aware HTML Escaping Function to Django

**Repository:** django/django
**Access Scope:** You may modify `django/utils/html.py`. You may read any file to understand the legacy encoding chain.

## Context

Django's HTML escaping pipeline (`escape()`, `conditional_escape()`, `format_html()`) assumes all input is UTF-8. However, Django's GIS module processes data from GDAL sources that may use non-UTF-8 encodings. Currently, GIS code calls `force_str()` from `django/utils/encoding.py` to convert to Python strings before rendering, but there is no way to escape HTML while preserving encoding awareness.

The legacy encoding functions in `django/utils/encoding.py` have existed since early Django versions. They have **no type hints**, use old-style parameter conventions (`strings_only`, `errors` mode), and handle edge cases from the Python 2 → 3 transition. Understanding how they work requires reading the actual implementation — the naming and parameters are not self-documenting.

## Task

Add an `escape_with_encoding()` function to `django/utils/html.py` that combines encoding conversion and HTML escaping in a single operation, properly handling the legacy `force_str()` parameter conventions.

**YOU MUST IMPLEMENT CODE CHANGES.**

### Requirements

1. Read `django/utils/encoding.py` to understand the legacy encoding functions:
   - `force_str(s, encoding='utf-8', strings_only=False, errors='strict')` — what does `strings_only` do? When is it `True`?
   - `smart_str()` — how does it differ from `force_str()`? When would you use one vs the other?
   - `is_protected_type()` — what types are "protected" and why?
   - These functions have NO type hints — you must read the implementation to understand behavior

2. Read `django/utils/html.py` to understand the existing escaping chain:
   - `escape(text)` — how does it handle non-string inputs?
   - `conditional_escape(text)` — what is the `__html__` convention? How does it handle `Promise` (lazy) objects?
   - `format_html()` and `format_html_join()` — how do they use `conditional_escape()`?

3. Trace real usage of the legacy encoding + escaping chain:
   - `django/contrib/gis/gdal/feature.py` calls `force_str(name, self.encoding, strings_only=True)` — understand why all three parameters matter
   - `django/template/base.py` `render_value_in_context()` calls `conditional_escape()` — trace the full path from value → escape → rendered string
   - `django/forms/utils.py` `flatatt()` uses `format_html_join()` — understand how attribute values get escaped

4. Add to `django/utils/html.py`:
   ```python
   def escape_with_encoding(text, encoding='utf-8', strings_only=False, errors='strict'):
       """
       Convert text to a string using the given encoding, then HTML-escape it.
       Combines force_str() and conditional_escape() for encoding-aware escaping.
       Respects the strings_only parameter: if True and text is a protected type
       (int, float, datetime, etc.), returns it unconverted.
       """
   ```

5. The function must:
   - Call `force_str()` with all four parameters to convert input
   - If `strings_only=True` and `force_str()` returns a non-string (protected type), return it as-is without escaping
   - Otherwise, pass the result through `conditional_escape()`
   - Handle `Promise` (lazy) objects correctly (force evaluation before escaping)
   - Import `force_str` from `django.utils.encoding` and use existing `conditional_escape`

### Hints

- `force_str()` with `strings_only=True` returns the original value unchanged if it's a "protected type" (int, float, Decimal, datetime, etc.)
- `conditional_escape()` handles `Promise` objects and `__html__` convention
- The GIS feature.py example shows why encoding matters: GDAL C API returns bytes in datasource-specific encoding
- Look at `is_protected_type()` in encoding.py to understand exactly which types are protected
- `format_html()` at line ~135 in html.py shows how existing escaping wraps `conditional_escape`

## Success Criteria

- `escape_with_encoding()` function exists in `django/utils/html.py`
- Correctly imports and calls `force_str()` with encoding, strings_only, and errors parameters
- Handles protected types (returns without escaping when strings_only=True)
- Passes non-protected results through `conditional_escape()`
- Valid Python syntax
- Changes limited to `django/utils/html.py`
