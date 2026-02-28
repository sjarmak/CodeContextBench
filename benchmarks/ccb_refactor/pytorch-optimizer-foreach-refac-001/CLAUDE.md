# pytorch-optimizer-foreach-refac-001: Extract foreach step

## Task Type: Cross-File Refactoring (Extract)

Extract shared foreach optimization into torch/optim/_foreach.py.

## Key Reference Files
- `torch/optim/sgd.py` — _multi_tensor_sgd
- `torch/optim/adam.py` — _multi_tensor_adam
- `torch/optim/_functional.py` — functional implementations

## Search Strategy
- Search for `_multi_tensor_` in `torch/optim/` for pattern locations
- Search for `_foreach_` for existing foreach usage
