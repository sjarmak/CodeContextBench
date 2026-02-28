#!/usr/bin/env python3
"""Scaffold 10 new feature tasks for ccb_feature suite."""

import json
import os
import shutil

BENCHMARK_DIR = os.path.join(os.path.dirname(__file__), '..', 'benchmarks', 'ccb_feature')
SGONLY_WRAPPER = os.path.join(os.path.dirname(__file__), 'sgonly_verifier_wrapper.sh')

TASKS = [
    {
        "id": "django-rate-limit-middleware-feat-001",
        "repo": "django/django",
        "mirror": "sg-evals/django--674eda1c",
        "language": "python",
        "category": "feature_implementation",
        "difficulty": "hard",
        "time_limit_sec": 1200,
        "build_timeout_sec": 900,
        "description": "Implement a RateLimitMiddleware in django/middleware/ using the cache framework",
        "instruction": """# Task: Implement RateLimitMiddleware for Django

## Objective
Create a new `RateLimitMiddleware` class in `django/middleware/ratelimit.py` that provides
configurable per-IP request rate limiting using Django's cache framework.

## Requirements

1. **Create `django/middleware/ratelimit.py`** with a `RateLimitMiddleware` class that:
   - Inherits from `MiddlewareMixin` (see `django/utils/deprecation.py`)
   - Reads configuration from `settings.RATE_LIMIT_REQUESTS` (default: 100) and `settings.RATE_LIMIT_WINDOW` (default: 3600 seconds)
   - Uses Django's cache framework (`django.core.cache.cache`) to track request counts per IP
   - Returns `HttpResponseTooManyRequests` (429) when limit is exceeded
   - Implements `process_request(self, request)` following the middleware pattern

2. **Update `django/http/__init__.py`** to export `HttpResponseTooManyRequests` if not already present

3. **Create `tests/middleware/test_ratelimit.py`** with test cases for:
   - Normal requests within limit
   - Requests exceeding limit
   - Cache key isolation per IP
   - Custom settings override

## Key Reference Files
- `django/middleware/csrf.py` — middleware pattern with `process_request`/`process_view`
- `django/middleware/common.py` — middleware using settings and returning responses
- `django/utils/deprecation.py` — `MiddlewareMixin` base class
- `django/core/cache/__init__.py` — cache framework API
- `django/http/response.py` — HTTP response classes (HttpResponseForbidden, etc.)

## Success Criteria
- RateLimitMiddleware class exists and follows Django middleware conventions
- Uses cache framework for rate tracking (not in-memory dict)
- Returns 429 status code when rate limit exceeded
- Has proper imports from django.conf, django.core.cache, django.http
- Test file exists with JUnit-style test methods
""",
        "claude_md": """# django-rate-limit-middleware-feat-001: RateLimitMiddleware

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
""",
        "checks": [
            ("file_exists", "django/middleware/ratelimit.py", "RateLimitMiddleware file exists"),
            ("contains", "django/middleware/ratelimit.py", "class RateLimitMiddleware", "RateLimitMiddleware class defined"),
            ("contains", "django/middleware/ratelimit.py", "process_request", "process_request method present"),
            ("contains", "django/middleware/ratelimit.py", "cache", "Uses cache framework"),
            ("contains", "django/middleware/ratelimit.py", "429\\|HttpResponseTooManyRequests\\|TooManyRequests", "Returns 429 response"),
            ("file_exists", "tests/middleware/test_ratelimit.py", "Test file exists"),
        ],
    },
    {
        "id": "prometheus-silence-bulk-api-feat-001",
        "repo": "prometheus/prometheus",
        "mirror": "sg-evals/prometheus--ba14bc4",
        "language": "go",
        "category": "feature_implementation",
        "difficulty": "hard",
        "time_limit_sec": 1200,
        "build_timeout_sec": 900,
        "description": "Implement a /api/v1/silences/bulk endpoint for batch silence creation in Prometheus",
        "instruction": """# Task: Implement Bulk Silence Creation API for Prometheus

## Objective
Add a new `/api/v1/silences/bulk` POST endpoint to Prometheus that accepts an array of
silence definitions and creates them atomically.

## Requirements

1. **Create handler in `web/api/v1/api.go`** (or a new file `web/api/v1/silences_bulk.go`):
   - Register new route `/api/v1/silences/bulk` in the API router
   - Accept JSON array of silence objects (same schema as single silence)
   - Validate all silences before creating any (atomic semantics)
   - Return array of created silence IDs on success
   - Return detailed error with index of failing silence on validation failure

2. **Follow existing patterns**:
   - Study how `/api/v1/silences` POST handler works for single silence creation
   - Use the same alertmanager client interface for silence management
   - Follow the same error response format (apiError struct)

3. **Create test file** `web/api/v1/silences_bulk_test.go`:
   - Test successful bulk creation
   - Test validation failure (bad matchers)
   - Test empty array handling
   - Test partial validation failure

## Key Reference Files
- `web/api/v1/api.go` — API router registration and handler patterns
- `web/api/v1/api_test.go` — test patterns for API endpoints
- `silence/silence.go` — silence model and validation

## Success Criteria
- Bulk endpoint handler function exists
- Route registered in API router
- Accepts array input and returns array of IDs
- Has proper error handling following Prometheus patterns
- Test file with test functions exists
""",
        "claude_md": """# prometheus-silence-bulk-api-feat-001: Bulk Silence API

## Task Type: Feature Implementation (API Endpoint)

Add a bulk silence creation endpoint following Prometheus API patterns.

## Key Reference Files
- `web/api/v1/api.go` — API router and handler registration
- `web/api/v1/api_test.go` — test patterns
- `silence/silence.go` — silence model

## Search Strategy
- Search for `silences` in `web/api/v1/` to find existing silence handlers
- Search for `router.Post` or `r.Post` to find route registration pattern
- Search for `apiError` to understand error response format
""",
        "checks": [
            ("grep_any", "web/api/v1/", "silences/bulk\\|silencesBulk\\|BulkSilence", "Bulk endpoint handler exists"),
            ("grep_any", "web/api/v1/", "silences/bulk", "Route registered"),
            ("contains_any", "web/api/v1/", "func.*bulk\\|func.*Bulk", "Bulk handler function defined"),
            ("grep_any", "web/api/v1/", "\\[\\].*Silence\\|silences.*\\[\\]", "Accepts array input"),
            ("file_pattern", "web/api/v1/*bulk*test*", "Test file exists"),
            ("grep_any", "web/api/v1/", "func Test.*[Bb]ulk", "Test functions present"),
        ],
    },
    {
        "id": "cilium-policy-audit-logger-feat-001",
        "repo": "cilium/cilium",
        "mirror": "sg-evals/cilium--v1.16.5",
        "language": "go",
        "category": "feature_implementation",
        "difficulty": "hard",
        "time_limit_sec": 1200,
        "build_timeout_sec": 900,
        "description": "Implement a PolicyAuditLogger in cilium's pkg/policy/ for structured policy decision logging",
        "instruction": """# Task: Implement PolicyAuditLogger for Cilium

## Objective
Create a `PolicyAuditLogger` in `pkg/policy/` that provides structured logging of policy
evaluation decisions for audit and debugging purposes.

## Requirements

1. **Create `pkg/policy/audit_logger.go`** with:
   - `PolicyAuditLogger` struct with configurable log level and output
   - `LogDecision(identity, policy, verdict, reason)` method
   - `LogEvaluation(ctx, policyKey, selectorCache, result)` method
   - Integration with Cilium's existing logging framework (logrus/scopedLog)
   - Support for JSON-structured audit log output

2. **Create `pkg/policy/audit_logger_test.go`** with tests

3. **Follow Cilium patterns**:
   - Use `logfields` package for structured log fields
   - Follow the `SelectorCache` interaction pattern
   - Use `lock.Mutex` from `pkg/lock/` for thread safety

## Key Reference Files
- `pkg/policy/distillery.go` — policy decision evaluation
- `pkg/policy/selectorcache.go` — SelectorCache for identity matching
- `pkg/policy/types.go` — policy types and interfaces
- `pkg/logging/logfields/logfields.go` — structured log field constants
- `pkg/lock/lock.go` — Cilium's lock primitives

## Success Criteria
- PolicyAuditLogger struct and methods exist
- Uses Cilium's logging framework (logrus/scopedLog)
- Has LogDecision method with policy verdict logging
- Thread-safe implementation
- Test file exists with test functions
""",
        "claude_md": """# cilium-policy-audit-logger-feat-001: Policy Audit Logger

## Task Type: Feature Implementation (Logging Infrastructure)

Implement structured audit logging for policy decisions in Cilium.

## Key Reference Files
- `pkg/policy/distillery.go` — policy evaluation
- `pkg/policy/selectorcache.go` — SelectorCache
- `pkg/logging/logfields/logfields.go` — log field constants
- `pkg/lock/lock.go` — lock primitives

## Search Strategy
- Search for `scopedLog` in `pkg/policy/` for logging patterns
- Search for `logfields` for structured field conventions
- Search for `lock.Mutex` for thread-safety patterns
""",
        "checks": [
            ("file_exists", "pkg/policy/audit_logger.go", "Audit logger file exists"),
            ("contains", "pkg/policy/audit_logger.go", "PolicyAuditLogger", "PolicyAuditLogger struct defined"),
            ("contains", "pkg/policy/audit_logger.go", "LogDecision\\|logDecision", "LogDecision method present"),
            ("contains", "pkg/policy/audit_logger.go", "logrus\\|scopedLog\\|log\\.", "Uses logging framework"),
            ("file_exists", "pkg/policy/audit_logger_test.go", "Test file exists"),
            ("contains", "pkg/policy/audit_logger_test.go", "func Test", "Test functions present"),
        ],
    },
    {
        "id": "terraform-compact-diff-fmt-feat-001",
        "repo": "hashicorp/terraform",
        "mirror": "sg-evals/terraform--v1.10.3",
        "language": "go",
        "category": "feature_implementation",
        "difficulty": "hard",
        "time_limit_sec": 1200,
        "build_timeout_sec": 900,
        "description": "Implement a CompactDiffFormatter in Terraform for condensed plan output",
        "instruction": """# Task: Implement CompactDiffFormatter for Terraform

## Objective
Create a `CompactDiffFormatter` in `internal/command/format/` that produces a condensed,
summary-style diff output for `terraform plan`, showing only resource-level changes
without attribute-level detail.

## Requirements

1. **Create `internal/command/format/compact.go`** with:
   - `CompactDiffFormatter` struct implementing a plan formatter
   - `Format(plan *plans.Plan, schemas *terraform.Schemas)` method returning string
   - Outputs one line per resource change: `[action] resource_type.name`
   - Groups changes by action type (create/update/delete/replace)
   - Shows summary counts at the end

2. **Create `internal/command/format/compact_test.go`** with tests

3. **Follow Terraform patterns**:
   - Study the existing `DiffFormatter` in the format package
   - Use `plans.Action` constants (Create, Update, Delete, etc.)
   - Use `addrs.AbsResourceInstance` for resource addressing

## Key Reference Files
- `internal/command/format/diff.go` — existing diff formatter
- `internal/command/format/state.go` — state formatter pattern
- `internal/plans/changes.go` — plan change types
- `internal/plans/plan.go` — Plan struct definition
- `internal/addrs/resource.go` — resource addressing

## Success Criteria
- CompactDiffFormatter struct exists in format package
- Format method accepts plan and schemas parameters
- Outputs resource-level change summary
- Groups by action type
- Test file exists
""",
        "claude_md": """# terraform-compact-diff-fmt-feat-001: Compact Diff Formatter

## Task Type: Feature Implementation (Output Formatting)

Implement a condensed plan diff formatter for Terraform.

## Key Reference Files
- `internal/command/format/diff.go` — existing formatter
- `internal/plans/changes.go` — change types
- `internal/plans/plan.go` — Plan struct
- `internal/addrs/resource.go` — resource addressing

## Search Strategy
- Search for `DiffFormatter` in `internal/command/format/`
- Search for `plans.Action` for action type constants
- Search for `AbsResourceInstance` for addressing pattern
""",
        "checks": [
            ("file_exists", "internal/command/format/compact.go", "Compact formatter file exists"),
            ("contains", "internal/command/format/compact.go", "CompactDiffFormatter", "CompactDiffFormatter defined"),
            ("contains", "internal/command/format/compact.go", "func.*Format\\|func.*format", "Format method present"),
            ("contains", "internal/command/format/compact.go", "plans\\.", "Uses plans package"),
            ("file_exists", "internal/command/format/compact_test.go", "Test file exists"),
            ("contains", "internal/command/format/compact_test.go", "func Test", "Test functions present"),
        ],
    },
    {
        "id": "numpy-rolling-median-feat-001",
        "repo": "numpy/numpy",
        "mirror": "sg-evals/numpy--v2.2.2",
        "language": "python",
        "category": "feature_implementation",
        "difficulty": "expert",
        "time_limit_sec": 1200,
        "build_timeout_sec": 900,
        "description": "Implement a rolling_median function in numpy/lib/ with proper array dispatch",
        "instruction": """# Task: Implement rolling_median for NumPy

## Objective
Add a `rolling_median` function to `numpy/lib/` that computes a rolling (sliding window)
median over a 1-D array, following NumPy's function dispatch and documentation conventions.

## Requirements

1. **Create `numpy/lib/_rolling_median.py`** (or add to existing stats module):
   - `rolling_median(a, window_size, *, axis=-1, mode='valid')` function
   - Supports 'valid', 'same', and 'full' modes (similar to np.convolve)
   - Handles edge cases: window_size > array length, window_size = 1
   - Uses `@array_function_dispatch` decorator for subclass support
   - Includes NumPy-style docstring with Parameters, Returns, Examples sections

2. **Register in module exports**:
   - Add to `numpy/lib/__init__.py` or appropriate submodule

3. **Create test file** `numpy/lib/tests/test_rolling_median.py`:
   - Test basic rolling median computation
   - Test different modes
   - Test edge cases

## Key Reference Files
- `numpy/lib/_function_base_impl.py` — array function implementations (median, average)
- `numpy/core/overrides.py` — `array_function_dispatch` decorator
- `numpy/lib/_nanfunctions_impl.py` — NaN-aware function patterns
- `numpy/lib/tests/test_function_base.py` — test patterns

## Success Criteria
- rolling_median function exists with proper signature
- Uses array_function_dispatch decorator
- Has NumPy-style docstring
- Handles window_size parameter
- Test file with test functions exists
""",
        "claude_md": """# numpy-rolling-median-feat-001: Rolling Median

## Task Type: Feature Implementation (Array Function)

Implement a rolling median with proper NumPy dispatch conventions.

## Key Reference Files
- `numpy/lib/_function_base_impl.py` — function implementations
- `numpy/core/overrides.py` — array_function_dispatch
- `numpy/lib/tests/test_function_base.py` — test patterns

## Search Strategy
- Search for `array_function_dispatch` to understand dispatch decorator usage
- Search for `def median` to find median implementation pattern
- Search for `sliding_window_view` as a potential building block
""",
        "checks": [
            ("grep_recursive", "numpy/lib/", "rolling_median", "rolling_median function exists"),
            ("grep_recursive", "numpy/lib/", "def rolling_median", "Function definition present"),
            ("grep_recursive", "numpy/lib/", "window_size\\|window", "Accepts window parameter"),
            ("grep_recursive", "numpy/lib/", "array_function_dispatch\\|dispatch", "Uses dispatch decorator"),
            ("file_pattern", "numpy/lib/tests/*rolling*", "Test file exists"),
            ("grep_recursive", "numpy/lib/tests/", "rolling_median\\|test_rolling", "Tests reference rolling_median"),
        ],
    },
    {
        "id": "envoy-custom-header-filter-feat-001",
        "repo": "envoyproxy/envoy",
        "mirror": "sg-evals/envoy--v1.33.0",
        "language": "cpp",
        "category": "feature_implementation",
        "difficulty": "expert",
        "time_limit_sec": 1800,
        "build_timeout_sec": 1200,
        "description": "Implement a custom_header_injection HTTP filter for Envoy",
        "instruction": """# Task: Implement Custom Header Injection Filter for Envoy

## Objective
Create a new HTTP filter `envoy.filters.http.custom_header_injection` that injects
configurable headers into requests and/or responses based on route metadata.

## Requirements

1. **Create filter source files**:
   - `source/extensions/filters/http/custom_header_injection/filter.h` — filter class declaration
   - `source/extensions/filters/http/custom_header_injection/filter.cc` — filter implementation
   - `source/extensions/filters/http/custom_header_injection/config.h` — factory declaration
   - `source/extensions/filters/http/custom_header_injection/config.cc` — factory registration

2. **Filter behavior**:
   - Implements `Http::StreamDecoderFilter` (request path) and `Http::StreamEncoderFilter` (response path)
   - Reads header injection rules from filter config
   - Supports both request and response header injection
   - Follows Envoy's filter lifecycle (decodeHeaders, encodeHeaders)

3. **Create test file**:
   - `test/extensions/filters/http/custom_header_injection/filter_test.cc`

## Key Reference Files
- `source/extensions/filters/http/header_to_metadata/filter.h` — simple header filter pattern
- `source/extensions/filters/http/header_to_metadata/filter.cc` — implementation pattern
- `source/extensions/filters/http/header_to_metadata/config.cc` — factory registration
- `source/extensions/filters/http/common/factory_base.h` — factory base class

## Success Criteria
- Filter header file declares class inheriting from StreamDecoderFilter/StreamEncoderFilter
- Filter implementation has decodeHeaders/encodeHeaders methods
- Factory config file registers the filter
- Follows Envoy naming: envoy.filters.http.custom_header_injection
- Test file exists
""",
        "claude_md": """# envoy-custom-header-filter-feat-001: Custom Header Injection Filter

## Task Type: Feature Implementation (HTTP Filter)

Implement an Envoy HTTP filter following extension patterns.

## Key Reference Files
- `source/extensions/filters/http/header_to_metadata/` — reference filter
- `source/extensions/filters/http/common/factory_base.h` — factory base
- `source/common/http/filter_manager.h` — filter interfaces

## Search Strategy
- Search for `StreamDecoderFilter` to find filter interface pattern
- Search for `header_to_metadata` as closest reference implementation
- Search for `RegisterFactory` for factory registration pattern
""",
        "checks": [
            ("file_pattern", "source/extensions/filters/http/custom_header_injection/*.h", "Filter header exists"),
            ("file_pattern", "source/extensions/filters/http/custom_header_injection/*.cc", "Filter implementation exists"),
            ("grep_recursive", "source/extensions/filters/http/custom_header_injection/", "decodeHeaders\\|encodeHeaders", "Filter methods present"),
            ("grep_recursive", "source/extensions/filters/http/custom_header_injection/", "StreamDecoderFilter\\|StreamEncoderFilter", "Inherits filter interfaces"),
            ("grep_recursive", "source/extensions/filters/http/custom_header_injection/", "custom_header_injection", "Filter name registered"),
            ("file_pattern", "test/extensions/filters/http/custom_header_injection/*test*", "Test file exists"),
        ],
    },
    {
        "id": "pytorch-gradient-noise-feat-001",
        "repo": "pytorch/pytorch",
        "mirror": "sg-evals/pytorch--d18007a1",
        "language": "python",
        "category": "feature_implementation",
        "difficulty": "hard",
        "time_limit_sec": 1200,
        "build_timeout_sec": 900,
        "description": "Implement a GradientNoiseInjector optimizer wrapper in torch/optim/",
        "instruction": """# Task: Implement GradientNoiseInjector for PyTorch

## Objective
Create a `GradientNoiseInjector` optimizer wrapper in `torch/optim/` that adds calibrated
Gaussian noise to gradients before the optimizer step, implementing the "Adding Gradient
Noise Improves Learning for Very Deep Networks" technique.

## Requirements

1. **Create `torch/optim/gradient_noise.py`** with:
   - `GradientNoiseInjector` class wrapping any base optimizer
   - `__init__(self, optimizer, eta=0.01, gamma=0.55)` — noise schedule parameters
   - `step(self, closure=None)` — injects noise then delegates to base optimizer
   - Noise variance schedule: `sigma^2 = eta / (1 + t)^gamma` where t is step count
   - Uses `torch.randn_like` for Gaussian noise generation

2. **Register in module**:
   - Add to `torch/optim/__init__.py` exports

3. **Create test file** `test/optim/test_gradient_noise.py`:
   - Test noise injection occurs
   - Test variance decay schedule
   - Test wrapping different optimizers (SGD, Adam)

## Key Reference Files
- `torch/optim/optimizer.py` — Optimizer base class
- `torch/optim/sgd.py` — simple optimizer implementation
- `torch/optim/lr_scheduler.py` — wrapper pattern with step counting
- `torch/optim/swa_utils.py` — optimizer wrapper pattern (AveragedModel)

## Success Criteria
- GradientNoiseInjector class exists in torch/optim/
- Wraps a base optimizer (composition pattern)
- Implements step() with noise injection
- Has eta and gamma parameters for noise schedule
- Test file exists
""",
        "claude_md": """# pytorch-gradient-noise-feat-001: Gradient Noise Injector

## Task Type: Feature Implementation (Optimizer Wrapper)

Implement a gradient noise injection wrapper for PyTorch optimizers.

## Key Reference Files
- `torch/optim/optimizer.py` — Optimizer base class
- `torch/optim/sgd.py` — simple optimizer
- `torch/optim/lr_scheduler.py` — wrapper with step counting
- `torch/optim/swa_utils.py` — optimizer wrapper pattern

## Search Strategy
- Search for `class Optimizer` in `torch/optim/optimizer.py`
- Search for `param_groups` to understand parameter group access
- Search for `torch.randn_like` for noise generation pattern
""",
        "checks": [
            ("grep_recursive", "torch/optim/", "GradientNoiseInjector", "GradientNoiseInjector exists"),
            ("grep_recursive", "torch/optim/", "class GradientNoiseInjector", "Class defined"),
            ("grep_recursive", "torch/optim/", "def step", "step method present"),
            ("grep_recursive", "torch/optim/", "eta\\|gamma\\|noise", "Noise parameters present"),
            ("grep_recursive", "torch/optim/", "randn_like\\|normal_\\|noise", "Noise generation"),
            ("file_pattern", "test/optim/*gradient_noise*\\|test/optim/*noise*", "Test file exists"),
        ],
    },
    {
        "id": "pandas-merge-asof-indicator-feat-001",
        "repo": "pandas-dev/pandas",
        "mirror": "sg-evals/pandas--v2.2.3",
        "language": "python",
        "category": "feature_implementation",
        "difficulty": "hard",
        "time_limit_sec": 1200,
        "build_timeout_sec": 900,
        "description": "Add indicator parameter to merge_asof() in pandas",
        "instruction": """# Task: Add indicator Parameter to merge_asof()

## Objective
Add an `indicator` parameter to `pandas.merge_asof()` that creates a column indicating
the merge result, similar to how `pd.merge()` supports `indicator=True`.

## Requirements

1. **Modify `pandas/core/reshape/merge.py`**:
   - Add `indicator` parameter to `merge_asof()` function signature
   - Pass `indicator` through to `_AsOfMerge` class
   - In `_AsOfMerge.__init__()`, store indicator setting
   - After merge, add indicator column showing 'both', 'left_only', or 'right_only'

2. **Update `_AsOfMerge` class**:
   - Accept `indicator` in constructor
   - Implement indicator column generation in `get_result()` or post-processing

3. **Create test additions** in `pandas/tests/reshape/merge/test_merge_asof.py`:
   - Test indicator=True produces _merge column
   - Test indicator with custom name
   - Test indicator values are correct

## Key Reference Files
- `pandas/core/reshape/merge.py` — merge_asof and _AsOfMerge class
- `pandas/core/reshape/merge.py` — _MergeOperation.get_result() for indicator pattern
- `pandas/tests/reshape/merge/test_merge_asof.py` — existing asof merge tests

## Success Criteria
- merge_asof function accepts indicator parameter
- _AsOfMerge class handles indicator
- Indicator column added to result when requested
- Follows existing indicator pattern from pd.merge()
- Test additions present
""",
        "claude_md": """# pandas-merge-asof-indicator-feat-001: merge_asof indicator

## Task Type: Feature Implementation (API Extension)

Add indicator support to merge_asof following existing merge patterns.

## Key Reference Files
- `pandas/core/reshape/merge.py` — merge_asof, _AsOfMerge, _MergeOperation
- `pandas/tests/reshape/merge/test_merge_asof.py` — existing tests

## Search Strategy
- Search for `def merge_asof` to find function signature
- Search for `class _AsOfMerge` to find class definition
- Search for `indicator` in merge.py to see how pd.merge handles it
""",
        "checks": [
            ("contains", "pandas/core/reshape/merge.py", "indicator.*merge_asof\\|merge_asof.*indicator", "merge_asof accepts indicator"),
            ("contains", "pandas/core/reshape/merge.py", "_AsOfMerge.*indicator\\|indicator.*_AsOfMerge", "AsOfMerge handles indicator"),
            ("grep_recursive", "pandas/core/reshape/", "indicator.*column\\|_merge.*indicator", "Indicator column logic"),
            ("grep_recursive", "pandas/core/reshape/", "both.*left_only\\|left_only.*right_only", "Indicator values"),
            ("grep_recursive", "pandas/tests/reshape/merge/", "indicator.*asof\\|asof.*indicator\\|test.*indicator", "Tests for indicator"),
            ("grep_recursive", "pandas/tests/reshape/merge/", "_merge\\|indicator", "Test checks indicator column"),
        ],
    },
    {
        "id": "istio-retry-budget-feat-001",
        "repo": "istio/istio",
        "mirror": "sg-evals/istio--f8af3cae",
        "language": "go",
        "category": "feature_implementation",
        "difficulty": "expert",
        "time_limit_sec": 1200,
        "build_timeout_sec": 900,
        "description": "Implement a retry budget controller in Istio's pilot for service-level retry limiting",
        "instruction": """# Task: Implement Retry Budget Controller for Istio

## Objective
Create a retry budget controller in `pilot/pkg/networking/` that enforces service-level
retry budgets, preventing retry storms by limiting the total retry rate as a percentage
of active requests.

## Requirements

1. **Create `pilot/pkg/networking/retrybudget/budget.go`** with:
   - `RetryBudget` struct with `budgetPercent`, `minRetriesPerSecond`, `activeRequests` fields
   - `NewRetryBudget(budgetPercent float64, minRetries int)` constructor
   - `ShouldRetry() bool` — checks if retry is within budget
   - `RecordRequest()` / `RecordRequestComplete()` — tracks active requests
   - `RecordRetry()` — tracks retry usage
   - Thread-safe using `sync.Mutex` or `atomic` operations

2. **Create `pilot/pkg/networking/retrybudget/budget_test.go`**

3. **Wire into route configuration**:
   - Study how VirtualService retry policy is translated to Envoy route config
   - Add budget integration point (can be a stub/interface)

## Key Reference Files
- `pilot/pkg/networking/core/route/retry.go` — retry policy translation
- `pilot/pkg/networking/core/route/route.go` — route configuration builder
- `pilot/pkg/model/service.go` — service model
- `pilot/pkg/networking/core/` — xDS generation

## Success Criteria
- RetryBudget struct with budget tracking exists
- ShouldRetry method implements budget check
- Request tracking methods exist
- Thread-safe implementation
- Test file exists
""",
        "claude_md": """# istio-retry-budget-feat-001: Retry Budget Controller

## Task Type: Feature Implementation (Networking Control)

Implement retry budget enforcement in Istio's pilot networking layer.

## Key Reference Files
- `pilot/pkg/networking/core/route/retry.go` — retry policy
- `pilot/pkg/networking/core/route/route.go` — route builder
- `pilot/pkg/model/service.go` — service model

## Search Strategy
- Search for `RetryPolicy` in `pilot/pkg/networking/` for retry handling
- Search for `retryOn` to find Envoy retry configuration translation
- Search for `sync.Mutex` in `pilot/pkg/` for thread-safety patterns
""",
        "checks": [
            ("file_exists", "pilot/pkg/networking/retrybudget/budget.go", "Budget file exists"),
            ("contains", "pilot/pkg/networking/retrybudget/budget.go", "RetryBudget", "RetryBudget struct defined"),
            ("contains", "pilot/pkg/networking/retrybudget/budget.go", "ShouldRetry", "ShouldRetry method present"),
            ("contains", "pilot/pkg/networking/retrybudget/budget.go", "RecordRequest\\|activeRequests\\|atomic", "Request tracking present"),
            ("file_exists", "pilot/pkg/networking/retrybudget/budget_test.go", "Test file exists"),
            ("contains", "pilot/pkg/networking/retrybudget/budget_test.go", "func Test", "Test functions present"),
        ],
    },
    {
        "id": "linux-procfs-cgroup-pressure-feat-001",
        "repo": "torvalds/linux",
        "mirror": "sg-evals/linux--55b2af1c",
        "language": "c",
        "category": "feature_implementation",
        "difficulty": "expert",
        "time_limit_sec": 1800,
        "build_timeout_sec": 1200,
        "description": "Implement a /proc/cgroups/memory_pressure interface in the Linux kernel",
        "instruction": """# Task: Implement /proc/cgroups/memory_pressure Interface

## Objective
Create a `/proc/cgroups/memory_pressure` proc file that exposes aggregated memory pressure
statistics across all cgroup v2 memory controllers, using the seq_file interface.

## Requirements

1. **Create or modify files in `mm/` or `kernel/cgroup/`**:
   - Register new proc entry for `/proc/cgroups/memory_pressure`
   - Use `seq_file` interface (`seq_open`, `seq_read`, `seq_printf`)
   - Iterate over cgroup hierarchy to collect memory pressure data
   - Output format: one line per cgroup with path and pressure stats

2. **Implementation details**:
   - Use `proc_create()` or `proc_create_seq_private()` for registration
   - Read from `memory.pressure` PSI data for each cgroup
   - Follow existing `/proc/cgroups` pattern for output formatting
   - Include `some`, `full` pressure levels

3. **Create header declarations if needed**

## Key Reference Files
- `kernel/cgroup/cgroup.c` — cgroup v2 core, /proc/cgroups handler
- `mm/memcontrol.c` — cgroup memory controller
- `kernel/sched/psi.c` — Pressure Stall Information (PSI) framework
- `fs/proc/root.c` — proc filesystem registration
- `include/linux/seq_file.h` — seq_file API

## Success Criteria
- Proc file registration code exists
- Uses seq_file interface (seq_printf, seq_open)
- References cgroup memory controller data
- Reads PSI/pressure information
- Includes both 'some' and 'full' pressure levels
- Has proper #include directives for kernel headers
""",
        "claude_md": """# linux-procfs-cgroup-pressure-feat-001: /proc/cgroups/memory_pressure

## Task Type: Feature Implementation (Kernel Interface)

Implement a proc filesystem entry for aggregated cgroup memory pressure.

## Key Reference Files
- `kernel/cgroup/cgroup.c` — /proc/cgroups handler
- `mm/memcontrol.c` — memory controller
- `kernel/sched/psi.c` — PSI framework
- `fs/proc/root.c` — proc registration

## Search Strategy
- Search for `proc_create` in `kernel/cgroup/` for proc registration
- Search for `seq_printf` in `kernel/cgroup/` for seq_file usage
- Search for `memory.pressure` or `psi_` for pressure data access
""",
        "checks": [
            ("grep_recursive", "kernel/cgroup/\\|mm/\\|fs/proc/", "memory_pressure", "memory_pressure reference exists"),
            ("grep_recursive", "kernel/cgroup/\\|mm/\\|fs/proc/", "proc_create\\|proc_register", "Proc file registration"),
            ("grep_recursive", "kernel/cgroup/\\|mm/\\|fs/proc/", "seq_printf\\|seq_open\\|seq_file", "Uses seq_file interface"),
            ("grep_recursive", "kernel/cgroup/\\|mm/\\|fs/proc/", "memcg\\|mem_cgroup\\|memory.*controller", "References memory controller"),
            ("grep_recursive", "kernel/cgroup/\\|mm/\\|fs/proc/", "psi\\|pressure", "References PSI/pressure data"),
            ("grep_recursive", "kernel/cgroup/\\|mm/\\|fs/proc/", "some\\|full", "Includes pressure levels"),
        ],
    },
]


