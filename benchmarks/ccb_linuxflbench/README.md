# ccb_linuxflbench — Linux Kernel Fault Localization

Fault localization benchmark derived from [LinuxFLBench](https://github.com/FudanSELab/LinuxFLBench) (Fudan SELab).
Each task gives the agent a real bug report from bugzilla.kernel.org and asks it to identify the buggy file(s) and function(s) in the Linux kernel source tree (~28K files, ~11.5M LOC).

**Paper**: [LinuxFLBench: A Benchmark for Evaluating LLM-based Fault Localization in Linux Kernel](https://arxiv.org/abs/2505.19489)

## Docker Architecture: Pre-built Base Images

The Linux kernel is ~2GB even with `--filter=blob:none`. Cloning it inside every
Harbor run would add ~10 minutes per task per config. To avoid this, we use a
**two-layer Docker strategy**:

```
┌──────────────────────────────────────────┐
│  ccb-linux-base:v5.6.7   (base image)   │  ← built once, ~3-5GB
│  gcc:13 + tools + Claude CLI + kernel    │
└──────────────────────────────────────────┘
                    ▲
┌──────────────────────────────────────────┐
│  task Dockerfile        (thin overlay)   │  ← rebuilt per run, <1MB
│  COPY tests/ + chmod                     │
└──────────────────────────────────────────┘
```

**Base images** live in `base_images/` and contain everything expensive (toolchain,
Node.js, Claude CLI, kernel clone at a pinned commit). They are tagged
`ccb-linux-base:<kernel-version>`.

**Task Dockerfiles** (`{task_id}/environment/Dockerfile`) do `FROM ccb-linux-base:<ver>`
and only copy in the task-specific test harness. This makes task rebuilds instant.

### First-time setup

Before running any LinuxFLBench tasks, build the base images:

```bash
# Build all 5 base images (takes ~30-50 min total, one-time cost)
./benchmarks/ccb_linuxflbench/base_images/build_base_images.sh

# Or build just one version
./benchmarks/ccb_linuxflbench/base_images/build_base_images.sh v5.6.7
```

Verify they exist:

```bash
docker images 'ccb-linux-base'
```

### Adding a new task

1. Pick a task from `dataset/LINUXFLBENCH_dataset.jsonl` (250 entries).
2. Find the kernel version's commit hash:
   ```bash
   # Stable releases (v4.x.y, v5.x.y, etc.) are in gregkh/linux:
   curl -s https://api.github.com/repos/gregkh/linux/git/ref/tags/v<VERSION> \
     | jq -r .object.sha
   # If type=tag (annotated), dereference:
   curl -s https://api.github.com/repos/gregkh/linux/git/tags/<TAG_SHA> \
     | jq -r .object.sha
   # Release candidates (v*-rc*) are in torvalds/linux directly.
   ```
3. Add the version+commit to `base_images/build_base_images.sh` VERSIONS array.
4. Build the new base image: `./base_images/build_base_images.sh v<VERSION>`
5. Scaffold the task directory:
   ```
   benchmarks/ccb_linuxflbench/<task_id>/
   ├── task.toml
   ├── instruction.md
   ├── environment/
   │   └── Dockerfile          # FROM ccb-linux-base:v<VERSION>
   └── tests/
       └── test.sh
   ```
6. The task Dockerfile should be minimal — just `FROM` + `COPY tests/`.
7. Register the task in `configs/selected_benchmark_tasks.json`.

### Kernel version → base image mapping

| Task ID | Kernel | Base Image Tag | Commit |
|---------|--------|----------------|--------|
| lfl-acpi-207835 | v5.6.7 | `ccb-linux-base:v5.6.7` | `55b2af1c23eb` |
| lfl-wifi-206661 | v5.6-rc2 | `ccb-linux-base:v5.6-rc2` | `11a48a5a18c6` |
| lfl-nfs-117651 | v4.1.15 | `ccb-linux-base:v4.1.15` | `07cc49f66973` |
| lfl-sata-203475 | v4.14.114 | `ccb-linux-base:v4.14.114` | `fa5941f45d7e` |
| lfl-sound-53441 | v3.7.6 | `ccb-linux-base:v3.7.6` | `07c4ee001f13` |

## Task Structure

Each task evaluates fault localization: given a bug report, the agent must
produce `/workspace/fault_localization_result.json` with:

```json
{
  "buggy_files": ["drivers/acpi/video_detect.c"],
  "buggy_functions": ["video_detect_dmi_table"],
  "confidence": 0.8,
  "reasoning": "..."
}
```

### Scoring (10 points)

| Points | Check |
|--------|-------|
| 1 | Result file has `buggy_files` and `buggy_functions` fields |
| 4 | File-level: first predicted file matches ground truth exactly |
| 1 | File-level: ground-truth in top-5 predictions (only if not first) |
| 3 | Method-level: exact match on ground-truth function/struct |
| 1 | Reasoning provided (>10 chars) |
| 1 | Valid confidence score provided (float 0.0–1.0) |

Score is normalized to 0.0–1.0 and written to `/logs/verifier/reward.txt`.

## Running

```bash
# Pre-flight: build base images (one-time)
./benchmarks/ccb_linuxflbench/base_images/build_base_images.sh

# Run all 3 configs
./configs/linuxflbench_3config.sh

# Run only baseline
./configs/linuxflbench_3config.sh --baseline-only

# Single task via Harbor
harbor run --path benchmarks/ccb_linuxflbench/lfl-acpi-207835
```

## Source Dataset

The full LinuxFLBench dataset (250 tasks) is at:
https://github.com/FudanSELab/LinuxFLBench/blob/main/dataset/LINUXFLBENCH_dataset.jsonl

Each JSONL entry has fields: `id`, `title`, `description`, `patch`, `paths`
(ground-truth buggy files), `methods` (ground-truth buggy functions),
`Kernel Version`, `Product`, `Component`.
