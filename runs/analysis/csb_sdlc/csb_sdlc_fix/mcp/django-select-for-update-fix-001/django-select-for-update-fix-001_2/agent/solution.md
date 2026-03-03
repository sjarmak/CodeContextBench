# Django select_for_update(of) Crash with Annotation Expressions - Analysis

## Files Examined

- **django/db/models/sql/compiler.py** — Entry point `get_select_for_update_of_arguments()` at line 1405 and its nested helper functions
- **django/db/models/query.py** — `values_list()` method at line 1369 and `_values()` at line 1355
- **django/db/models/sql/query.py** — `set_values()` method at line 2492 (controls how field selection is built)
- **django/db/models/expressions.py** — `Col` class at line 1287 (defines the `.target` attribute on column references)

## Dependency Chain

1. **Symptom observed in**: User calls `Person.objects.select_for_update(of=("self",)).values_list(Concat(Value("Dr. "), F("name")), "born")`

2. **Called from**: `django/db/models/query.py:1369` — `values_list()` method processes the annotation expression and regular fields

3. **Processed by**: `django/db/models/query.py:1355` — `_values()` converts expression arguments to annotations via `annotate()`

4. **Then calls**: `django/db/models/sql/query.py:2492` — `set_values()` marks which fields are selected and sets `self.query.selected`

5. **SQL generation in**: `django/db/models/sql/compiler.py:248` — `get_select()` method builds the select list using `self.query.selected`

6. **Bug triggered by**: `django/db/models/sql/compiler.py:1405` — `get_select_for_update_of_arguments()` method attempts to determine which model columns are selected in order to apply the FOR UPDATE OF clause

## Root Cause

- **File**: `django/db/models/sql/compiler.py`
- **Functions**:
  - `get_select_for_update_of_arguments()` at line 1405
  - `_get_parent_klass_info()` (nested helper, line 1411)
  - `_get_first_selected_col_from_model()` (nested helper, line 1430)
- **Lines with bug**:
  - Line 1424-1425 (in `_get_parent_klass_info()`)
  - Line 1440 (in `_get_first_selected_col_from_model()`)

**Explanation**:

The bug occurs because of a mismatch between how `select_fields` is populated and how it's used:

1. At lines 262-267 in `get_select()`, `select_fields` is calculated assuming model columns are at specific positions (from index `len(extra_select)` to `len(extra_select) + len(cols)`).

2. This assumption is valid when `self.query.selected is None` (default behavior), because the select list is built as: extra_select items → model columns → annotation items (lines 271-278).

3. However, when `values_list()` is called with expression arguments, `self.query.selected` is not None (line 280). The selected list is then built by iterating through `self.query.selected.items()` (lines 280-290), which returns items in the order they appear in the dictionary. **The annotation expressions can appear before model field columns in this dictionary**.

4. When the select list is rebuilt from `self.query.selected` at lines 280-290, annotation expressions (like `Concat()`) are added to the select list. These are `Expression` objects, not `Col` objects, so they **do not have a `.target` attribute**.

5. The `get_select_for_update_of_arguments()` method uses `select_fields` to find which selected items correspond to model columns by checking if `self.select[select_index][0].target.model == concrete_model` (lines 1424-1425, 1440).