def generate_test_sh(task):
    """Generate test.sh for a feature task."""
    checks = task["checks"]
    total = len(checks)

    lines = [
        '#!/bin/bash',
        'set -euo pipefail',
        '',
        '[ -f /tmp/.sg_only_mode ] && [ -f /tests/sgonly_verifier_wrapper.sh ] && source /tests/sgonly_verifier_wrapper.sh',
        '',
        'SCORE=0',
        f'TOTAL={total}',
        'WORKSPACE="${VERIFY_REPO:-/workspace}"',
        '',
    ]

    for i, (check_type, *args) in enumerate(checks, 1):
        description = args[-1]  # Last arg is always description
        lines.append(f'# Check {i}: {description}')

        if check_type == "file_exists":
            path = args[0]
            lines.append(f'if [ -f "$WORKSPACE/{path}" ]; then')
            lines.append(f'    SCORE=$((SCORE + 1))')
            lines.append(f'    echo "PASS: {description}"')
            lines.append(f'else')
            lines.append(f'    echo "FAIL: {description}"')
            lines.append(f'fi')

        elif check_type == "contains":
            path, pattern = args[0], args[1]
            lines.append(f'if grep -q \'{pattern}\' "$WORKSPACE/{path}" 2>/dev/null; then')
            lines.append(f'    SCORE=$((SCORE + 1))')
            lines.append(f'    echo "PASS: {description}"')
            lines.append(f'else')
            lines.append(f'    echo "FAIL: {description}"')
            lines.append(f'fi')

        elif check_type == "grep_recursive":
            path, pattern = args[0], args[1]
            lines.append(f'if grep -rq \'{pattern}\' "$WORKSPACE/{path}" 2>/dev/null; then')
            lines.append(f'    SCORE=$((SCORE + 1))')
            lines.append(f'    echo "PASS: {description}"')
            lines.append(f'else')
            lines.append(f'    echo "FAIL: {description}"')
            lines.append(f'fi')

        elif check_type == "grep_any":
            path, pattern = args[0], args[1]
            lines.append(f'if grep -rq \'{pattern}\' "$WORKSPACE/{path}" 2>/dev/null; then')
            lines.append(f'    SCORE=$((SCORE + 1))')
            lines.append(f'    echo "PASS: {description}"')
            lines.append(f'else')
            lines.append(f'    echo "FAIL: {description}"')
            lines.append(f'fi')

        elif check_type == "contains_any":
            path, pattern = args[0], args[1]
            lines.append(f'if grep -rqE \'{pattern}\' "$WORKSPACE/{path}" 2>/dev/null; then')
            lines.append(f'    SCORE=$((SCORE + 1))')
            lines.append(f'    echo "PASS: {description}"')
            lines.append(f'else')
            lines.append(f'    echo "FAIL: {description}"')
            lines.append(f'fi')

        elif check_type == "file_pattern":
            pattern = args[0]
            # Use shell glob
            lines.append(f'if ls $WORKSPACE/{pattern} 1>/dev/null 2>&1; then')
            lines.append(f'    SCORE=$((SCORE + 1))')
            lines.append(f'    echo "PASS: {description}"')
            lines.append(f'else')
            lines.append(f'    echo "FAIL: {description}"')
            lines.append(f'fi')

        lines.append('')

    lines.extend([
        'echo ""',
        'echo "Score: $SCORE / $TOTAL"',
        '',
        'mkdir -p /logs/verifier',
        'python3 -c "print($SCORE / $TOTAL)" > /logs/verifier/reward.txt',
    ])

    return '\n'.join(lines) + '\n'


