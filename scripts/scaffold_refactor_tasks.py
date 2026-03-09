#!/usr/bin/env python3
"""Scaffold 13 new refactor tasks for csb_sdlc_refactor suite."""

import json
import os
import shutil

BENCHMARK_DIR = os.path.join(os.path.dirname(__file__), '..', 'benchmarks', 'csb_sdlc_refactor')
SGONLY_WRAPPER = os.path.join(os.path.dirname(__file__), 'sgonly_verifier_wrapper.sh')

TASKS = [
    {
        "id": "django-request-factory-refac-001",
        "repo": "django/django",
        "mirror": "sg-evals/django--674eda1c",
        "language": "python",
        "category": "cross_file_refactoring",
        "difficulty": "hard",
        "time_limit_sec": 1200,
        "build_timeout_sec": 900,
        "description": "Rename RequestFactory to TestRequestBuilder across Django test utilities",
        "old_symbol": "RequestFactory",
        "new_symbol": "TestRequestBuilder",
        "search_dirs": ["django/test/", "tests/"],
        "expected_refs": 25,
        "instruction": """# Task: Rename RequestFactory to TestRequestBuilder

## Objective
Rename the `RequestFactory` class to `TestRequestBuilder` across the Django codebase
to better reflect its purpose as a test utility that builds HTTP request objects.

## Requirements

1. **Rename the class definition** in `django/test/client.py`:
   - `class RequestFactory` → `class TestRequestBuilder`
   - Keep all methods and behavior unchanged

2. **Update all references** across the codebase:
   - Import statements: `from django.test import RequestFactory` → `TestRequestBuilder`
   - Type annotations and docstrings
   - Test files that instantiate RequestFactory
   - Expected: 25+ call sites across django/test/ and tests/

3. **Maintain backward compatibility** (optional alias):
   - Add `RequestFactory = TestRequestBuilder` alias for deprecation

## Key Reference Files
- `django/test/client.py` — class definition
- `django/test/__init__.py` — module exports
- `tests/requests/test_data_upload_settings.py` — usage example
- `tests/test_client/tests.py` — heavy usage

## Success Criteria
- Old symbol `RequestFactory` removed from class definition
- New symbol `TestRequestBuilder` used as class name
- References updated across 80%+ of call sites
- No `class RequestFactory` definition remains (alias is OK)
""",
        "claude_md": """# django-request-factory-refac-001: Rename RequestFactory

## Task Type: Cross-File Refactoring (Rename)

Rename RequestFactory → TestRequestBuilder across Django.

## Key Reference Files
- `django/test/client.py` — class definition
- `django/test/__init__.py` — exports
- `tests/` — 25+ usage sites

## Search Strategy
- Search for `class RequestFactory` to find definition
- Search for `RequestFactory` across codebase for all references
- Search for `from django.test import` for import patterns
""",
    },
    {
        "id": "prometheus-query-engine-refac-001",
        "repo": "prometheus/prometheus",
        "mirror": "sg-evals/prometheus--ba14bc4",
        "language": "go",
        "category": "cross_file_refactoring",
        "difficulty": "hard",
        "time_limit_sec": 1200,
        "build_timeout_sec": 900,
        "description": "Rename QueryEngine to PromQLEvaluator in Prometheus promql package",
        "old_symbol": "QueryEngine",
        "new_symbol": "PromQLEvaluator",
        "search_dirs": ["promql/", "web/", "cmd/"],
        "expected_refs": 15,
        "instruction": """# Task: Rename QueryEngine to PromQLEvaluator

## Objective
Rename the `QueryEngine` struct to `PromQLEvaluator` in the Prometheus PromQL package
to better describe its role as a PromQL expression evaluator.

## Requirements

1. **Rename the struct definition** in `promql/engine.go`:
   - `type QueryEngine struct` → `type PromQLEvaluator struct`
   - Rename constructor: `NewQueryEngine` → `NewPromQLEvaluator`

2. **Update all references** (15+ call sites):
   - `web/api/v1/api.go` — API handler initialization
   - `cmd/prometheus/main.go` — engine creation
   - `promql/` package internal references
   - Interface references and type assertions

3. **Update receiver methods**:
   - All methods on `*QueryEngine` → `*PromQLEvaluator`

## Key Reference Files
- `promql/engine.go` — struct definition, constructor, methods
- `web/api/v1/api.go` — API uses QueryEngine
- `cmd/prometheus/main.go` — creates QueryEngine

## Success Criteria
- `type QueryEngine struct` no longer exists
- `type PromQLEvaluator struct` exists
- Constructor renamed to NewPromQLEvaluator
- References updated across 80%+ of call sites
""",
        "claude_md": """# prometheus-query-engine-refac-001: Rename QueryEngine

## Task Type: Cross-File Refactoring (Rename)

Rename QueryEngine → PromQLEvaluator across Prometheus.

## Key Reference Files
- `promql/engine.go` — struct definition
- `web/api/v1/api.go` — API usage
- `cmd/prometheus/main.go` — initialization

## Search Strategy
- Search for `type QueryEngine struct` for definition
- Search for `QueryEngine` across all Go files for references
- Search for `NewQueryEngine` for constructor usage
""",
    },
    {
        "id": "terraform-eval-context-refac-001",
        "repo": "hashicorp/terraform",
        "mirror": "sg-evals/terraform--v1.10.3",
        "language": "go",
        "category": "cross_file_refactoring",
        "difficulty": "hard",
        "time_limit_sec": 1200,
        "build_timeout_sec": 900,
        "description": "Rename NodeAbstractResourceInstance to NodeResourceInstanceBase in Terraform",
        "old_symbol": "NodeAbstractResourceInstance",
        "new_symbol": "NodeResourceInstanceBase",
        "search_dirs": ["internal/terraform/"],
        "expected_refs": 10,
        "instruction": """# Task: Rename NodeAbstractResourceInstance to NodeResourceInstanceBase

## Objective
Rename `NodeAbstractResourceInstance` to `NodeResourceInstanceBase` in Terraform's
internal graph node hierarchy to follow Go naming conventions (avoiding "Abstract").

## Requirements

1. **Rename the struct** in `internal/terraform/node_resource_abstract_instance.go`:
   - `type NodeAbstractResourceInstance struct` → `type NodeResourceInstanceBase struct`
   - Rename the file to `node_resource_instance_base.go` (optional)

2. **Update all references** (10+ call sites):
   - Embedding in other node types
   - Method receivers
   - Type assertions and casts
   - Graph builder functions

3. **Update receiver methods** on the struct

## Key Reference Files
- `internal/terraform/node_resource_abstract_instance.go` — struct definition
- `internal/terraform/node_resource_apply_instance.go` — embeds the struct
- `internal/terraform/node_resource_plan_instance.go` — embeds the struct
- `internal/terraform/node_resource_destroy.go` — references

## Success Criteria
- `NodeAbstractResourceInstance` no longer used as struct name
- `NodeResourceInstanceBase` used instead
- Embedding sites updated
- Method receivers updated
""",
        "claude_md": """# terraform-eval-context-refac-001: Rename NodeAbstractResourceInstance

## Task Type: Cross-File Refactoring (Rename)

Rename NodeAbstractResourceInstance → NodeResourceInstanceBase in Terraform.

## Key Reference Files
- `internal/terraform/node_resource_abstract_instance.go` — definition
- `internal/terraform/node_resource_apply_instance.go` — embedding
- `internal/terraform/node_resource_plan_instance.go` — embedding

## Search Strategy
- Search for `NodeAbstractResourceInstance` for all references
- Search for `node_resource_abstract` for file names
""",
    },
    {
        "id": "cilium-endpoint-manager-refac-001",
        "repo": "cilium/cilium",
        "mirror": "sg-evals/cilium--v1.16.5",
        "language": "go",
        "category": "cross_file_refactoring",
        "difficulty": "expert",
        "time_limit_sec": 1200,
        "build_timeout_sec": 900,
        "description": "Extract EndpointRegenerator from pkg/endpoint/manager.go in Cilium",
        "old_symbol": "endpointManager",
        "new_symbol": "EndpointRegenerator",
        "search_dirs": ["pkg/endpoint/"],
        "expected_refs": 15,
        "instruction": """# Task: Extract EndpointRegenerator from Endpoint Manager

## Objective
Extract the regeneration logic from `pkg/endpoint/manager.go` into a new
`EndpointRegenerator` struct in `pkg/endpoint/regenerator.go`, following the
single-responsibility principle.

## Requirements

1. **Create `pkg/endpoint/regenerator.go`**:
   - `EndpointRegenerator` struct with regeneration-related fields from manager
   - Move regeneration methods: `RegenerateAllEndpoints`, `WaitForEndpointRegeneration`
   - Keep manager as coordinator that delegates to regenerator

2. **Update `pkg/endpoint/manager.go`**:
   - Add `regenerator *EndpointRegenerator` field
   - Delegate regeneration calls to new struct
   - Remove extracted methods

3. **Update callers** that call regeneration methods through manager

## Key Reference Files
- `pkg/endpoint/manager.go` — current manager with regeneration logic
- `pkg/endpoint/endpoint.go` — Endpoint struct
- `pkg/endpoint/regeneration.go` — regeneration logic (if exists)

## Success Criteria
- EndpointRegenerator struct exists in a separate file
- Regeneration methods moved to EndpointRegenerator
- Manager delegates to EndpointRegenerator
- Callers updated
""",
        "claude_md": """# cilium-endpoint-manager-refac-001: Extract EndpointRegenerator

## Task Type: Cross-File Refactoring (Extract)

Extract regeneration logic into EndpointRegenerator struct.

## Key Reference Files
- `pkg/endpoint/manager.go` — source of extraction
- `pkg/endpoint/endpoint.go` — Endpoint struct

## Search Strategy
- Search for `Regenerat` in `pkg/endpoint/` for regeneration methods
- Search for `endpointManager` for manager references
""",
    },
    {
        "id": "envoy-listener-manager-refac-001",
        "repo": "envoyproxy/envoy",
        "mirror": "sg-evals/envoy--v1.33.0",
        "language": "cpp",
        "category": "cross_file_refactoring",
        "difficulty": "expert",
        "time_limit_sec": 1800,
        "build_timeout_sec": 1200,
        "description": "Rename ListenerManagerImpl to ListenerOrchestrator in Envoy",
        "old_symbol": "ListenerManagerImpl",
        "new_symbol": "ListenerOrchestrator",
        "search_dirs": ["source/common/listener_manager/", "source/server/", "test/"],
        "expected_refs": 20,
        "instruction": """# Task: Rename ListenerManagerImpl to ListenerOrchestrator

## Objective
Rename `ListenerManagerImpl` to `ListenerOrchestrator` in Envoy to better
describe the class's role as an orchestrator of listener lifecycle operations.

## Requirements

1. **Rename the class definition**:
   - `class ListenerManagerImpl` → `class ListenerOrchestrator`
   - Update header file and implementation file

2. **Update all references** (20+ call sites):
   - Constructor calls
   - Type declarations and pointers
   - Test files
   - Factory registrations

3. **Update header guards and includes**

## Key Reference Files
- `source/common/listener_manager/listener_manager_impl.h` — class declaration
- `source/common/listener_manager/listener_manager_impl.cc` — implementation
- `source/server/server.h` — uses ListenerManagerImpl
- `test/common/listener_manager/listener_manager_impl_test.cc` — tests

## Success Criteria
- `class ListenerManagerImpl` no longer exists
- `class ListenerOrchestrator` exists
- 80%+ of references updated
- Tests still reference the class correctly
""",
        "claude_md": """# envoy-listener-manager-refac-001: Rename ListenerManagerImpl

## Task Type: Cross-File Refactoring (Rename)

Rename ListenerManagerImpl → ListenerOrchestrator in Envoy.

## Key Reference Files
- `source/common/listener_manager/listener_manager_impl.h` — declaration
- `source/common/listener_manager/listener_manager_impl.cc` — implementation
- `source/server/server.h` — usage

## Search Strategy
- Search for `ListenerManagerImpl` across the codebase
- Search for `listener_manager_impl` for file references
""",
    },
    {
        "id": "numpy-array-dispatch-refac-001",
        "repo": "numpy/numpy",
        "mirror": "sg-evals/numpy--v2.2.2",
        "language": "python",
        "category": "cross_file_refactoring",
        "difficulty": "expert",
        "time_limit_sec": 1200,
        "build_timeout_sec": 900,
        "description": "Rename _implement_array_function to _dispatch_array_function in NumPy",
        "old_symbol": "_implement_array_function",
        "new_symbol": "_dispatch_array_function",
        "search_dirs": ["numpy/"],
        "expected_refs": 40,
        "instruction": """# Task: Rename _implement_array_function to _dispatch_array_function

## Objective
Rename `_implement_array_function` to `_dispatch_array_function` throughout NumPy
to better describe the function's role as a dispatch mechanism.

## Requirements

1. **Rename in core definition** (likely `numpy/core/overrides.py`):
   - Function/method name change
   - Docstring update

2. **Update all call sites** (40+ references):
   - `numpy/core/` — core usage
   - `numpy/lib/` — library functions that use dispatch
   - `numpy/ma/` — masked array dispatch
   - Test files

3. **Update any C-level references** if the symbol is exposed to C

## Key Reference Files
- `numpy/core/overrides.py` — dispatch mechanism definition
- `numpy/lib/_function_base_impl.py` — heavy user
- `numpy/ma/core.py` — masked array dispatch

## Success Criteria
- `_implement_array_function` no longer used as function name
- `_dispatch_array_function` used instead
- 80%+ of 40+ call sites updated
""",
        "claude_md": """# numpy-array-dispatch-refac-001: Rename dispatch function

## Task Type: Cross-File Refactoring (Rename)

Rename _implement_array_function → _dispatch_array_function across NumPy.

## Key Reference Files
- `numpy/core/overrides.py` — definition
- `numpy/lib/` — heavy usage
- `numpy/ma/core.py` — masked array usage

## Search Strategy
- Search for `_implement_array_function` for all references
- Search for `array_function_dispatch` for related dispatch code
""",
    },
    {
        "id": "pytorch-optimizer-foreach-refac-001",
        "repo": "pytorch/pytorch",
        "mirror": "sg-evals/pytorch--d18007a1",
        "language": "python",
        "category": "cross_file_refactoring",
        "difficulty": "expert",
        "time_limit_sec": 1200,
        "build_timeout_sec": 900,
        "description": "Extract _foreach_optimizer_step to a shared module in torch/optim/",
        "old_symbol": "_multi_tensor_",
        "new_symbol": "_foreach_optimizer_step",
        "search_dirs": ["torch/optim/"],
        "expected_refs": 8,
        "instruction": """# Task: Extract Shared Foreach Optimizer Step

## Objective
Extract the repeated `_multi_tensor_*` foreach optimization patterns from individual
optimizer files (sgd.py, adam.py, adamw.py, etc.) into a shared
`torch/optim/_foreach.py` module.

## Requirements

1. **Create `torch/optim/_foreach.py`**:
   - `_foreach_optimizer_step(params, grads, step_fn, **kwargs)` function
   - Common foreach/fused parameter handling logic
   - Shared gradient scaling and clipping utilities

2. **Update optimizer files** to use the shared module:
   - `torch/optim/sgd.py`
   - `torch/optim/adam.py`
   - `torch/optim/adamw.py`
   - Others that have `_multi_tensor_` functions

3. **Keep backward compatibility**: existing public APIs unchanged

## Key Reference Files
- `torch/optim/sgd.py` — `_multi_tensor_sgd` function
- `torch/optim/adam.py` — `_multi_tensor_adam` function
- `torch/optim/adamw.py` — `_multi_tensor_adamw` function
- `torch/optim/_functional.py` — functional optimizer implementations

## Success Criteria
- `torch/optim/_foreach.py` exists with shared logic
- At least 3 optimizer files import from _foreach
- Duplicate foreach patterns reduced
- Original optimizer APIs still work
""",
        "claude_md": """# pytorch-optimizer-foreach-refac-001: Extract foreach step

## Task Type: Cross-File Refactoring (Extract)

Extract shared foreach optimization into torch/optim/_foreach.py.

## Key Reference Files
- `torch/optim/sgd.py` — _multi_tensor_sgd
- `torch/optim/adam.py` — _multi_tensor_adam
- `torch/optim/_functional.py` — functional implementations

## Search Strategy
- Search for `_multi_tensor_` in `torch/optim/` for pattern locations
- Search for `_foreach_` for existing foreach usage
""",
    },
    {
        "id": "istio-discovery-server-refac-001",
        "repo": "istio/istio",
        "mirror": "sg-evals/istio--f8af3cae",
        "language": "go",
        "category": "cross_file_refactoring",
        "difficulty": "hard",
        "time_limit_sec": 1200,
        "build_timeout_sec": 900,
        "description": "Rename DiscoveryServer to XDSServer in Istio pilot xds package",
        "old_symbol": "DiscoveryServer",
        "new_symbol": "XDSServer",
        "search_dirs": ["pilot/pkg/xds/", "pilot/pkg/bootstrap/"],
        "expected_refs": 30,
        "instruction": """# Task: Rename DiscoveryServer to XDSServer

## Objective
Rename `DiscoveryServer` to `XDSServer` in Istio's pilot xDS package to better
describe the server's role as an xDS (discovery service) protocol server.

## Requirements

1. **Rename struct** in `pilot/pkg/xds/discovery.go`:
   - `type DiscoveryServer struct` → `type XDSServer struct`
   - Rename constructor: `NewDiscoveryServer` → `NewXDSServer`

2. **Update all references** (30+ call sites):
   - `pilot/pkg/xds/` — internal package references
   - `pilot/pkg/bootstrap/` — server initialization
   - `pilot/pkg/networking/` — xDS generation
   - Test files

3. **Update receiver methods**

## Key Reference Files
- `pilot/pkg/xds/discovery.go` — struct definition
- `pilot/pkg/bootstrap/server.go` — creates DiscoveryServer
- `pilot/pkg/xds/ads.go` — uses DiscoveryServer

## Success Criteria
- `type DiscoveryServer struct` no longer exists
- `type XDSServer struct` exists
- Constructor renamed
- 80%+ of references updated
""",
        "claude_md": """# istio-discovery-server-refac-001: Rename DiscoveryServer

## Task Type: Cross-File Refactoring (Rename)

Rename DiscoveryServer → XDSServer across Istio pilot.

## Key Reference Files
- `pilot/pkg/xds/discovery.go` — definition
- `pilot/pkg/bootstrap/server.go` — initialization
- `pilot/pkg/xds/ads.go` — usage

## Search Strategy
- Search for `DiscoveryServer` across pilot/ for all references
- Search for `NewDiscoveryServer` for constructor calls
""",
    },
    {
        "id": "kubernetes-scheduler-profile-refac-001",
        "repo": "kubernetes/kubernetes",
        "mirror": "sg-evals/kubernetes--v1.30.0",
        "language": "go",
        "category": "cross_file_refactoring",
        "difficulty": "hard",
        "time_limit_sec": 1200,
        "build_timeout_sec": 900,
        "description": "Rename SchedulerProfile to SchedulingProfile in Kubernetes scheduler",
        "old_symbol": "SchedulerProfile",
        "new_symbol": "SchedulingProfile",
        "search_dirs": ["pkg/scheduler/", "staging/src/k8s.io/kube-scheduler/"],
        "expected_refs": 15,
        "instruction": """# Task: Rename SchedulerProfile to SchedulingProfile

## Objective
Rename `SchedulerProfile` to `SchedulingProfile` in the Kubernetes scheduler
to follow the API naming convention (action-noun pattern).

## Requirements

1. **Rename the type** (likely in scheduler config or profile package):
   - `type SchedulerProfile struct` → `type SchedulingProfile struct`

2. **Update all references** (15+ call sites):
   - `pkg/scheduler/` — scheduler internals
   - `staging/src/k8s.io/kube-scheduler/` — API types
   - Config and profile loading code
   - Test files

3. **Update constructor functions** and factory methods

## Key Reference Files
- `pkg/scheduler/profile/profile.go` — profile definition
- `pkg/scheduler/scheduler.go` — uses profiles
- `staging/src/k8s.io/kube-scheduler/config/` — API config types

## Success Criteria
- `SchedulerProfile` no longer used as type name
- `SchedulingProfile` used instead
- 80%+ of references updated
""",
        "claude_md": """# kubernetes-scheduler-profile-refac-001: Rename SchedulerProfile

## Task Type: Cross-File Refactoring (Rename)

Rename SchedulerProfile → SchedulingProfile in Kubernetes scheduler.

## Key Reference Files
- `pkg/scheduler/profile/` — profile definition
- `pkg/scheduler/scheduler.go` — usage
- `staging/src/k8s.io/kube-scheduler/` — API types

## Search Strategy
- Search for `SchedulerProfile` across the codebase
- Search for `type SchedulerProfile` for definition
""",
    },
    {
        "id": "pandas-index-engine-refac-001",
        "repo": "pandas-dev/pandas",
        "mirror": "sg-evals/pandas--v2.2.3",
        "language": "python",
        "category": "cross_file_refactoring",
        "difficulty": "hard",
        "time_limit_sec": 1200,
        "build_timeout_sec": 900,
        "description": "Rename _engine property to _index_engine in pandas Index class",
        "old_symbol": "_engine",
        "new_symbol": "_index_engine",
        "search_dirs": ["pandas/core/indexes/"],
        "expected_refs": 20,
        "instruction": """# Task: Rename _engine to _index_engine in Index

## Objective
Rename the `_engine` property/attribute to `_index_engine` in `pandas/core/indexes/base.py`
and all subclasses to avoid naming collisions and improve clarity.

## Requirements

1. **Rename in base class** `pandas/core/indexes/base.py`:
   - `_engine` property → `_index_engine`
   - Update cache decorators and lazy evaluation

2. **Update all subclass overrides** (20+ references):
   - `pandas/core/indexes/range.py`
   - `pandas/core/indexes/multi.py`
   - `pandas/core/indexes/datetimes.py`
   - `pandas/core/indexes/period.py`
   - Internal callers

3. **Update internal callers** that access `._engine`

## Key Reference Files
- `pandas/core/indexes/base.py` — base Index with _engine
- `pandas/core/indexes/range.py` — RangeIndex override
- `pandas/core/indexes/multi.py` — MultiIndex
- `pandas/_libs/index.pyx` — Cython engine implementations

## Success Criteria
- `_engine` no longer used as property name in Index
- `_index_engine` used instead
- Subclass overrides updated
- Internal callers updated (80%+)
""",
        "claude_md": """# pandas-index-engine-refac-001: Rename _engine property

## Task Type: Cross-File Refactoring (Rename)

Rename _engine → _index_engine across pandas Index hierarchy.

## Key Reference Files
- `pandas/core/indexes/base.py` — base definition
- `pandas/core/indexes/range.py` — RangeIndex
- `pandas/core/indexes/multi.py` — MultiIndex

## Search Strategy
- Search for `_engine` in `pandas/core/indexes/` for all references
- Search for `def _engine` for property definitions
""",
    },
    {
        "id": "scikit-learn-estimator-tags-refac-001",
        "repo": "scikit-learn/scikit-learn",
        "mirror": "sg-evals/scikit-learn--1.6.1",
        "language": "python",
        "category": "cross_file_refactoring",
        "difficulty": "expert",
        "time_limit_sec": 1200,
        "build_timeout_sec": 900,
        "description": "Rename _get_tags to _estimator_tags across scikit-learn estimator hierarchy",
        "old_symbol": "_get_tags",
        "new_symbol": "_estimator_tags",
        "search_dirs": ["sklearn/"],
        "expected_refs": 50,
        "instruction": """# Task: Rename _get_tags to _estimator_tags

## Objective
Rename `_get_tags` method to `_estimator_tags` across the scikit-learn estimator hierarchy
to better describe the method's purpose and avoid confusion with generic getter patterns.

## Requirements

1. **Rename in base estimator** `sklearn/base.py`:
   - `def _get_tags(self)` → `def _estimator_tags(self)`

2. **Update ALL overrides** across estimator hierarchy (50+ references):
   - `sklearn/linear_model/` — LinearRegression, LogisticRegression, etc.
   - `sklearn/tree/` — DecisionTreeClassifier, etc.
   - `sklearn/ensemble/` — RandomForestClassifier, etc.
   - `sklearn/svm/` — SVC, SVR, etc.
   - `sklearn/utils/estimator_checks.py` — tag checking utilities
   - Test files

3. **Update tag checking utilities** that call `_get_tags()`

## Key Reference Files
- `sklearn/base.py` — BaseEstimator._get_tags()
- `sklearn/utils/estimator_checks.py` — uses _get_tags extensively
- `sklearn/utils/_tags.py` — tag-related utilities

## Success Criteria
- `_get_tags` no longer used as method name in BaseEstimator
- `_estimator_tags` used instead
- 80%+ of 50+ overrides and call sites updated
""",
        "claude_md": """# scikit-learn-estimator-tags-refac-001: Rename _get_tags

## Task Type: Cross-File Refactoring (Rename)

Rename _get_tags → _estimator_tags across scikit-learn.

## Key Reference Files
- `sklearn/base.py` — BaseEstimator definition
- `sklearn/utils/estimator_checks.py` — tag checking
- `sklearn/utils/_tags.py` — tag utilities

## Search Strategy
- Search for `_get_tags` across sklearn/ for all references
- Search for `def _get_tags` for overrides
""",
    },
    {
        "id": "curl-multi-process-refac-001",
        "repo": "curl/curl",
        "mirror": "sg-evals/curl--09e25b9d",
        "language": "c",
        "category": "cross_file_refactoring",
        "difficulty": "hard",
        "time_limit_sec": 1200,
        "build_timeout_sec": 900,
        "description": "Rename Curl_multi_process_pending_handles to multi_activate_pending in curl",
        "old_symbol": "Curl_multi_process_pending_handles",
        "new_symbol": "multi_activate_pending",
        "search_dirs": ["lib/"],
        "expected_refs": 5,
        "instruction": """# Task: Rename Curl_multi_process_pending_handles

## Objective
Rename `Curl_multi_process_pending_handles` to `multi_activate_pending` in curl's
multi interface to follow the shorter internal naming convention.

## Requirements

1. **Rename function** in `lib/multi.c`:
   - `Curl_multi_process_pending_handles` → `multi_activate_pending`
   - Make it `static` if not used outside multi.c

2. **Update declaration** in `lib/multihandle.h` or `lib/multi.h`

3. **Update all call sites** (5+ references in lib/)

## Key Reference Files
- `lib/multi.c` — function definition and main callers
- `lib/multihandle.h` — multi handle declarations
- `lib/url.c` — potential caller

## Success Criteria
- `Curl_multi_process_pending_handles` no longer exists
- `multi_activate_pending` used instead
- All call sites updated
- Function compiles (declaration matches)
""",
        "claude_md": """# curl-multi-process-refac-001: Rename multi process function

## Task Type: Cross-File Refactoring (Rename)

Rename Curl_multi_process_pending_handles → multi_activate_pending.

## Key Reference Files
- `lib/multi.c` — function definition
- `lib/multihandle.h` — declaration
- `lib/url.c` — caller

## Search Strategy
- Search for `Curl_multi_process_pending_handles` for all references
- Search for `multi_process_pending` for partial matches
""",
    },
    {
        "id": "etcd-raft-storage-refac-001",
        "repo": "etcd-io/etcd",
        "mirror": "sg-evals/etcd--d89978e8",
        "language": "go",
        "category": "cross_file_refactoring",
        "difficulty": "hard",
        "time_limit_sec": 1200,
        "build_timeout_sec": 900,
        "description": "Rename MemoryStorage to InMemoryRaftLog in etcd raft package",
        "old_symbol": "MemoryStorage",
        "new_symbol": "InMemoryRaftLog",
        "search_dirs": ["raft/", "server/"],
        "expected_refs": 20,
        "instruction": """# Task: Rename MemoryStorage to InMemoryRaftLog

## Objective
Rename `MemoryStorage` to `InMemoryRaftLog` in etcd's raft package to better
describe the struct's role as an in-memory Raft log implementation.

## Requirements

1. **Rename struct** in raft storage file:
   - `type MemoryStorage struct` → `type InMemoryRaftLog struct`
   - Rename constructor: `NewMemoryStorage` → `NewInMemoryRaftLog`

2. **Update all references** (20+ call sites):
   - `raft/` package — internal usage
   - `server/` — server initialization
   - Test files
   - Interface implementations

3. **Update receiver methods**

## Key Reference Files
- `raft/storage.go` — MemoryStorage definition
- `raft/raft.go` — uses storage
- `raft/raft_test.go` — test usage
- `server/etcdserver/raft.go` — server integration

## Success Criteria
- `type MemoryStorage struct` no longer exists
- `type InMemoryRaftLog struct` exists
- Constructor renamed
- 80%+ of references updated
""",
        "claude_md": """# etcd-raft-storage-refac-001: Rename MemoryStorage

## Task Type: Cross-File Refactoring (Rename)

Rename MemoryStorage → InMemoryRaftLog in etcd raft package.

## Key Reference Files
- `raft/storage.go` — definition
- `raft/raft.go` — usage
- `server/etcdserver/raft.go` — server integration

## Search Strategy
- Search for `MemoryStorage` across raft/ and server/
- Search for `NewMemoryStorage` for constructor calls
""",
    },
]