6. **The crash occurs** because when `select_fields` contains an index pointing to an annotation expression (which doesn't have `.target`), accessing `.target.model` raises an `AttributeError`.

### Why This Happens

When `values_list(Concat(...), "name")` is called:
- The `Concat` expression becomes an annotation
- `set_values()` creates `self.query.selected = {"concat1": "concat1", "name": 0}` (or similar)
- In `get_select()`, this dictionary is iterated, adding the expression first, then the field
- But `select_fields` still points to indices assuming the old order
- When annotation expressions are added to the select list, `select_fields` indices now point to expressions instead of columns

## Proposed Fix

The fix is to add `hasattr(expr, "target")` checks before accessing the `.target` attribute. This follows the pattern already used at line 212 in the same file:

```python
if (
    hasattr(expr, "target")
    and expr.target.primary_key
    and self.connection.features.allows_group_by_selected_pks_on_model(
        expr.target.model
    )
):
```

### Implementation

There are two locations in `django/db/models/sql/compiler.py` that need fixes:

#### Fix 1: `_get_parent_klass_info()` function (lines 1419-1427)

```diff
             "select_fields": [
                 select_index
                 for select_index in klass_info["select_fields"]
                 # Selected columns from a model or its parents.
                 if (
+                    hasattr(self.select[select_index][0], "target")
+                    and (
-                    self.select[select_index][0].target.model == parent_model
-                    or self.select[select_index][0].target.model in all_parents
+                        self.select[select_index][0].target.model == parent_model
+                        or self.select[select_index][0].target.model in all_parents
+                    )
                 )
             ],
```

#### Fix 2: `_get_first_selected_col_from_model()` function (lines 1439-1441)

```diff
         def _get_first_selected_col_from_model(klass_info):
             """
             Find the first selected column from a model. If it doesn't exist,
             don't lock a model.

             select_fields is filled recursively, so it also contains fields
             from the parent models.
             """
             concrete_model = klass_info["model"]._meta.concrete_model
             for select_index in klass_info["select_fields"]:
-                if self.select[select_index][0].target.model == concrete_model:
+                if (
+                    hasattr(self.select[select_index][0], "target")
+                    and self.select[select_index][0].target.model == concrete_model
+                ):
                     return self.select[select_index][0]
```

## Analysis

### The Bug Manifestation

When executing:
```python
Person.objects.select_for_update(of=("self",)).values_list(
    Concat(Value("Dr. "), F("name")), "born"
)
```

The error occurs:
```
AttributeError: 'Concat' object has no attribute 'target'
```

This happens at line 1440 or 1424 when the code tries to access `.target.model` on an annotation expression.

### Step-by-Step Execution Trace

1. **`values_list()` is called** (line 1369 in query.py)
   - Arguments: `Concat(Value("Dr. "), F("name"))` and `"born"`
   - The Concat expression is converted to a keyword argument via naming

2. **`_values()` is called** (line 1355 in query.py)
   - The expression keyword arguments are passed to `annotate()`, creating annotations
   - `query.set_values([field_names])` is called with field names in the order: `["concat1", "born"]`

3. **`set_values()` is called** (line 2492 in query.py)
   - Sets `self.query.selected = {"concat1": "concat1", "born": 0}` (or similar dict)
   - This marks which fields should be selected and in what order

4. **`get_select()` is called** (line 248 in compiler.py)
   - Line 253: `self.query.default_cols = False` (because values() was used)
   - Lines 262-267: `select_fields = [0, 1]` (range starting from `len(extra_select)`)
   - Lines 280-290: Builds `selected` list by iterating `self.query.selected.items()`
     - First item: `("concat1", Concat(...))` → added to selected
     - Second item: `("born", 0)` → gets replaced with `cols[0]` (the "born" column)
   - Lines 292-295: Builds final `self.select` list:
     - `self.select[0] = (Concat(...), "concat1")`
     - `self.select[1] = (Col(...), None)`

5. **`get_select_for_update_of_arguments()` is called** (line 1405 in compiler.py)
   - Tries to find the first selected column from the Person model to apply FOR UPDATE OF
   - `select_fields = [0, 1]` (from step 4)
   - For `select_fields[0] = 0`:
     - Accesses `self.select[0][0]` → gets the `Concat(...)` expression
     - **Attempts to access `.target` attribute** → CRASH! `Concat` has no `.target` attribute

### Why This Happens

The root cause is **inconsistent indexing assumptions**:

- **`select_fields` calculation** (line 264-266): Assumes model columns are at indices `len(extra_select)` through `len(extra_select) + len(cols)`
- **`select` list construction when `self.query.selected` is not None** (lines 280-290): Uses the order from `self.query.selected.items()`, which can have annotations before model columns

When `values_list()` with expression arguments is used, the expression dictionary order changes, causing annotation expressions to appear at indices that `select_fields` expects model columns to be.

### Why the Existing Code Fails

The code at lines 1424-1425 and 1440 makes an unsafe assumption:
```python
if self.select[select_index][0].target.model == concrete_model:
```

This assumes:
1. Every item in `self.select` at an index in `select_fields` is a `Col` object
2. All `Col` objects have a `.target` attribute

However, when annotation expressions are present, these assumptions fail:
- Annotation expressions (Concat, F, Case, etc.) are `Expression` objects, not `Col` objects
- Expression objects do not have a `.target` attribute

### Why the Fix Works

The fix adds a defensive check:
```python
if (
    hasattr(self.select[select_index][0], "target")
    and self.select[select_index][0].target.model == concrete_model
):
```

This properly handles both cases:
1. **When select_index points to a Col object**: The `hasattr()` check passes, and the model comparison works correctly
2. **When select_index points to an annotation Expression**: The `hasattr()` check fails, the expression is skipped, and the loop continues looking for an actual model column

This is correct behavior because:
- Annotation expressions don't represent model columns that can be locked with FOR UPDATE OF
- The function is specifically looking for "the first selected **column** from a model" (emphasis from docstring at line 1432)
- Skipping annotation expressions correctly focuses on finding model field columns

The fix is minimal and correct because:
- It only adds defensive checks
- It maintains backward compatibility (existing code paths unaffected)
- It follows the established pattern in the same file (line 212)
- It correctly handles the case where `select_fields` points to annotation expressions (which should be skipped when looking for model columns)

---

## Summary

**The Problem**: When `select_for_update(of=("self",))` is combined with `values_list()` containing annotation expressions, the code crashes with `AttributeError` because it tries to access `.target.model` on annotation expressions that don't have a `.target` attribute.

**The Root Cause**: The `select_fields` index calculation assumes model columns are at specific positions in the select list. However, when `values_list()` with expression arguments is used, annotation expressions can appear before model columns, causing `select_fields` indices to point to expressions instead of Col objects.

**The Solution**: Add `hasattr(self.select[select_index][0], "target")` checks before accessing `.target.model` in two places:
1. Line 1424-1425 in `_get_parent_klass_info()`
2. Line 1440 in `_get_first_selected_col_from_model()`

This defensive check follows the existing pattern at line 212 and properly skips annotation expressions while finding model columns for the FOR UPDATE OF clause.
