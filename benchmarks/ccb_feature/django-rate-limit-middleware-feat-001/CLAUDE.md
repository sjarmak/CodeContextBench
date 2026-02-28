# django-rate-limit-middleware-feat-001: RateLimitMiddleware

## Task Type: Feature Implementation (Middleware)

Implement a rate-limiting middleware using Django's cache framework.

## Key Reference Files
- `django/middleware/csrf.py` — middleware pattern
- `django/middleware/common.py` — middleware using settings
- `django/utils/deprecation.py` — MiddlewareMixin base class
- `django/core/cache/__init__.py` — cache API
- `django/http/response.py` — response classes

## Search Strategy
- Search for `MiddlewareMixin` to understand middleware base pattern
- Search for `process_request` in `django/middleware/` for request processing examples
- Search for `HttpResponseForbidden` to find the pattern for HTTP error responses
- Check `django/conf/global_settings.py` for settings pattern
