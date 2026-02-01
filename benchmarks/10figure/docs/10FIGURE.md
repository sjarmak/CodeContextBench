# 10Figure Corpus Setup & Usage

## Overview

The 10Figure Corpus is a real-world codebase evaluation framework containing standardized task definitions and target repositories (Kubernetes, Firefox, etc.) for benchmarking agent code understanding and manipulation capabilities.

The corpus is managed via **infrastructure/datasets.yaml**, which defines:
- Container image contract (`harbor-10figure:base`)
- Environment variable setup (`HARBOR_10FIGURE`)
- Task structure and validation
- Generator tool integration

## Corpus Location

**Local:** `/Users/sjarmak/harbor-10figure-dataset/`

The corpus is ~5GB and not version-controlled. It's referenced via:
- Symlinks in development
- Volume mounts in Harbor container execution
- Environment variables for path configuration

## Directory Structure

```
/10figure/
├── src/                           # Source repositories
│   ├── kubernetes/                # Target codebase (multiple versions)
│   ├── firefox/
│   ├── llvm/
│   └── ...
├── tasks/                         # Task definitions (YAML format)
│   ├── cross_file_reasoning_01.yaml
│   ├── cross_file_reasoning_02.yaml
│   ├── refactor_rename_01.yaml
│   ├── api_upgrade_01.yaml
│   ├── bug_localization_01.yaml
│   └── ...
└── scripts/                       # Utilities
    ├── validate_patch.py          # Validator for task evaluation
    └── ...
```

## Task Types

The corpus supports four standardized task types:

### 1. Cross-File Reasoning
Trace function call chains across multiple files to find implementation.

**Example:** Start from a public API, trace through wrapper layers, find the actual implementation.

**Files generated:**
- `instruction.md` - Task description with starting symbol and goal
- `task.yaml` - Task definition with `start_symbol` and `goal`

### 2. Refactor/Rename
Rename a symbol throughout the codebase while maintaining functionality.

**Example:** Rename a function, variable, or class across all call sites.

**Files generated:**
- `instruction.md` - Task description with old/new names
- `task.yaml` - Task definition with `symbol_to_rename` and `new_name`

### 3. API Upgrade
Migrate deprecated API usages to a new API pattern.

**Example:** Update all calls from `old_api()` to `new_api()` with parameter translation.

**Files generated:**
- `instruction.md` - Task description with old/new API patterns
- `task.yaml` - Task definition with `old_api` and `new_api` patterns

### 4. Bug Localization
Find and fix a bug given an error message or symptom.

**Example:** Given "null pointer at line X", localize root cause and implement fix.

**Files generated:**
- `instruction.md` - Task description with error message and symptoms
- `task.yaml` - Task definition with `error_message` and `symptoms` list

## Task Generation Workflow

### Step 1: Generate Harbor Tasks

Convert 10Figure YAML task definitions to Harbor format:

```bash
python3 runners/gen_harbor_tasks.py \
  --input /Users/sjarmak/harbor-10figure-dataset/tasks \
  --output benchmarks/10figure \
  --templates benchmarks/10figure/templates \
  --repo kubernetes \
  --corpus-root /10figure
```

### Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `--input` | Directory with 10Figure task YAML files | Required |
| `--output` | Output directory for generated Harbor tasks | Required |
| `--templates` | Directory with Jinja2 templates (test.sh.j2) | Required |
| `--repo` | Repository name (kubernetes, firefox, etc.) | "kubernetes" |
| `--corpus-root` | Corpus root path in container | "/10figure" |

### Step 2: Generated Task Structure

Each generated task in `benchmarks/10figure/` contains:

```
<task_id>/
├── instruction.md         # Human-readable task description (type-specific)
├── task.toml             # Harbor metadata (id, type, max_time, difficulty)
├── task.yaml             # 10Figure task definition with fixed paths
├── repo_path             # Path to repository in container
├── environment/
│   └── Dockerfile        # Container setup (inherits from harbor-10figure:base)
└── tests/
    └── test.sh           # Validation script (rendered from test.sh.j2)
```

### Step 3: Validate Task Structure

All 5 files are required for Harbor validation:

```bash
ls -la benchmarks/10figure/<task_id>/
# Expected output:
# - instruction.md
# - task.toml
# - task.yaml
# - repo_path
# - environment/Dockerfile
# - tests/test.sh
```

## Container Integration

### Base Image: harbor-10figure:base

Provides:
- 10Figure corpus (pre-loaded)
- Source repositories (in `/10figure/src/`)
- Validator script (`/10figure/scripts/validate_patch.py`)
- Task runner environment

### Building the Base Image

```bash
cd /Users/sjarmak/harbor-10figure-dataset
docker build -t harbor-10figure:base .
```

### Dockerfile Task Setup

Each generated task's `environment/Dockerfile` inherits from the base:

```dockerfile
FROM harbor-10figure:base

# Task-specific setup (if needed)
# The base image already contains the 10Figure corpus and validator

WORKDIR /workspace
```

## Validation Pipeline

### Test Script Execution

The generated `tests/test.sh` runs:

1. **Check patch exists:** `/logs/agent/patch.diff`
2. **Run validator:** `python3 /10figure/scripts/validate_patch.py <patch> --output <result.json>`
3. **Extract score:** Parse `validation_result.json` for `overall_score`
4. **Write reward:** Write score to `/logs/verifier/reward.txt`

### Validator Contract

The validator expects:

| Input | Path | Format |
|-------|------|--------|
| Patch | `/logs/agent/patch.diff` | Unified diff format |
| Task definition | `/task/task.yaml` | 10Figure YAML with fixed paths |
| Corpus root | `/10figure` | Directory with src/ and tasks/ |

| Output | Path | Format |
|--------|------|--------|
| Result | `/logs/verifier/validation_result.json` | JSON with `overall_score` field |
| Reward | `/logs/verifier/reward.txt` | Single float (0.0-1.0) |

## Environment Variables

### Quick Setup

```bash
# 1. Create .env.local from example
cp .env.local.example .env.local

# 2. Edit with your credentials
nano .env.local

# 3. Load environment
source infrastructure/load-env.sh

# 4. Run benchmarks
bash runners/harbor_benchmark.sh --benchmark 10figure --agent claude-baseline
```

### Configuration

Store credentials in `.env.local` (created from `.env.local.example`):

**Required:**
- `ANTHROPIC_API_KEY`: Claude API key (get from https://console.anthropic.com/)

**For Claude+MCP agent:**
- `SOURCEGRAPH_ACCESS_TOKEN`: Sourcegraph API token (legacy scripts may reference `SRC_ACCESS_TOKEN`)

**Optional (with defaults):**
- `SOURCEGRAPH_URL`: Sourcegraph instance (default: https://sourcegraph.sourcegraph.com)
- `HARBOR_10FIGURE`: Corpus path (default: /10figure in containers)
- `CONTAINER_RUNTIME`: Container system - podman or docker (default: podman)

**Important:** Never commit `.env.local` to version control. It's in `.gitignore`.

## Running Tasks in Harbor

### Single Task Execution

```bash
harbor run \
  --dockerfile benchmarks/10figure/<task_id>/environment/Dockerfile \
  --test-script benchmarks/10figure/<task_id>/tests/test.sh \
  --config benchmarks/10figure/<task_id>/task.toml
```

### Batch Execution

Use the benchmark runner:

```bash
bash runners/harbor_benchmark.sh \
  --benchmark 10figure \
  --agent claude-baseline \
  --tasks 10
```

## Example: Generate and Run a Single Task

```bash
# 1. Generate all tasks
python3 runners/gen_harbor_tasks.py \
  --input /Users/sjarmak/harbor-10figure-dataset/tasks \
  --output benchmarks/10figure \
  --templates benchmarks/10figure/templates

# 2. Verify generation
ls benchmarks/10figure/ | head -5

# 3. Run a specific task
TASK_ID=$(ls benchmarks/10figure | head -1)
harbor run \
  --dockerfile benchmarks/10figure/$TASK_ID/environment/Dockerfile \
  --test-script benchmarks/10figure/$TASK_ID/tests/test.sh \
  --config benchmarks/10figure/$TASK_ID/task.toml

# 4. Check results
cat jobs/run-*/reward.txt
```

## Troubleshooting

### Tasks not found

```bash
# Verify corpus is accessible
ls -la /10figure/tasks/ | wc -l

# Check task YAML files are valid
find /10figure/tasks -name "*.yaml" -exec head -5 {} \;
```

### Generation fails

**Error:** "Template directory not found"
```bash
# Ensure templates exist
ls benchmarks/10figure/templates/test.sh.j2
```

**Error:** "ground_truth path not found"
```bash
# Check that ground_truth paths in task.yaml are absolute or relative to /10figure
grep ground_truth benchmarks/10figure/*/task.yaml
```

### Validation fails

**Error:** "Validator not found"
```bash
# Verify base image has validator
docker run harbor-10figure:base ls -la /10figure/scripts/validate_patch.py
```

**Error:** "Patch file empty"
```bash
# Agent made no changes; check agent command and instruction
cat benchmarks/10figure/<task_id>/instruction.md
```

## Integration with Benchmark Framework

### Task Schema Validation

All tasks are validated against the Task schema in `src/benchmark/task_schema.py`:

```bash
python tests/test_task_schema.py -v
```

### Result Aggregation

After running multiple tasks, aggregate results:

```bash
python runners/aggregator.py --runs jobs/ --output jobs/report.json
```

### Comparative Analysis

Compare performance across agents:

```bash
python runners/compare_results.py jobs/claude-baseline-* jobs/claude-mcp-*
```

## References

- **infrastructure/datasets.yaml** - Dataset contract definition
- **benchmarks/10figure/README.md** - Task generation guide
- **runners/gen_harbor_tasks.py** - Task generator source
- **benchmarks/10figure/templates/test.sh.j2** - Validation script template
- **docs/DEVELOPMENT.md** - Development setup and commands
- **AGENTS.md** - Agent implementation patterns