def generate_refactor_test_sh(task):
    """Generate test.sh for a refactor task with 4-layer verification."""
    old = task["old_symbol"]
    new = task["new_symbol"]
    dirs = task["search_dirs"]
    expected = task["expected_refs"]
    min_refs = max(1, int(expected * 0.5))  # 50% threshold for partial credit

    # Join search dirs for grep
    dirs_str = " ".join(f'"$WORKSPACE/{d}"' for d in dirs)

    return f'''#!/bin/bash
set -euo pipefail

[ -f /tmp/.sg_only_mode ] && [ -f /tests/sgonly_verifier_wrapper.sh ] && source /tests/sgonly_verifier_wrapper.sh

SCORE=0
TOTAL=6
TASK_WORKDIR="${{TASK_WORKDIR:-/workspace}}"
TASK_REPO_ROOT="${{TASK_REPO_ROOT:-${{VERIFY_REPO:-$TASK_WORKDIR}}}}"
WORKSPACE="$$TASK_REPO_ROOT"

# Check 1: Old symbol removed from primary definition
OLD_DEF_COUNT=$(grep -r 'class {old}\\|type {old} struct\\|def {old}\\|function {old}' {dirs_str} 2>/dev/null | grep -v 'alias\\|compat\\|deprecated\\|backward\\|#.*{old}\\|//.*{old}' | wc -l)
if [ "$OLD_DEF_COUNT" -eq 0 ]; then
    SCORE=$((SCORE + 1))
    echo "PASS: Old symbol definition removed"
else
    echo "FAIL: Old symbol \\"{old}\\" still defined ($OLD_DEF_COUNT definitions found)"
fi

# Check 2: New symbol exists in definition
NEW_DEF_COUNT=$(grep -r 'class {new}\\|type {new} struct\\|def {new}\\|function {new}\\|{new}' {dirs_str} 2>/dev/null | wc -l)
if [ "$NEW_DEF_COUNT" -gt 0 ]; then
    SCORE=$((SCORE + 1))
    echo "PASS: New symbol \\"{new}\\" found ($NEW_DEF_COUNT occurrences)"
else
    echo "FAIL: New symbol \\"{new}\\" not found"
fi

# Check 3: Old symbol reference count reduced (allowing aliases/deprecation)
OLD_REF_COUNT=$(grep -r '{old}' {dirs_str} 2>/dev/null | grep -v 'test\\|_test\\|spec\\|alias\\|compat\\|deprecated\\|backward\\|#.*{old}\\|//.*{old}\\|\\.pyc' | wc -l)
if [ "$OLD_REF_COUNT" -le 3 ]; then
    SCORE=$((SCORE + 1))
    echo "PASS: Old symbol references minimized ($OLD_REF_COUNT remaining, max 3)"
else
    echo "FAIL: Too many old symbol references remain ($OLD_REF_COUNT, max 3)"
fi

# Check 4: New symbol used across multiple files
NEW_FILE_COUNT=$(grep -rl '{new}' {dirs_str} 2>/dev/null | wc -l)
if [ "$NEW_FILE_COUNT" -ge 2 ]; then
    SCORE=$((SCORE + 1))
    echo "PASS: New symbol used across $NEW_FILE_COUNT files"
else
    echo "FAIL: New symbol only in $NEW_FILE_COUNT files (need >= 2)"
fi

# Check 5: New symbol call sites meet threshold
NEW_REF_COUNT=$(grep -r '{new}' {dirs_str} 2>/dev/null | wc -l)
if [ "$NEW_REF_COUNT" -ge {min_refs} ]; then
    SCORE=$((SCORE + 1))
    echo "PASS: New symbol has $NEW_REF_COUNT references (>= {min_refs})"
else
    echo "FAIL: New symbol only has $NEW_REF_COUNT references (need >= {min_refs})"
fi

# Check 6: Code changes were actually made (git diff check)
cd "$WORKSPACE"
CHANGED_FILES=$(git diff --name-only 2>/dev/null | wc -l)
COMMITTED_FILES=$(git log --oneline --name-only -1 2>/dev/null | tail -n +2 | wc -l)
TOTAL_CHANGES=$((CHANGED_FILES + COMMITTED_FILES))
if [ "$TOTAL_CHANGES" -ge 2 ]; then
    SCORE=$((SCORE + 1))
    echo "PASS: Multiple files changed ($TOTAL_CHANGES)"
else
    echo "FAIL: Not enough files changed ($TOTAL_CHANGES, need >= 2)"
fi

echo ""
echo "Score: $SCORE / $TOTAL"

mkdir -p /logs/verifier
python3 -c "print($SCORE / $TOTAL)" > /logs/verifier/reward.txt
'''


