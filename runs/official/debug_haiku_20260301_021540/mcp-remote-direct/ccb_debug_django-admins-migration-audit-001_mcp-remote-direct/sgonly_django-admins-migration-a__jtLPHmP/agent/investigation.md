# Django ADMINS/MANAGERS Settings Format Migration Audit

## Summary

Django is transitioning the `ADMINS` and `MANAGERS` settings from a list of `(name, email)` tuples to simple email address strings. The migration is tracked in Django ticket #36138. This audit identifies all code paths, tests, and documentation that consume the old tuple format and must be updated to support the new string-only format.

**Current Status**: Django 6.0 deprecated tuple format (RemovedInDjango70Warning). Full removal is targeted for Django 7.0.

---

## Root Cause

The old format `[(name, email), ...]` is being replaced with `[email_string, ...]` for the following reasons:

1. **Django never used the name portion** - The name was extracted by the legacy code but unused
2. **Email formatting is more flexible** - Users can use format strings like `'"Full Name" <address@example.com>'` or `email.utils.formataddr()`
3. **Simpler API** - Direct email strings are more intuitive than tuples

The core consumption point is `django/core/mail/__init__.py:_send_server_message()` which converts the old format and issues deprecation warnings.

---

## Evidence: Code References with File Paths and Line Numbers

### 1. Core Email Functions

#### File: `django/core/mail/__init__.py`
- **Lines 141-148**: Deprecation handling for tuple format
  - Detects old tuple format: `all(isinstance(a, (list, tuple)) and len(a) == 2 for a in recipients)`
  - Extracts email from tuple: `recipients = [a[1] for a in recipients]`
  - Issues warning: `RemovedInDjango70Warning`
- **Lines 150-155**: Format validation
  - Validates recipients are list/tuple of strings or Promise
  - Raises `ImproperlyConfigured` if format is invalid
- **Functions `mail_admins()` (line 169)** and **`mail_managers()` (line 183)** call `_send_server_message()`

### 2. Logging Handler

#### File: `django/utils/log.py`
- **Line 97**: `AdminEmailHandler.emit()` checks if `settings.ADMINS` is empty
  - Currently handles both tuple and string formats through `mail.mail_admins()` call (line 138-140)
  - Will need validation after tuple format is removed

### 3. Middleware

#### File: `django/middleware/common.py`
- **Line 129**: `BrokenLinkEmailsMiddleware.process_response()` calls `mail_managers()`
  - Only passes message text, relies on `mail_managers()` for format handling

### 4. Management Command

#### File: `django/core/management/commands/sendtestemail.py`
- **Lines 42-46**: Calls `mail_managers()` and `mail_admins()`
  - Uses the functions but doesn't directly handle tuple format

### 5. Default Settings

#### File: `django/conf/global_settings.py`
- **Lines 24-26**: ADMINS default definition with **outdated comment**
  ```python
  # People who get code error notifications. In the format
  # [('Full Name', 'email@example.com'), ('Full Name', 'anotheremail@example.com')]
  ADMINS = []
  ```
  - **This comment describes the OLD deprecated format and must be updated**
- **Line 174**: `MANAGERS = ADMINS`

---

## Test Files Using Old Format

### File: `tests/mail/tests.py`
- **Lines 1865-1888**: `test_deprecated_admins_managers_tuples()`
  - Tests both tuple formats: list of tuples and list of lists
  - Expects `RemovedInDjango70Warning`
  - Will be removed in Django 7.0
- **Lines 1890-1901**: `test_wrong_admins_managers()`
  - Tests invalid format detection
  - Comments indicate cases will be uncommented after tuple removal

### File: `tests/mail/test_sendtestemail.py`
- **Lines 6-8**: Uses new string format in `@override_settings`
  ```python
  ADMINS=["admin@example.com", "admin_and_manager@example.com"],
  MANAGERS=["manager@example.com", "admin_and_manager@example.com"],
  ```
  - Already compliant with new format ✓

### File: `tests/logging_tests/tests.py`
- **Line 251**: `AdminEmailHandlerTest.test_accepts_args()` uses new string format
  ```python
  ADMINS=["admin@example.com"],
  ```
  - Already compliant ✓

### File: `tests/middleware/tests.py`
- **Line 392**: `BrokenLinkEmailsMiddlewareTest` uses new string format
  ```python
  MANAGERS=["manager@example.com"],
  ```
  - Already compliant ✓

---

## Documentation References

### File: `django/conf/global_settings.py` (Lines 24-26)
**CRITICAL**: Comment shows old tuple format - MUST BE UPDATED

### File: `docs/ref/settings.txt`
- **Lines 43-62**: ADMINS setting documentation
  - **Lines 55-57**: Shows NEW string format examples (✓ already updated)
  - **Lines 59-61**: Version change note documents the migration