def generate_task_toml(task):
    """Generate task.toml for a feature task."""
    return f'''version = "1.0"

[metadata]
name = "{task['id']}"
description = "{task['description']}"
license = "Apache-2.0"
author_name = "CodeContextBench"
author_email = "ccb@example.com"

[task]
id = "{task['id']}"
repo = "{task['repo']}"
category = "{task['category']}"
language = "{task['language']}"
difficulty = "{task['difficulty']}"
time_limit_sec = {task['time_limit_sec']}

[verification]
type = "test"
command = "bash /tests/test.sh"
reward_type = "checklist"
description = "Checks feature implementation: file existence, class/function definitions, pattern usage, tests"

[environment]
build_timeout_sec = {task['build_timeout_sec']}.0
cpus = 4
memory = "8G"
storage = "20G"

[environment.setup_scripts]
mcp_config = \'\'\'
#!/bin/bash
echo "Sourcegraph MCP available for code search"
\'\'\'
'''


def generate_dockerfile(task):
    """Generate baseline Dockerfile that clones from the mirror."""
    mirror = task['mirror']
    # Extract just the mirror name for git clone URL
    return f'''FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \\
    git ca-certificates python3 curl \\
    && rm -rf /var/lib/apt/lists/*

# Pre-create claude user
RUN (adduser --disabled-password --gecos '' claude 2>/dev/null || true)

# Clone repo as claude user
USER claude
WORKDIR /workspace
RUN git clone --depth 1 https://github.com/{task['repo']}.git . || \\
    (git init && git config user.email "agent@example.com" && git config user.name "Agent")
USER root

RUN mkdir -p /logs/agent /logs/verifier && \\
    chown -R claude:claude /logs

ENTRYPOINT []
'''