def generate_task_toml(task):
    return f'''version = "1.0"

[metadata]
name = "{task['id']}"
description = "{task['description']}"
license = "Apache-2.0"
author_name = "CodeScaleBench"
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
description = "Checks refactoring: old symbol removal, new symbol presence, reference count, multi-file changes"

[environment]
build_timeout_sec = {task['build_timeout_sec']}.0
cpus = 4
memory = "8G"
storage = "10G"

[environment.setup_scripts]
mcp_config = \'\'\'
#!/bin/bash
echo "Sourcegraph MCP available for code search"
\'\'\'
'''


def generate_dockerfile(task):
    return f'''FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV TASK_WORKDIR=/workspace
ENV TASK_REPO_ROOT=/workspace

RUN apt-get update && apt-get install -y --no-install-recommends \\
    git ca-certificates python3 curl \\
    && rm -rf /var/lib/apt/lists/*

RUN (adduser --disabled-password --gecos '' claude 2>/dev/null || true)

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
    return f'''FROM ubuntu:22.04

ENV SOURCEGRAPH_REPO_NAME={task['mirror']}
ENV DEBIAN_FRONTEND=noninteractive
ENV TASK_WORKDIR=/workspace
ENV TASK_REPO_ROOT=/workspace

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
    return json.dumps({
        "task_id": task["id"],
        "old_symbol": task["old_symbol"],
        "new_symbol": task["new_symbol"],
        "expected_refs": task["expected_refs"],
        "search_dirs": task["search_dirs"],
    }, indent=2) + '\n'