- **Lines 2070-2084**: MANAGERS setting documentation
  - **Line 2081-2083**: Version change note documents the migration

### File: `docs/releases/6.0.txt`
- **Lines 331-334**: Deprecation notes (already documented)

### File: `docs/internals/deprecation.txt`
- **Lines 31-32**: Lists removal in Django 7.0 (already documented)

### File: `docs/topics/email.txt`
- **Lines 89-92**: MANAGERS setting reference
- **Lines 166-184**: `mail_admins()` documentation
- **Lines 188-192**: `mail_managers()` documentation
- These appear to reference the settings but don't detail the format

### File: `docs/howto/error-reporting.txt`
- **Lines 44-45**: References ADMINS setting for error reporting
- Doesn't specify format details

---

## Affected Components

1. **Email System** (`django/core/mail/`)
   - Core function: `_send_server_message()` - handles tuple-to-string conversion
   - High-level functions: `mail_admins()`, `mail_managers()`

2. **Logging** (`django/utils/log.py`)
   - `AdminEmailHandler.emit()` - indirectly affected via `mail_admins()` call

3. **Middleware** (`django/middleware/common.py`)
   - `BrokenLinkEmailsMiddleware.process_response()` - uses `mail_managers()`

4. **Management Commands** (`django/core/management/commands/`)
   - `sendtestemail.py` - uses `mail_admins()` and `mail_managers()`

5. **Default Configuration** (`django/conf/global_settings.py`)
   - Global ADMINS and MANAGERS defaults

6. **Test Suite** (multiple test files)
   - Tests verifying deprecation behavior
   - Tests verifying format validation

---

## Third-Party Compatibility Concerns

### What Breaks for Users with Old-Format Settings

When Django 7.0 removes tuple support, user code with old-format settings will:

1. **Raise `ImproperlyConfigured` exception** if ADMINS/MANAGERS contains tuples
   - Error message: `"The {setting_name} setting must be a list of email address strings."`
   - Crash location: `django/core/mail/__init__.py:_send_server_message()` (lines 150-155)
   - Affected functions: Any call to `mail_admins()`, `mail_managers()`, or logging that triggers email

2. **No graceful fallback** - the old code path is completely removed

### Migration Path for Users

Users must update their settings from:
```python
ADMINS = [("John", "john@example.com"), ("Jane", "jane@example.com")]
```

To one of:
```python
# Simple format
ADMINS = ["john@example.com", "jane@example.com"]

# With display names
ADMINS = ['"John" <john@example.com>', '"Jane" <jane@example.com>']

# Using email.utils.formataddr()
from email.utils import formataddr
ADMINS = [
    formataddr(("John", "john@example.com")),
    formataddr(("Jane", "jane@example.com")),
]
```

---

## Migration Checklist: Files Requiring Changes for Django 7.0

### Phase 1: Code Removal (Django 7.0)

#### High Priority - Core Functionality

| File | Line(s) | Change Required |
|------|---------|-----------------|
| `django/core/mail/__init__.py` | 140-148 | **REMOVE** deprecated tuple handling and RemovedInDjango70Warning import |
| `django/core/mail/__init__.py` | 150-155 | **SIMPLIFY** validation to assume only string format (remove tuple check) |
| `django/core/mail/__init__.py` | 5 | Remove `warnings` import if no longer needed |
| `django/core/mail/__init__.py` | 27 | Remove `RemovedInDjango70Warning` from imports |

#### High Priority - Documentation & Comments

