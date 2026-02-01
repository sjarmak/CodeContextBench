# 10Figure Benchmark

End-to-end benchmark for evaluating coding agents on large-scale codebases using the 10Figure corpus (Kubernetes, Envoy, Django, TensorFlow).

Part of [CodeContextBench](https://github.com/sjarmak/CodeContextBench_Dashboard).

## Overview

| Attribute | Value |
|-----------|-------|
| **Tasks** | 5 (4 real + 1 smoke test) |
| **Source Repository** | [kubernetes/kubernetes](https://github.com/kubernetes/kubernetes) |
| **Language** | Go |
| **Task Types** | API upgrade, bug localization, cross-file reasoning, refactoring |
| **Difficulty** | Hard |
| **Evaluation** | Patch validation against expected changes |

## Tasks

| Task ID | Type | Description |
|---------|------|-------------|
| `api_upgrade_01` | API Migration | Migrate from `pointer.Int32()` to generic `ptr.To[int32]()` |
| `bug_localization_01` | Bug Localization | Find nil pointer dereference in EventedPLEG status update |
| `cross_file_reasoning_01` | Cross-File Reasoning | Trace Pod creation request flow from HTTP handler to validation |
| `refactor_rename_01` | Refactoring | Rename symbol throughout codebase while maintaining functionality |
| `simple_test_01` | Smoke Test | Basic validation that agent environment works |

## Prerequisites

- **Docker or Podman** installed and running
- **Python 3.8+** with `pyyaml` and `jinja2` (`pip install pyyaml jinja2`)
- **~10GB disk space** (~5GB corpus + ~6-8GB Docker image)

## Quick Start

```bash
# 1. Clone
git clone https://github.com/sjarmak/ccb-10figure.git
cd ccb-10figure

# 2. Configure environment
cp .env.local.example .env.local
# Edit .env.local with your API keys

# 3. Build base Docker image
cd base && bash build.sh && cd ..

# 4. Validate setup
python tests/smoke_test_10figure.py

# 5. Run a task
harbor run \
  --dockerfile simple_test_01/environment/Dockerfile \
  --test-script simple_test_01/tests/test.sh
```

## Setup

### Step 1: Build the base Docker image

The base image embeds the entire corpus so individual tasks don't need to re-copy it.

```bash
cd base

# Uses ~/10Figure-Codebases by default
./build.sh

# Or specify a custom corpus location
CORPUS_PATH=/path/to/10Figure-Codebases ./build.sh
```

Verify the image:

```bash
docker run --rm harbor-10figure:base ls /10figure/src
# Expected output: django  envoy  kubernetes  tensorflow
```

See `base/README.md` for details on the image contents and build process.

### Step 2: Configure environment

```bash
cp .env.local.example .env.local
# Edit with your credentials
source infrastructure/load-env.sh
```

### Step 3: Run tasks

#### Single task via Harbor

```bash
harbor run \
  --dockerfile api_upgrade_01/environment/Dockerfile \
  --test-script api_upgrade_01/tests/test.sh \
  --config api_upgrade_01/task.toml
```

#### Batch execution

```bash
bash runners/harbor_benchmark.sh \
  --benchmark 10figure \
  --agent claude-baseline \
  --tasks 5
```

#### Direct Python runner

```bash
python runners/run_benchmark.py \
  --benchmark 10figure \
  --agent claude-baseline \
  --tasks 4
```

## Repository Structure

```
ccb-10figure/
├── README.md                          # This file
├── .env.local.example                 # Environment config template
├── base/                              # Docker base image
│   ├── Dockerfile                     # Base image definition
│   ├── build.sh                       # Build script
│   └── README.md                      # Base image docs
├── api_upgrade_01/                    # Task: API migration
│   ├── instruction.md                 # Agent instruction
│   ├── task.toml                      # Harbor metadata
│   ├── task.yaml                      # Task definition
│   ├── environment/Dockerfile         # Container setup
│   └── tests/
│       ├── test.sh                    # Validation script
│       └── expected_changes.json      # Ground truth
├── bug_localization_01/               # Task: Bug finding
├── cross_file_reasoning_01/           # Task: Cross-file tracing
├── refactor_rename_01/                # Task: Symbol renaming
├── simple_test_01/                    # Task: Smoke test
├── templates/
│   └── test.sh.j2                     # Jinja2 template for test scripts
├── scripts/
│   └── gen_harbor_tasks.py            # Generate Harbor tasks from YAML
├── infrastructure/
│   ├── datasets.yaml                  # Dataset contract definition
│   ├── harbor-config.yaml             # Harbor execution config
│   └── load-env.sh                    # Environment loader
├── runners/
│   ├── harbor_benchmark.sh            # Shell-based benchmark runner
│   ├── run_benchmark.py               # Python benchmark runner
│   └── validate_benchmark_setup.py    # Pre-flight validation
├── tests/
│   └── smoke_test_10figure.py         # Smoke test suite
└── docs/
    └── 10FIGURE.md                    # Detailed setup & usage guide
```

## Task Structure

Each task directory contains:

| File | Purpose |
|------|---------|
| `instruction.md` | Human-readable task description for the agent |
| `task.toml` | Harbor metadata (id, type, max_time, difficulty) |
| `task.yaml` | 10Figure task definition with paths and parameters |
| `environment/Dockerfile` | Container setup (inherits from `harbor-10figure:base`) |
| `tests/test.sh` | Validation script that checks agent output |
| `tests/expected_changes.json` | Ground truth for patch validation |

## Validation Pipeline

Each task's `tests/test.sh` script:

1. Checks for the agent's patch file at `/logs/agent/patch.diff`
2. Runs `validate_patch.py` with the patch and task definition
3. Extracts the overall score from the validation result
4. Writes the score (0.0-1.0) to `/logs/verifier/reward.txt`

## Generating New Tasks

To generate Harbor tasks from 10Figure YAML definitions:

```bash
python3 scripts/gen_harbor_tasks.py \
  --input ~/10Figure-Codebases/tasks \
  --output . \
  --templates templates \
  --repo kubernetes \
  --corpus-root /10figure
```

| Flag | Required | Default | Description |
|------|----------|---------|-------------|
| `--input` | Yes | -- | Directory with 10Figure task YAML files |
| `--output` | Yes | -- | Output directory for generated Harbor tasks |
| `--templates` | No | `templates` | Directory with Jinja2 templates |
| `--repo` | No | `kubernetes` | Target repository name |
| `--corpus-root` | No | `/10figure` | Corpus root path in container |

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | Yes | Claude API key |
| `SRC_ACCESS_TOKEN` | For MCP agent | Sourcegraph API token |
| `SOURCEGRAPH_URL` | No | Sourcegraph instance (default: sourcegraph.com) |
| `HARBOR_10FIGURE` | No | Corpus path (default: `/10figure` in containers) |
| `CONTAINER_RUNTIME` | No | `podman` or `docker` (default: `podman`) |

## License

See [CodeContextBench](https://github.com/sjarmak/CodeContextBench_Dashboard) for license information.