def main():
    for task in TASKS:
        task_dir = os.path.join(BENCHMARK_DIR, task['id'])
        env_dir = os.path.join(task_dir, 'environment')
        tests_dir = os.path.join(task_dir, 'tests')

        os.makedirs(env_dir, exist_ok=True)
        os.makedirs(tests_dir, exist_ok=True)

        with open(os.path.join(task_dir, 'task.toml'), 'w') as f:
            f.write(generate_task_toml(task))

        with open(os.path.join(task_dir, 'instruction.md'), 'w') as f:
            f.write(task['instruction'].strip() + '\n')

        with open(os.path.join(task_dir, 'CLAUDE.md'), 'w') as f:
            f.write(task['claude_md'].strip() + '\n')

        with open(os.path.join(env_dir, 'Dockerfile'), 'w') as f:
            f.write(generate_dockerfile(task))

        with open(os.path.join(env_dir, 'Dockerfile.sg_only'), 'w') as f:
            f.write(generate_dockerfile_sg_only(task))

        test_sh_path = os.path.join(tests_dir, 'test.sh')
        with open(test_sh_path, 'w') as f:
            f.write(generate_refactor_test_sh(task))
        os.chmod(test_sh_path, 0o755)

        with open(os.path.join(tests_dir, 'ground_truth.json'), 'w') as f:
            f.write(generate_ground_truth(task))

        if os.path.exists(SGONLY_WRAPPER):
            shutil.copy2(SGONLY_WRAPPER, os.path.join(tests_dir, 'sgonly_verifier_wrapper.sh'))

        print(f"  Scaffolded: {task['id']}")

    print(f"\nTotal: {len(TASKS)} refactor tasks scaffolded in {BENCHMARK_DIR}")


if __name__ == '__main__':
    main()
