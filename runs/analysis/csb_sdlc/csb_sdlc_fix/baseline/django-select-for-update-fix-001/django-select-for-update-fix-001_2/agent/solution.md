# Django select_for_update(of) Crash with Annotation Expressions - Root Cause Analysis

## Files Examined
- `/workspace/django/db/models/sql/compiler.py` — Entry point and buggy method `get_select_for_update_of_arguments()`
- `/workspace/django/db/models/sql/query.py` — `set_values()` method that sets `self.selected` when `values_list()` is called
- `/workspace/django/db/models/query.py` — `values_list()` method that triggers the queryset to use `values()` behavior
- `/workspace/django/db/models/expressions.py` — `Col` class that has `.target` attribute vs. annotation expressions that don't

## Dependency Chain

1. **Symptom observed in**: `django/db/models/sql/compiler.py:get_select_for_update_of_arguments()`
   - User code calls: `Person.objects.select_for_update(of=("self",)).values_list(Concat(...), "field")`
   - This crashes with `AttributeError: 'Concat' object has no attribute 'target'`

2. **Called from**: `django/db/models/sql/compiler.py:as_sql()`
   - Line 884 calls `get_select_for_update_of_arguments()` to get the table aliases for the FOR UPDATE OF clause

3. **Triggered by**: `django/db/models/query.py:values_list()`
   - User calls `values_list(Concat(Value("Dr. "), F("name")), "born")`
   - This calls `_values()` which calls `set_values()` on the query object

4. **Root cause mechanism**:
   - `django/db/models/sql/query.py:set_values()` (line 2558) sets `self.selected` as an ordered dict
   - `django/db/models/sql/compiler.py:get_select()` (lines 270-290) uses `self.selected.items()` to build the select list when `self.query.selected is not None`
   - This causes annotation expressions to be mixed with model field columns in the select list

5. **Bug triggered at**: `django/db/models/sql/compiler.py:get_select_for_update_of_arguments()` lines 1424-1425 and 1440

## Root Cause

### File
`/workspace/django/db/models/sql/compiler.py`

### Functions
- `get_select_for_update_of_arguments()` (line 1405)
- Helper function `_get_parent_klass_info()` (line 1411)
- Helper function `_get_first_selected_col_from_model()` (line 1430)

### Lines
- **Line 1424-1425** (in `_get_parent_klass_info()`):
  ```python
  self.select[select_index][0].target.model == parent_model
  or self.select[select_index][0].target.model in all_parents
  ```

- **Line 1440** (in `_get_first_selected_col_from_model()`):
  ```python
  if self.select[select_index][0].target.model == concrete_model:
  ```

### Explanation

The bug occurs because:

1. **Before the field ordering change**: When `values_list()` was called, the select list was always built in the order: extra_select items → model field columns → annotations. The `klass_info["select_fields"]` indices pointed to model field columns at fixed positions.

2. **After the field ordering change**: With commit related to #28900 ("Made SELECT respect the order specified by values(*selected)"), the `get_select()` method was modified to respect the order specified by `self.query.selected` when it's not None (lines 270-290 of `get_select()`). This allows annotations to appear anywhere in the select list, not just at the end.

3. **The incompatibility**:
   - `self.select[select_index]` returns a 3-tuple `(expression, (sql, params), alias)`
   - When accessing `self.select[select_index][0]`, we get the `expression`
   - For model field columns, the expression is a `Col` object which has a `.target` attribute
   - For annotation expressions (like `Concat`, `F`, `Value`, etc.), these are `BaseExpression` subclasses that **do not have** a `.target` attribute
   - The code assumes all items at indices in `klass_info["select_fields"]` are `Col` objects, but this assumption breaks when annotations appear before model fields

4. **Why `.target.model` fails**:
   - The `Col` class (defined in `django/db/models/expressions.py:1287`) has `self.target` as a field object
   - Annotation expressions don't have this attribute
   - When annotation expressions are mixed into the select list before model fields, accessing `.target` raises `AttributeError`

## Proposed Fix