def generate_dockerfile_sg_only(task):
    """Generate Dockerfile.sg_only for MCP-only mode."""
    return f'''FROM ubuntu:22.04

ENV SOURCEGRAPH_REPO_NAME={task['mirror']}
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \\
    git ca-certificates python3 curl \\
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

RUN git init && \\
    git config user.email "agent@example.com" && \\
    git config user.name "Agent"

RUN mkdir -p /logs/agent /logs/verifier

RUN touch /tmp/.sg_only_mode

RUN (adduser --disabled-password --gecos '' claude 2>/dev/null || true) && \\
    for d in /workspace /logs; do [ -d "$d" ] && chown -R claude:claude "$d"; done || true

ENTRYPOINT []
'''


def generate_ground_truth(task):
    """Generate ground_truth.json for a feature task."""
    gt = {
        "task_id": task["id"],
        "expected_files": [],
        "expected_keywords": [],
    }

    for check_type, *args in task["checks"]:
        if check_type == "file_exists":
            gt["expected_files"].append(args[0])
        elif check_type in ("contains", "grep_recursive", "grep_any", "contains_any"):
            pattern = args[1]
            # Strip regex characters for keyword
            keyword = pattern.replace('\\|', '|').split('|')[0].replace('\\', '')
            gt["expected_keywords"].append(keyword)

    return json.dumps(gt, indent=2) + '\n'


