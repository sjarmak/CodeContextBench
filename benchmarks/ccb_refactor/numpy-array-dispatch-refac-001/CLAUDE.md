# numpy-array-dispatch-refac-001: Rename dispatch decorator

## Task Type: Cross-File Refactoring (Rename)

Rename array_function_dispatch → dispatch_array_function across NumPy.

## Key Reference Files
- `numpy/_core/overrides.py` — definition
- `numpy/lib/` — heavy decorator usage
- `numpy/ma/core.py` — masked array usage

## Search Strategy
- Search for `array_function_dispatch` for all references
- Search for `def array_function_dispatch` for the definition
- Search in `numpy/_core/` and `numpy/core/` (both paths may exist)
