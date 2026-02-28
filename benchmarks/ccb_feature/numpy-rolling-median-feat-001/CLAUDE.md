# numpy-rolling-median-feat-001: Rolling Median

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
