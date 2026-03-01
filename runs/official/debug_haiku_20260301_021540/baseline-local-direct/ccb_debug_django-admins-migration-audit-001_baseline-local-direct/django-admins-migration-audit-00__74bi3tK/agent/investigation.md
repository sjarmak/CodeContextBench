# Django ADMINS/MANAGERS Settings Format Migration Audit

## Summary

Django's `ADMINS` and `MANAGERS` settings are currently defined as lists of 2-tuples `[(name, email), ...]` in 9 Python files and 11 documentation files. The core validation and processing logic is centralized in `django/core/mail/__init__.py`, making this a manageable migration. However, this is a **breaking change** for all users who have existing configurations, requiring careful deprecation messaging and validation logic updates.

## Root Cause

The current implementation stores both display names and email addresses together in tuples for backward compatibility with early Django versions. The email extraction happens in the `_send_server_message()` function which:
1. Validates each item is a 2-tuple: `len(a) == 2`
2. Extracts the email address at index `[1]`
3. Uses display names only for documentation/comments (not displayed in emails)

The new format would eliminate the first element (display name) and store only email strings.

## Evidence

### Core Implementation Files

**`django/core/mail/__init__.py` (lines 122-147)** - **CRITICAL**
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

    if not all(isinstance(a, (list, tuple)) and len(a) == 2 for a in recipients):
        raise ValueError(f"The {setting_name} setting must be a list of 2-tuples.")

    mail = EmailMultiAlternatives(
        subject="%s%s" % (settings.EMAIL_SUBJECT_PREFIX, subject),
        body=message,
        from_email=settings.SERVER_EMAIL,
        to=[a[1] for a in recipients],  # <-- EMAIL EXTRACTION
        connection=connection,
    )
    if html_message:
        mail.attach_alternative(html_message, "text/html")
    mail.send(fail_silently=fail_silently)
```

**Change Required:** Replace tuple validation with string validation, change extraction from `a[1]` to `a`.

**`django/conf/global_settings.py` (line 24-26)**
```python
# People who get code error notifications. In the format
# [('Full Name', 'email@example.com'), ('Full Name', 'anotheremail@example.com')]
ADMINS = []
```

**Change Required:** Update comment to show new format, e.g. `['admin@example.com', 'admin2@example.com']`

**`django/conf/global_settings.py` (line 174)**
```python
MANAGERS = ADMINS
```

**Change Required:** No code change needed; will inherit new format from ADMINS.

### Logging/Error Handling

**`django/utils/log.py` (line 97)** - AdminEmailHandler class
```python
if (
    not settings.ADMINS
    # Method not overridden.
    and self.send_mail.__func__ is AdminEmailHandler.send_mail
):
    return
```

**Change Required:** No change needed; this only checks if ADMINS is truthy (not empty).

### Management Commands

**`django/core/management/commands/sendtestemail.py` (lines 42-46)**
```python
if kwargs["managers"]:
    mail_managers(subject, "This email was sent to the site managers.")

if kwargs["admins"]:
    mail_admins(subject, "This email was sent to the site admins.")
```

**Change Required:** No code change; calls existing `mail_admins()` and `mail_managers()` functions.

### Test Files Using Old Format

**`tests/mail/test_sendtestemail.py` (lines 7-14)** - Uses tuple format
```python
@override_settings(
    ADMINS=(
        ("Admin", "admin@example.com"),
        ("Admin and Manager", "admin_and_manager@example.com"),
    ),
    MANAGERS=(
        ("Manager", "manager@example.com"),
        ("Admin and Manager", "admin_and_manager@example.com"),
    ),
)
```

**`tests/mail/tests.py` - Multiple occurrences:**
- Line 1142: `ADMINS=[("nobody", "nobody@example.com")]`
- Line 1155: `MANAGERS=[("nobody", "nobody@example.com")]`
- Lines 1780-1805: `ADMINS` and `MANAGERS` validation tests
- Lines 1836-1837: Custom email addresses tests
- Line 1851: Empty settings tests

**`tests/logging_tests/tests.py` (lines 251-570)** - Multiple test classes
- Line 251: `ADMINS=[("whatever admin", "admin@example.com")]`
- Line 283: `ADMINS=[("whatever admin", "admin@example.com")]`
- Line 322: `ADMINS=[("admin", "admin@example.com")]`
- Line 344: `ADMINS=[("admin", "admin@example.com")]`
- Line 375: `ADMINS=[("whatever admin", "admin@example.com")]`
- Line 396: `MANAGERS=[("manager", "manager@example.com")]`
- Line 438: `ADMINS=[("A.N.Admin", "admin@example.com")]`
- Line 452: `ADMINS=[("admin", "admin@example.com")]`
- Line 474: `ADMINS=[]` (empty list - OK for new format)
- Line 570: `ADMINS=[("admin", "admin@example.com")]`

**`tests/view_tests/tests/test_debug.py` (lines 1454-1534)**
- Line 1454: `ADMINS=[("Admin", "admin@fattie-breakie.com")]`
- Line 1490: `ADMINS=[("Admin", "admin@fattie-breakie.com")]`
- Line 1533: `ADMINS=[("Admin", "admin@fattie-breakie.com")]`

**`tests/middleware/tests.py` (line 392)**
- `MANAGERS=[("PHD", "PHB@dilbert.com")]`

**Change Required:** Update all tuple format to string format.

### Documentation Files

**`docs/ref/settings.txt` (lines 43-57)** - ADMINS documentation
```
.. setting:: ADMINS

``ADMINS``
----------

Default: ``[]`` (Empty list)