def main():
    for task in TASKS:
        task_dir = os.path.join(BENCHMARK_DIR, task['id'])
        env_dir = os.path.join(task_dir, 'environment')
        tests_dir = os.path.join(task_dir, 'tests')

        os.makedirs(env_dir, exist_ok=True)
        os.makedirs(tests_dir, exist_ok=True)

        # task.toml
        with open(os.path.join(task_dir, 'task.toml'), 'w') as f:
            f.write(generate_task_toml(task))

        # instruction.md
        with open(os.path.join(task_dir, 'instruction.md'), 'w') as f:
            f.write(task['instruction'].strip() + '\n')

        # CLAUDE.md
        with open(os.path.join(task_dir, 'CLAUDE.md'), 'w') as f:
            f.write(task['claude_md'].strip() + '\n')

        # environment/Dockerfile
        with open(os.path.join(env_dir, 'Dockerfile'), 'w') as f:
            f.write(generate_dockerfile(task))

        # environment/Dockerfile.sg_only
        with open(os.path.join(env_dir, 'Dockerfile.sg_only'), 'w') as f:
            f.write(generate_dockerfile_sg_only(task))

        # tests/test.sh
        test_sh_path = os.path.join(tests_dir, 'test.sh')
        with open(test_sh_path, 'w') as f:
            f.write(generate_test_sh(task))
        os.chmod(test_sh_path, 0o755)

        # tests/ground_truth.json
        with open(os.path.join(tests_dir, 'ground_truth.json'), 'w') as f:
            f.write(generate_ground_truth(task))

        # tests/sgonly_verifier_wrapper.sh — copy from scripts/
        if os.path.exists(SGONLY_WRAPPER):
            shutil.copy2(SGONLY_WRAPPER, os.path.join(tests_dir, 'sgonly_verifier_wrapper.sh'))

        print(f"  Scaffolded: {task['id']}")

    print(f"\nTotal: {len(TASKS)} feature tasks scaffolded in {BENCHMARK_DIR}")


if __name__ == '__main__':
    main()