| File | Line(s) | Change Required |
|------|---------|-----------------|
| `django/conf/global_settings.py` | 24-25 | **UPDATE comment** from tuple format example to string format |
| `docs/internals/deprecation.txt` | 31-32 | **REMOVE** this item from deprecation timeline (it's been removed) |

#### Medium Priority - Tests

| File | Line(s) | Change Required |
|------|---------|-----------------|
| `tests/mail/tests.py` | 1865-1888 | **DELETE** `test_deprecated_admins_managers_tuples()` test |
| `tests/mail/tests.py` | 1890-1901 | **UNCOMMENT** currently-commented invalid format test cases (lines 1896-1897) |
| `tests/mail/tests.py` | 1893-1894 | **DELETE** comment block indicating removal in Django 7.0 |

#### Low Priority - Docstrings & Help Text

| File | Line(s) | Change Required |
|------|---------|-----------------|
| `django/core/management/commands/sendtestemail.py` | 24, 29 | Verify help text is still accurate (likely no change needed) |

### Phase 2: Validation Verification (Django 7.0)

| File | Line(s) | Testing Required |
|------|---------|-----------------|
| `django/core/mail/__init__.py` | 150-155 | Verify that non-string formats raise proper `ImproperlyConfigured` exception |
| `tests/mail/tests.py` | 1890-1901 | Run test suite to confirm invalid format detection still works |

### Phase 3: Related Documentation Updates

| File | Action | Note |
|------|--------|------|
| `docs/releases/7.0.txt` | **ADD** to "Features removed" section | Document removal of tuple format support |
| `docs/ref/settings.txt` | **VERIFY** lines 43-62, 2070-2084 | Ensure no mention of old tuple format in version-changed sections |

---

## Detailed Change Summary

### `django/core/mail/__init__.py` (MOST CRITICAL)

**Current (Django 6.x) - Lines 127-166:**
```python
def _send_server_message(
    *,
    setting_name,
    subject,
    message,
    html_message=None,
    fail_silently=False,
    connection=None,
):
    recipients = getattr(settings, setting_name)
    if not recipients:
        return

    # RemovedInDjango70Warning.
    if all(isinstance(a, (list, tuple)) and len(a) == 2 for a in recipients):
        warnings.warn(
            f"Using (name, address) pairs in the {setting_name} setting is deprecated."
            " Replace with a list of email address strings.",
            RemovedInDjango70Warning,
            stacklevel=2,
        )
        recipients = [a[1] for a in recipients]

    if not isinstance(recipients, (list, tuple)) or not all(
        isinstance(address, (str, Promise)) for address in recipients
    ):
        raise ImproperlyConfigured(
            f"The {setting_name} setting must be a list of email address strings."
        )
    # ... rest of function
```

**Target (Django 7.0) - Simplified:**
```python
def _send_server_message(
    *,
    setting_name,
    subject,
    message,
    html_message=None,
    fail_silently=False,
    connection=None,
):
    recipients = getattr(settings, setting_name)
    if not recipients:
        return

    if not isinstance(recipients, (list, tuple)) or not all(
        isinstance(address, (str, Promise)) for address in recipients
    ):
        raise ImproperlyConfigured(
            f"The {setting_name} setting must be a list of email address strings."
        )
    # ... rest of function
```

**Changes:**
1. Remove lines 140-148 (deprecation handling)
2. Remove tuple check from validation (line 141)
3. Remove `warnings` and `RemovedInDjango70Warning` imports if unused elsewhere

### `django/conf/global_settings.py` (Lines 24-26)

**Current:**
```python
# People who get code error notifications. In the format
# [('Full Name', 'email@example.com'), ('Full Name', 'anotheremail@example.com')]
ADMINS = []
```

**Target:**
```python
# People who get code error notifications. Must be a list of email address strings.
# Example: ["john@example.com", '\"John Doe\" <john@example.com>']
ADMINS = []
```

---

## Risk Assessment

### Low Risk Changes
- Removing deprecation warnings and old-format handling code
- Updating comments and documentation
- Deleting deprecation tests

### Medium Risk Changes
- Validation logic simplification (ensure exception handling is correct)
- Import statement cleanup

### Testing Required Before Release
1. Run full test suite with ADMINS/MANAGERS as string lists
2. Verify exception is raised for invalid formats
3. Test with `AdminEmailHandler` in logging configuration
4. Test `BrokenLinkEmailsMiddleware` functionality
5. Test management command `sendtestemail` with both formats (should fail gracefully with non-string formats)

---

## Implementation Recommendations

### For Django 7.0 Release:

1. **Immediate**: Update docstring in `global_settings.py` to show new format clearly
2. **Before removal**: Add detailed migration guide to release notes
3. **At removal**:
   - Delete tuple handling code
   - Update validation
   - Remove deprecation test
   - Uncomment test cases for invalid formats
4. **Post-release**: Monitor bug reports for users still using old format

### For User Communication:

- Add prominent deprecation warning in Django 6.x release notes
- Include migration example in official documentation
- Provide automated tool/script for settings migration if possible

---

## Summary Statistics

| Metric | Count |
|--------|-------|
| Files with ADMINS/MANAGERS references | 18 |
| Lines of deprecation code to remove | ~9 lines |
| Core functions affected | 2 (`mail_admins`, `mail_managers`) |
| Test files already using new format | 3/5 |
| Deprecation tests to remove | 1 major test function |
| Documentation sections to verify | 6 |
| Critical files requiring changes | 2 (`core/mail/__init__.py`, `conf/global_settings.py`) |

---

## Related Issues & Tickets

- **Django Ticket**: #36138 (ADMINS/MANAGERS format change)
- **Deprecation Timeline**: Deprecated in Django 6.0, removal targeted for Django 7.0
- **Warning Type**: `RemovedInDjango70Warning`