The fix is to add a guard to check if the expression has a `.target` attribute (i.e., is a `Col` object) before attempting to access `.target.model`. Expressions without this attribute should be skipped.

```diff
--- a/django/db/models/sql/compiler.py
+++ b/django/db/models/sql/compiler.py
@@ -1420,9 +1420,11 @@ class SQLCompiler:
                     select_index
                     for select_index in klass_info["select_fields"]
                     # Selected columns from a model or its parents.
-                    if (
-                        self.select[select_index][0].target.model == parent_model
-                        or self.select[select_index][0].target.model in all_parents
+                    if (
+                        hasattr(self.select[select_index][0], "target")
+                        and (
+                            self.select[select_index][0].target.model == parent_model
+                            or self.select[select_index][0].target.model in all_parents
+                        )
                     )
                 ],
             }

@@ -1437,7 +1439,8 @@ class SQLCompiler:
             concrete_model = klass_info["model"]._meta.concrete_model
             for select_index in klass_info["select_fields"]:
-                if self.select[select_index][0].target.model == concrete_model:
+                if (hasattr(self.select[select_index][0], "target")
+                    and self.select[select_index][0].target.model == concrete_model):
                     return self.select[select_index][0]
```

## Analysis

### The Execution Path

1. User code:
   ```python
   Person.objects.select_for_update(of=("self",)).values_list(
       Concat(Value("Dr. "), F("name")), "born"
   )
   ```

2. `values_list()` (query.py:1369-1403) is called with two items:
   - `Concat(Value("Dr. "), F("name"))` — an annotation expression
   - `"born"` — a field name

   The method converts the annotation expression into a temporary annotation alias (e.g., "concat1") and calls `_values()` with both as field names plus the expression in `expressions` dict.

3. `_values()` (query.py:1355-1361) calls:
   - `annotate(**expressions)` to add the temporary annotation
   - `query.set_values(fields)` to specify which fields should be selected

4. `set_values()` (sql/query.py:2492-2558) sets up `self.selected` as an ordered dict:
   - Iterates through requested fields in order: `["concat1", "born"]`
   - Maps each field to its position or reference
   - Sets `self.selected = selected` at line 2558

5. When the query is executed, `setup_query()` calls `get_select()` (compiler.py:71-77, 230-333):
   - At line 270, since `self.query.selected is not None`, it enters the else block
   - Lines 280-290 iterate through `self.query.selected.items()` in order, which is `[("concat1", concat_expr), ("born", 1)]`
   - The `selected` list is built with these items in this order
   - Line 295 appends to `select` list in the same order
   - This means the select list now has: `[concat_expr_tuple, born_col_tuple, ...]` where `concat_expr_tuple[0]` is a `Concat` expression and `born_col_tuple[0]` is a `Col` object

6. Meanwhile, `klass_info["select_fields"]` was set at line 262-267 to `range(len(extra_select), len(extra_select) + len(cols))`:
   - This was computed when `cols` (the default columns) was established
   - These indices assume model fields are at fixed positions, but now they're mixed with annotations

7. When `get_select_for_update_of_arguments()` is called (line 884):
   - It calls `_get_first_selected_col_from_model()` at line 1473
   - This iterates through `klass_info["select_fields"]` indices
   - For each index, it accesses `self.select[select_index][0].target.model`
   - But if `self.select[select_index][0]` is a `Concat` expression instead of a `Col`, it fails with `AttributeError`

### Why the Fix Works

By adding `hasattr(self.select[select_index][0], "target")` check:

1. Only expressions with a `.target` attribute (i.e., `Col` objects representing model fields) are considered
2. Annotation expressions without `.target` are skipped
3. The method correctly identifies which select indices correspond to actual model field columns
4. For `select_for_update(of=...)`, we can still determine which tables need to be locked

### Key Insight

The root issue is a **mismatch between assumptions about select list ordering**:
- `klass_info["select_fields"]` assumes a fixed ordering (extra_select, then model fields)
- But when `values_list()` is called with mixed expressions and fields, the actual select list order becomes arbitrary
- The fix doesn't try to restore the old ordering; instead, it makes the code defensive against arbitrary ordering by checking expression types