A list of all the people who get code error notifications. When
:setting:`DEBUG=False <DEBUG>` and :class:`~django.utils.log.AdminEmailHandler`
is configured in :setting:`LOGGING` (done by default), Django emails these
people the details of exceptions raised in the request/response cycle.

Each item in the list should be a tuple of (Full name, email address). Example::

    [("John", "john@example.com"), ("Mary", "mary@example.com")]
```

**`docs/ref/settings.txt` (line 2073)** - MANAGERS documentation
```
A list in the same format as :setting:`ADMINS` that specifies who should get
broken link notifications when
:class:`~django.middleware.common.BrokenLinkEmailsMiddleware` is enabled.
```

**`docs/topics/email.txt` (lines 164-192)** - Function documentation
- Documents `mail_admins()` and `mail_managers()` functions
- References ADMINS/MANAGERS settings

**Other documentation files:**
- `docs/howto/error-reporting.txt` - Error reporting configuration guide
- `docs/ref/logging.txt` - Logging configuration reference
- `docs/ref/django-admin.txt` - Django admin command reference
- `docs/howto/deployment/checklist.txt` - Deployment checklist
- `docs/internals/contributing/writing-documentation.txt` - Contributor docs
- `docs/releases/3.0.txt` - Release notes (may reference settings format)

## Affected Components

### Core Modules
1. **django.core.mail** - Email sending utilities (CRITICAL)
2. **django.utils.log** - Logging and error handling (indirect dependency)
3. **django.conf** - Settings configuration (documentation)

### Commands
1. **django.core.management.commands.sendtestemail** - Test email command

### Middleware
1. **BrokenLinkEmailsMiddleware** - Uses MANAGERS setting via mail_managers()

### Test Coverage
All email and logging functionality tests use the old format.

## Third-Party Compatibility Concerns

### Breaking Changes for Users

**Current user code pattern:**
```python
ADMINS = [
    ("John Admin", "john@example.com"),
    ("Jane Admin", "jane@example.com"),
]
```

**Would break if code expects tuples:**
```python
for name, email in settings.ADMINS:  # FAILS: unpacking string
    send_notification(name, email)
```

### Migration Path Options

1. **Hard Break (Risky)**
   - Change format immediately
   - All existing settings become invalid
   - No backward compatibility

2. **Deprecation Warning (Recommended)**
   - Accept both formats temporarily
   - Validate and convert tuples to strings
   - Emit `PendingDeprecationWarning` for tuple format
   - Plan removal in Django N+2

3. **Validation Only (Safe)**
   - Accept only email strings immediately
   - Provide clear error message for tuples
   - Document migration path

## Recommendation: Migration Checklist

### Phase 1: Validation and Warnings (Next Release)

- [ ] **`django/core/mail/__init__.py`** (lines 122-147)
  - Modify `_send_server_message()` to accept both formats
  - Extract email from tuples: `[a[1] if isinstance(a, (tuple, list)) else a for a in recipients]`
  - Emit `DeprecationWarning` if tuples detected
  - Add comment about migration timeline

- [ ] **`django/conf/global_settings.py`** (lines 24-26)
  - Update comment to show both formats with deprecation notice
  - Example: "Format: ['email@example.com', ...] or [('Name', 'email@example.com'), ...] (deprecated)"

### Phase 2: Tests and Documentation Updates

- [ ] **Update all test files to new format:**
  - `tests/mail/test_sendtestemail.py` - 2 occurrences
  - `tests/mail/tests.py` - 10+ occurrences
  - `tests/logging_tests/tests.py` - 10+ occurrences
  - `tests/view_tests/tests/test_debug.py` - 3 occurrences
  - `tests/middleware/tests.py` - 1 occurrence

- [ ] **Update documentation:**
  - `docs/ref/settings.txt` - ADMINS description (lines 43-57)
  - `docs/ref/settings.txt` - MANAGERS description (line 2073)
  - `docs/topics/email.txt` - mail_admins/mail_managers docs
  - `docs/howto/error-reporting.txt` - Error reporting guide
  - `docs/ref/logging.txt` - Logging reference
  - Add migration guide: `docs/releases/<VERSION>/deprecations.txt`

### Phase 3: Future Release (2-3 versions later)

- [ ] **`django/core/mail/__init__.py`**
  - Remove tuple support
  - Remove deprecation warning
  - Simplify to: `to=recipients` (all strings now)
  - Keep validation: `isinstance(recipients, list)` and `all(isinstance(a, str) for a in recipients)`

- [ ] **Remove backward compatibility code** from:
  - `django/conf/global_settings.py`
  - Related utility functions

## User Migration Guidance

### Before (Current Format)
```python
ADMINS = [
    ("Admin Name", "admin@example.com"),
    ("Manager Name", "manager@example.com"),
]
```

### After (New Format)
```python
ADMINS = [
    "admin@example.com",
    "manager@example.com",
]
```

### Breaking User Patterns

These patterns will break and need updating:
```python
# Pattern 1: Tuple unpacking
for name, email in settings.ADMINS:  # Will fail
    do_something(name, email)

# Pattern 2: Manual tuple construction
ADMINS = ADMINS + [("New Admin", "newadmin@example.com")]  # Type mismatch

# Pattern 3: Index access
admin_name = settings.ADMINS[0][0]  # Will fail (no name)
admin_email = settings.ADMINS[0]    # Correct for new format
```

## Summary Statistics

- **Files to modify:** 9 Python files + 7 documentation files
- **Test occurrences:** 20+ test decorators/settings
- **Core validation logic:** 1 critical function
- **Backward compatibility:** Required for smooth migration
- **Risk level:** Medium (breaking change, but limited scope)
- **Complexity:** Low (simple format change, centralized validation)
