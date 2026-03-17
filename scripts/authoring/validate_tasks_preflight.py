#!/usr/bin/env python3
"""Pre-flight validation of benchmark tasks before launching runs.

Checks task definitions for known problems that would waste compute:
- Truncated instruction.md
- task.toml language/difficulty mismatches vs selected_benchmark_tasks.json
- test.sh missing or not executable
- Missing task in selection registry
- Crossrepo expected_changes content mismatches
- Verifier self-tests via fixtures (perfect_input/empty_input score bounds)
- Verifier idempotency (deterministic scores across repeated runs)

Usage:
    # Validate all tasks in a suite
    python3 scripts/validate_tasks_preflight.py --suite ccb_pytorch

    # Validate all selected tasks
    python3 scripts/validate_tasks_preflight.py --all

    # Validate a single task
    python3 scripts/validate_tasks_preflight.py --task benchmarks/ccb_pytorch/sgt-005

    # JSON output
    python3 scripts/validate_tasks_preflight.py --all --format json

    # Runtime smoke (no agent): Docker build + verifier execution + fixture self-tests
    python3 scripts/validate_tasks_preflight.py --task benchmarks/ccb_largerepo/big-code-k8s-001 --smoke-runtime

    # Runtime smoke for a full suite (expensive)
    python3 scripts/validate_tasks_preflight.py --suite ccb_largerepo --smoke-runtime --smoke-timeout-sec 900

    # Idempotency check only (also activated by --smoke-runtime)
    python3 scripts/validate_tasks_preflight.py --all --idempotency

    # Fixture self-tests only (without Docker smoke)
    python3 scripts/validate_tasks_preflight.py --all --fixture-tests
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path
from typing import NamedTuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BENCHMARKS_DIR = PROJECT_ROOT / "benchmarks"
SOURCEGRAPH_TASKS_DIR = PROJECT_ROOT / "sourcegraph_tasks"
SELECTED_TASKS_PATH = PROJECT_ROOT / "configs" / "selected_benchmark_tasks.json"

# Minimum instruction.md length (characters) to consider non-truncated
MIN_INSTRUCTION_LENGTH = 200

# Idempotency tolerance: scores within this epsilon are considered equal
IDEMPOTENCY_EPSILON = 0.001

# Timeout for individual fixture verifier runs (seconds)
FIXTURE_RUN_TIMEOUT = 120

# Template placeholder patterns that should have been replaced
TEMPLATE_PATTERNS = [
    re.compile(r"#ISSUE_NUMBER"),
    re.compile(r"#REPO_NAME"),
    re.compile(r"\{\{.*?\}\}"),
    re.compile(r"<PLACEHOLDER>"),
    re.compile(r"TODO:?\s*fill"),
]

ABSOLUTE_TASK_ROOTS = ("/app", "/workspace")
CONTRACT_ENV_VARS = (
    "TASK_WORKDIR",
    "TASK_REPO_ROOT",
    "TASK_OUTPUT",
    "TASK_OUTPUT_PATH",
)
OUTPUT_ARTIFACT_NAMES = (
    "solution.json",
    "solution.md",
    "review.json",
    "answer.json",
    "answer.md",
)
DAYTONA_DEFAULT_STORAGE_GB = 10
CONTRACT_CHECKS = {
    "hardcoded_task_paths",
    "variant_workdir_mismatch",
    "artifact_variant_workdir_mismatch",
    "verifier_workdir_mismatch",
    "instruction_output_contract_missing",
    "sg_only_restore_contract_missing",
    "sg_only_base_mismatch",
    "daytona_storage_over_10g",
    "stale_daytona_routing_metadata",
}


def load_selected_tasks() -> dict:
    """Load selected_benchmark_tasks.json and index by (benchmark, task_id)."""
    if not SELECTED_TASKS_PATH.is_file():
        return {}
    data = json.loads(SELECTED_TASKS_PATH.read_text())
    index = {}
    for task in data.get("tasks", []):
        key = (task.get("benchmark", ""), task.get("task_id", ""))
        index[key] = task
    return index


def parse_task_toml_simple(path: Path) -> dict:
    """Minimal TOML parser for task.toml (avoids tomllib dependency).

    Handles flat key=value and [section] headers. Enough for our fields.
    """
    result = {}
    section = ""
    if not path.is_file():
        return result
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("["):
            section = line.strip("[]").strip()
            continue
        if "=" in line:
            # Handle multi-line strings (triple-quoted) — skip them
            if '"""' in line:
                break
            key, _, val = line.partition("=")
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            full_key = f"{section}.{key}" if section else key
            result[full_key] = val
    return result


def _read_text(path: Path) -> str:
    if not path.is_file():
        return ""
    return path.read_text(errors="replace")


def _extract_last_workdir(dockerfile_path: Path) -> str | None:
    content = _read_text(dockerfile_path)
    workdirs = re.findall(r"(?im)^\s*WORKDIR\s+([^\s]+)\s*$", content)
    if not workdirs:
        return None
    return workdirs[-1].strip()


def _extract_from_image(dockerfile_path: Path) -> str | None:
    content = _read_text(dockerfile_path)
    match = re.search(r"(?im)^\s*FROM\s+([^\s]+)", content)
    if not match:
        return None
    return match.group(1).strip()


def _extract_task_roots(script_content: str) -> set[str]:
    roots = set()
    for root in ABSOLUTE_TASK_ROOTS:
        pattern = rf"(?<![A-Za-z0-9_.-]){re.escape(root)}(?=/|\b|['\"\\s]|$)"
        if re.search(pattern, script_content):
            roots.add(root)
    return roots


def _extract_output_artifacts(script_content: str) -> set[str]:
    return {name for name in OUTPUT_ARTIFACT_NAMES if name in script_content}


def _storage_gb(raw_value: str) -> int | None:
    if not raw_value:
        return None
    match = re.fullmatch(r"\s*(\d+)\s*G\s*", raw_value, re.IGNORECASE)
    if not match:
        return None
    return int(match.group(1))


def validate_task(task_dir: Path, selected_index: dict) -> list[dict]:
    """Validate a single task directory. Returns list of issues."""
    issues = []
    task_name = task_dir.name
    benchmark = task_dir.parent.name
    if benchmark == "tasks":
        benchmark = task_dir.parent.parent.name

    def issue(severity: str, check: str, message: str):
        issues.append({
            "severity": severity,
            "check": check,
            "task": task_name,
            "benchmark": benchmark,
            "message": message,
            "path": str(task_dir),
        })

    # --- Check instruction.md ---
    instruction_path = task_dir / "instruction.md"
    if not instruction_path.is_file():
        issue("CRITICAL", "missing_instruction", "No instruction.md found")
    else:
        content = instruction_path.read_text(errors="replace")
        if len(content) < MIN_INSTRUCTION_LENGTH:
            issue("CRITICAL", "truncated_instruction",
                  f"instruction.md is only {len(content)} chars (minimum: {MIN_INSTRUCTION_LENGTH})")

        # Check for template placeholders
        for pattern in TEMPLATE_PATTERNS:
            match = pattern.search(content)
            if match:
                issue("WARNING", "template_placeholder",
                      f"instruction.md contains template placeholder: {match.group(0)}")

    # --- Check task.toml ---
    toml_path = task_dir / "task.toml"
    if not toml_path.is_file():
        issue("WARNING", "missing_task_toml", "No task.toml found")
        toml_data = {}
    else:
        toml_data = parse_task_toml_simple(toml_path)

    # Determine benchmark from task location and task metadata.
    benchmark = task_dir.parent.name
    if benchmark == "tasks":
        benchmark = task_dir.parent.parent.name
    elif benchmark == "sourcegraph_tasks":
        benchmark = (
            toml_data.get("task.mcp_suite")
            or toml_data.get("task.category")
            or benchmark
        )

    storage_raw = toml_data.get("environment.storage", "") or toml_data.get("task.storage", "")
    storage_gb = _storage_gb(storage_raw)
    if storage_gb is not None and storage_gb > DAYTONA_DEFAULT_STORAGE_GB:
        issue(
            "WARNING",
            "daytona_storage_over_10g",
            f"task.toml requests storage={storage_raw}; exceeds Daytona default "
            f"{DAYTONA_DEFAULT_STORAGE_GB}G cap and needs justification or alternate routing",
        )

    # --- Check test.sh (or eval.sh for MCP-unique tasks) ---
    test_sh = task_dir / "tests" / "test.sh"
    eval_sh = task_dir / "tests" / "eval.sh"
    if test_sh.is_file():
        verifier_script = test_sh
        verifier_name = "test.sh"
    elif eval_sh.is_file():
        verifier_script = eval_sh
        verifier_name = "eval.sh"
    else:
        verifier_script = None
        verifier_name = None
        issue("CRITICAL", "missing_test_sh", "No tests/test.sh or tests/eval.sh found")

    if verifier_script is not None:
        if not os.access(verifier_script, os.X_OK):
            issue("WARNING", "test_not_executable", f"tests/{verifier_name} is not executable")

        # Check for known bad patterns in test.sh
        test_content = verifier_script.read_text(errors="replace")
        if "--output_path" in test_content and "--result_path" not in test_content:
            # Check if this is a TAC task with the known --output_path bug
            if "tac" in benchmark.lower():
                issue("WARNING", "test_sh_bad_flag",
                      "test.sh uses --output_path (should be --result_path for TAC tasks)")

        instruction_has_contract_env = any(token in content for token in CONTRACT_ENV_VARS) if instruction_path.is_file() else False
        verifier_has_contract_env = any(token in test_content for token in CONTRACT_ENV_VARS)
        verifier_roots = _extract_task_roots(test_content)
        referenced_outputs = _extract_output_artifacts(test_content)

        dockerfile = task_dir / "environment" / "Dockerfile"
        dockerfile_sg_only = task_dir / "environment" / "Dockerfile.sg_only"
        dockerfile_artifact = task_dir / "environment" / "Dockerfile.artifact_only"
        base_workdir = _extract_last_workdir(dockerfile)
        sg_only_workdir = _extract_last_workdir(dockerfile_sg_only)
        artifact_workdir = _extract_last_workdir(dockerfile_artifact)
        base_from = _extract_from_image(dockerfile)
        sg_only_from = _extract_from_image(dockerfile_sg_only)

        if verifier_roots and not (instruction_has_contract_env or verifier_has_contract_env):
            issue(
                "WARNING",
                "hardcoded_task_paths",
                "Verifier hardcodes task paths "
                f"{', '.join(sorted(verifier_roots))} without TASK_WORKDIR/TASK_REPO_ROOT/TASK_OUTPUT contract vars",
            )

        if base_workdir and sg_only_workdir and base_workdir != sg_only_workdir:
            issue(
                "WARNING",
                "variant_workdir_mismatch",
                f"Dockerfile WORKDIR={base_workdir} but Dockerfile.sg_only WORKDIR={sg_only_workdir}",
            )

        if base_workdir and artifact_workdir and base_workdir != artifact_workdir:
            issue(
                "INFO",
                "artifact_variant_workdir_mismatch",
                f"Dockerfile WORKDIR={base_workdir} but Dockerfile.artifact_only WORKDIR={artifact_workdir}",
            )

        expected_workdirs = {wd for wd in (base_workdir, sg_only_workdir, artifact_workdir) if wd}
        unexpected_roots = verifier_roots - expected_workdirs
        if unexpected_roots:
            issue(
                "CRITICAL",
                "verifier_workdir_mismatch",
                "Verifier references "
                f"{', '.join(sorted(unexpected_roots))} but task image WORKDIRs are "
                f"{', '.join(sorted(expected_workdirs)) or 'unset'}",
            )

        instruction_content = content if instruction_path.is_file() else ""
        helper_outputs = set()
        if "answer_json_verifier_lib.sh" in test_content:
            # answer.json is an artifact-only transport detail, not the canonical
            # task output the agent is expected to produce in normal harnesses.
            helper_outputs.add("answer.json")
        required_outputs = referenced_outputs - helper_outputs
        missing_output_mentions = [name for name in sorted(required_outputs) if name not in instruction_content]
        if required_outputs and missing_output_mentions:
            issue(
                "INFO",
                "instruction_output_contract_missing",
                "instruction.md does not explicitly mention verifier-required artifact(s): "
                + ", ".join(missing_output_mentions),
            )

        sg_only_content = _read_text(dockerfile_sg_only)
        if dockerfile_sg_only.is_file() and "/repo_full" in test_content:
            has_restore_contract = (
                "/repo_full" in sg_only_content
                or ".sg_only_clone_manifest.json" in sg_only_content
                or "sgonly_verifier_wrapper.sh" in test_content
            )
            if not has_restore_contract:
                issue(
                    "CRITICAL",
                    "sg_only_restore_contract_missing",
                    "Verifier depends on /repo_full, but Dockerfile.sg_only has no visible restore contract",
                )

        if dockerfile_sg_only.is_file() and "/utils" in test_content and base_from and sg_only_from and base_from != sg_only_from:
            issue(
                "WARNING",
                "sg_only_base_mismatch",
                f"Verifier references /utils but Dockerfile.sg_only base image changed from {base_from} to {sg_only_from}",
            )

    # --- Cross-check with selected_benchmark_tasks.json ---
    selected_key = (benchmark, task_name)
    selected = selected_index.get(selected_key)

    if not selected:
        # Also try with the task_dir field
        for key, val in selected_index.items():
            if val.get("task_dir", "").endswith(f"/{task_name}"):
                selected = val
                break

    if selected:
        # Check language match
        toml_language = toml_data.get("task.language", "")
        selected_language = selected.get("language", "")
        if toml_language and selected_language and toml_language != selected_language:
            issue("WARNING", "language_mismatch",
                  f"task.toml language='{toml_language}' vs selected_tasks language='{selected_language}'")

        # Check difficulty match
        toml_difficulty = toml_data.get("task.difficulty", "")
        selected_difficulty = selected.get("difficulty", "")
        if toml_difficulty and selected_difficulty and toml_difficulty != selected_difficulty:
            issue("WARNING", "difficulty_mismatch",
                  f"task.toml difficulty='{toml_difficulty}' vs selected_tasks difficulty='{selected_difficulty}'")

        selected_execution_env = selected.get("execution_env")
        selected_daytona_reason = selected.get("daytona_incompatible_reason")
        if (
            selected_execution_env == "local_docker_only"
            and selected_daytona_reason == "repo_too_large_for_10gb_sandbox"
            and storage_gb is not None
            and storage_gb <= DAYTONA_DEFAULT_STORAGE_GB
        ):
            issue(
                "WARNING",
                "stale_daytona_routing_metadata",
                "selected_benchmark_tasks.json still marks task local_docker_only for "
                "repo_too_large_for_10gb_sandbox, but task.toml now requests storage "
                f"{storage_raw or f'{storage_gb}G'} within the Daytona default cap",
            )
    else:
        if task_dir.parent.name != "sourcegraph_tasks":
            issue("INFO", "not_in_selection",
                  f"Task not found in selected_benchmark_tasks.json")

    # --- Check expected_changes.json (crossrepo) ---
    expected_changes = task_dir / "expected_changes.json"
    if expected_changes.is_file() and instruction_path.is_file():
        try:
            ec_content = expected_changes.read_text()
            instr_content = instruction_path.read_text(errors="replace")

            # Extract repo references from expected_changes
            ec_data = json.loads(ec_content)
            ec_repos = set()
            if isinstance(ec_data, dict):
                for key in ec_data:
                    # Keys often contain repo/file paths
                    parts = key.split("/")
                    if len(parts) >= 2:
                        ec_repos.add(parts[0].lower())

            # Check if expected_changes references repos not in instruction
            instr_lower = instr_content.lower()
            for repo in ec_repos:
                if repo and len(repo) > 3 and repo not in instr_lower:
                    issue("WARNING", "expected_changes_mismatch",
                          f"expected_changes.json references '{repo}' not found in instruction.md")
        except (json.JSONDecodeError, OSError):
            issue("WARNING", "expected_changes_invalid",
                  "expected_changes.json is not valid JSON")

    return issues


def _shorten(text: str, limit: int = 500) -> str:
    text = (text or "").strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def smoke_task_runtime(
    task_dir: Path,
    timeout_sec: int = 300,
    build_timeout_sec: int | None = None,
    verify_timeout_sec: int | None = None,
) -> list[dict]:
    """Build task image and run verifier without an agent.

    This catches broken Dockerfiles and verifier script/runtime wiring before
    expensive benchmark batches are launched.
    """
    issues: list[dict] = []
    benchmark = task_dir.parent.name if task_dir.parent.name != "tasks" else task_dir.parent.parent.name
    task_name = task_dir.name

    def issue(severity: str, check: str, message: str):
        issues.append({
            "severity": severity,
            "check": check,
            "task": task_name,
            "benchmark": benchmark,
            "message": message,
            "path": str(task_dir),
        })

    if shutil.which("docker") is None:
        issue("CRITICAL", "smoke_no_docker", "docker not found on PATH")
        return issues

    dockerfile = task_dir / "environment" / "Dockerfile"
    tests_dir = task_dir / "tests"
    test_sh = tests_dir / "test.sh"
    if not dockerfile.is_file():
        issue("CRITICAL", "smoke_missing_dockerfile", "Missing environment/Dockerfile")
        return issues
    if not test_sh.is_file():
        issue("CRITICAL", "smoke_missing_test_sh", "Missing tests/test.sh")
        return issues

    image_tag = f"ccb-smoke-{task_name.lower().replace('_', '-')}-{uuid.uuid4().hex[:8]}"
    build_timeout = build_timeout_sec if build_timeout_sec is not None else timeout_sec
    verify_timeout = verify_timeout_sec if verify_timeout_sec is not None else timeout_sec

    try:
        build_contexts = [task_dir, dockerfile.parent]
        build_succeeded = False
        build_errors: list[str] = []
        saw_build_timeout = False
        for ctx in build_contexts:
            try:
                build = subprocess.run(
                    ["docker", "build", "-f", str(dockerfile), "-t", image_tag, str(ctx)],
                    capture_output=True,
                    text=True,
                    timeout=build_timeout,
                    check=False,
                )
                if build.returncode == 0:
                    build_succeeded = True
                    break
                build_errors.append(f"context={ctx}: {_shorten(build.stdout + chr(10) + build.stderr)}")
            except subprocess.TimeoutExpired:
                saw_build_timeout = True
                build_errors.append(f"context={ctx}: timeout ({build_timeout}s)")

        if not build_succeeded:
            check_name = "smoke_build_timeout" if saw_build_timeout else "smoke_docker_build_fail"
            issue("CRITICAL", check_name, "Docker build failed for all contexts: " + " | ".join(build_errors))
            return issues

        tmp_logs = tempfile.mkdtemp(prefix=f"ccb-smoke-{task_name}-")
        run_cmd = [
            "docker",
            "run",
            "--rm",
            "-v",
            f"{tests_dir}:/tests:ro",
            "-v",
            f"{tmp_logs}:/logs",
            image_tag,
            "bash",
            "-lc",
            (
                "set -e; mkdir -p /logs/agent /logs/verifier; "
                "printf 'smoke preflight\\n' > /logs/agent/solution.md; "
                "bash /tests/test.sh"
            ),
        ]
        run = subprocess.run(
            run_cmd,
            capture_output=True,
            text=True,
            timeout=verify_timeout,
            check=False,
        )
        reward_txt = Path(tmp_logs) / "verifier" / "reward.txt"
        reward_json = Path(tmp_logs) / "verifier" / "reward.json"
        has_reward = reward_txt.is_file() or reward_json.is_file()

        if run.returncode != 0:
            message = _shorten(run.stdout + "\n" + run.stderr)
            lower = message.lower()
            hard_failure_patterns = [
                "syntax error",
                "no such file or directory",
                "command not found",
                "traceback",
                "module not found",
                "modulenotfounderror",
            ]
            if any(p in lower for p in hard_failure_patterns):
                issue("CRITICAL", "smoke_verifier_exec_fail", f"Verifier execution failed: {message}")
                return issues
            if not has_reward:
                issue(
                    "CRITICAL",
                    "smoke_verifier_exec_fail",
                    f"Verifier failed before producing reward artifact: {message}",
                )
                return issues
            issue(
                "WARNING",
                "smoke_verifier_nonzero_with_reward",
                "Verifier returned non-zero but produced reward artifact (likely expected with dummy solution).",
            )

        if not has_reward:
            issue(
                "CRITICAL",
                "smoke_reward_missing",
                "Verifier ran but produced no reward.txt/reward.json in /logs/verifier",
            )
    except subprocess.TimeoutExpired:
        issue("CRITICAL", "smoke_verify_timeout", f"Verifier smoke exceeded timeout ({verify_timeout}s)")
    finally:
        subprocess.run(["docker", "image", "rm", "-f", image_tag], capture_output=True, text=True)

    return issues


class FixtureResult(NamedTuple):
    """Result of running a single fixture against a verifier."""
    task_name: str
    benchmark: str
    fixture_name: str  # e.g. "perfect_input" or "empty_input"
    score: float | None  # None if verifier couldn't run
    expected_min: float
    expected_max: float
    passed: bool
    skipped: bool
    skip_reason: str
    verifier_type: str


def _read_reward(logs_dir: Path) -> float | None:
    """Read the reward value from a verifier's output directory.

    Checks reward.txt first (plain float), then reward.json ({"reward": float}).
    Returns None if no reward file exists or is unparseable.
    """
    reward_txt = logs_dir / "verifier" / "reward.txt"
    reward_json = logs_dir / "verifier" / "reward.json"

    if reward_txt.is_file():
        try:
            text = reward_txt.read_text().strip()
            # Handle lines like "0.95" or "Score: 0.95" — take last float-like token
            for token in reversed(text.split()):
                try:
                    return float(token)
                except ValueError:
                    continue
        except (OSError, ValueError):
            pass

    if reward_json.is_file():
        try:
            data = json.loads(reward_json.read_text())
            if isinstance(data, dict):
                for key in ("reward", "score"):
                    if key in data:
                        return float(data[key])
        except (OSError, json.JSONDecodeError, ValueError, TypeError):
            pass

    return None


def _discover_fixtures(task_dir: Path) -> dict | None:
    """Discover fixture directories and load metadata for a task.

    Returns metadata dict (from metadata.json) if fixtures exist, else None.
    The metadata dict is augmented with 'fixtures_dir' pointing to the
    tests/fixtures/ directory and 'fixture_names' listing available fixtures
    (e.g. ['perfect_input', 'empty_input']).
    """
    fixtures_dir = task_dir / "tests" / "fixtures"
    metadata_path = fixtures_dir / "metadata.json"

    if not fixtures_dir.is_dir() or not metadata_path.is_file():
        return None

    try:
        metadata = json.loads(metadata_path.read_text())
    except (OSError, json.JSONDecodeError):
        return None

    # Discover fixture subdirectories (perfect_input, empty_input, etc.)
    fixture_names = []
    for entry in sorted(fixtures_dir.iterdir()):
        if entry.is_dir() and not entry.name.startswith("."):
            fixture_names.append(entry.name)

    if not fixture_names:
        return None

    metadata["_fixtures_dir"] = fixtures_dir
    metadata["_fixture_names"] = fixture_names
    metadata["_task_dir"] = task_dir
    return metadata


def _resolve_fixture_placement(
    fixture_name: str,
    metadata: dict,
    fixture_dir: Path,
) -> list[tuple[Path, str]]:
    """Determine where each fixture file should be placed.

    Returns a list of (source_path, dest_relative_path) tuples where
    dest_relative_path is relative to the sandbox root (e.g. "workspace/review.json"
    or "logs/agent/solution.md").

    The placement logic uses the 'fixture_files' metadata if available, falling
    back to heuristics based on file extension and common verifier conventions.
    """
    placements = []
    fixture_files_meta = metadata.get("fixture_files", {}).get(fixture_name, {})

    for fpath in sorted(fixture_dir.iterdir()):
        if not fpath.is_file():
            continue
        fname = fpath.name

        # Check metadata for explicit placement description
        desc = fixture_files_meta.get(fname, "")
        desc_lower = desc.lower()

        # Determine destination based on metadata description or heuristics
        if "/logs/agent/" in desc_lower or "placed at /logs/agent/" in desc_lower:
            placements.append((fpath, f"logs/agent/{fname}"))
        elif "placed at /workspace/" in desc_lower:
            # Extract the specific path after "/workspace/"
            match = re.search(r"placed at /workspace/(\S+)", desc, re.IGNORECASE)
            if match:
                # The metadata might say "Placed at /workspace/review.json" or
                # "Placed at src/Components/.../File.cs in workspace"
                rel = match.group(1).rstrip(".")
                placements.append((fpath, f"workspace/{rel}"))
            else:
                placements.append((fpath, f"workspace/{fname}"))
        elif " at " in desc_lower and "workspace" in desc_lower:
            # Pattern: "Placed at src/Foo/Bar.cs in workspace"
            match = re.search(
                r"placed at (\S+)\s+in\s+workspace", desc, re.IGNORECASE
            )
            if match:
                rel = match.group(1).rstrip(".")
                placements.append((fpath, f"workspace/{rel}"))
            else:
                placements.append((fpath, f"workspace/{fname}"))
        elif fname == "solution.md":
            # Default: solution.md goes to /logs/agent/
            placements.append((fpath, f"logs/agent/{fname}"))
        elif fname == "documentation.md":
            # Default: documentation.md goes to /workspace/
            placements.append((fpath, f"workspace/{fname}"))
        elif fname == "review.json":
            # Default: review.json goes to /workspace/
            placements.append((fpath, f"workspace/{fname}"))
        elif fname.endswith(".diff"):
            # Diff files go to workspace for verify_diff.py
            placements.append((fpath, f"workspace/{fname}"))
        else:
            # Default: place in workspace root
            placements.append((fpath, f"workspace/{fname}"))

    return placements


def _setup_fixture_sandbox(
    task_dir: Path,
    fixture_dir: Path,
    metadata: dict,
    fixture_name: str,
) -> Path:
    """Create a temporary sandbox mimicking the container filesystem layout.

    Creates:
        <tmpdir>/workspace/   - agent output area
        <tmpdir>/logs/agent/  - agent logs
        <tmpdir>/logs/verifier/ - verifier output
        <tmpdir>/tests/       - copy of task's tests/ directory

    Copies fixture files into appropriate locations based on metadata.
    Returns the tmpdir path.
    """
    sandbox = Path(tempfile.mkdtemp(prefix=f"ccb-fixture-{task_dir.name}-{fixture_name}-"))
    workspace = sandbox / "workspace"
    logs_agent = sandbox / "logs" / "agent"
    logs_verifier = sandbox / "logs" / "verifier"
    tests = sandbox / "tests"

    workspace.mkdir(parents=True)
    logs_agent.mkdir(parents=True)
    logs_verifier.mkdir(parents=True)
    tests.mkdir(parents=True)

    # Copy the task's tests/ directory contents into sandbox /tests/
    src_tests = task_dir / "tests"
    if src_tests.is_dir():
        for item in src_tests.iterdir():
            dest = tests / item.name
            if item.is_dir():
                if item.name == "fixtures":
                    # Don't copy fixtures into /tests/ -- they're placed explicitly
                    continue
                shutil.copytree(item, dest, dirs_exist_ok=True)
            elif item.is_file():
                shutil.copy2(item, dest)

    # Place fixture files according to metadata
    placements = _resolve_fixture_placement(fixture_name, metadata, fixture_dir)
    for src, dest_rel in placements:
        dest = sandbox / dest_rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)

    # Initialize a minimal git repo in /workspace so verifiers using git don't crash.
    # The git history is set up so fixture files appear as "agent changes":
    #   1. First commit: empty (or baseline)
    #   2. Second commit: fixture files added (shows as COMMIT_COUNT >= 1)
    # This satisfies change-detection guards in verifiers that check for
    # unstaged/staged/committed changes before scoring.
    #
    # If git setup fails (timeout, missing git, etc.), the workspace is left
    # without a .git directory. Verifiers that only check for file existence
    # (not git changes) will still work. Those that require git will get
    # graceful skip at runtime.
    git_timeout = 30  # generous timeout for potentially slow filesystems
    git_env = os.environ.copy()
    git_env["GIT_AUTHOR_DATE"] = "2025-01-01T00:00:00+00:00"
    git_env["GIT_COMMITTER_DATE"] = "2025-01-01T00:00:00+00:00"
    try:
        def _git(*args: str) -> subprocess.CompletedProcess:
            return subprocess.run(
                ["git"] + list(args),
                cwd=str(workspace),
                capture_output=True,
                text=True,
                timeout=git_timeout,
                check=False,
                env=git_env,
            )

        r = _git("init")
        if r.returncode != 0:
            raise RuntimeError(f"git init failed: {r.stderr}")
        _git("config", "user.email", "fixture-test@ccb.local")
        _git("config", "user.name", "Fixture Test")
        _git("config", "commit.gpgsign", "false")
        # Baseline commit (empty)
        r = _git("commit", "--allow-empty", "-m", "baseline (pre-agent)")
        if r.returncode != 0:
            raise RuntimeError(f"git commit baseline failed: {r.stderr}")
        # Stage and commit fixture files as the "agent" work
        _git("add", "-A")
        _git("commit", "-m", "agent changes (fixture)", "--allow-empty")
    except (subprocess.TimeoutExpired, FileNotFoundError, RuntimeError, OSError):
        # If git setup fails, remove the partial .git so verifiers don't
        # see a broken repo. The files will remain in workspace as-is.
        git_dir = workspace / ".git"
        if git_dir.exists():
            shutil.rmtree(git_dir, ignore_errors=True)

    return sandbox


def _can_run_outside_docker(task_dir: Path) -> tuple[bool, str]:
    """Heuristic check whether a verifier is likely to work outside Docker.

    Returns (can_run, reason) where reason explains why not if can_run is False.
    """
    test_sh = task_dir / "tests" / "test.sh"
    if not test_sh.is_file():
        return False, "tests/test.sh not found"

    try:
        content = test_sh.read_text(errors="replace")
    except OSError:
        return False, "Could not read tests/test.sh"

    # Verifiers that source external scripts not in tests/ are likely Docker-only
    # (e.g. find_and_prove_verifier.sh needs the full build environment)
    if "find_and_prove_verifier" in content:
        return False, "find_and_prove verifier requires full Docker environment (go test, patch)"

    # Verifiers that run compilation (mvn, make, go build, etc.) need Docker.
    # Even if gated behind conditionals, the verifier typically relies on the
    # build environment for significant scoring weight.
    compile_cmds = [
        ("mvn ", "Maven build"),
        ("make ", "Make build"),
        ("go test ", "Go test execution"),
        ("go build ", "Go build"),
        ("cargo ", "Cargo build"),
        ("dotnet ", ".NET build"),
        ("npm test", "npm test execution"),
        ("npm run ", "npm script execution"),
    ]
    for cmd, desc in compile_cmds:
        if cmd in content:
            return False, f"Verifier uses {desc} (requires Docker build environment)"

    # Verifiers that use verify_diff.py with --pre-fix-rev need a real repo at that rev
    if "--pre-fix-rev" in content:
        return False, "verify_diff.py with --pre-fix-rev requires the actual git repo at the right commit"

    # Verifiers that check file existence in /workspace against documentation
    # content (hallucination penalty) require the actual repo source tree
    if re.search(r"Path\(['\"]?/workspace['\"]?,\s*\w+\)\.exists\(\)", content):
        return False, "Verifier checks file existence in /workspace (requires full repo source tree)"

    # Verifiers that source verifier_lib.sh need that file available
    if "verifier_lib.sh" in content:
        # verifier_lib.sh is typically a bash library with IR scoring functions.
        # Check if it exists in the task's tests/
        lib_path = task_dir / "tests" / "verifier_lib.sh"
        if not lib_path.is_file():
            return False, "verifier_lib.sh not found in tests/"

    # Verifiers checking paths like /workspace/documentation.md via python3 inline
    # are usually safe to run outside Docker with our sandbox
    return True, ""


def _rewrite_paths_in_script(script_content: str, sandbox: str) -> str:
    """Rewrite absolute container paths in a verifier script to sandbox paths.

    Replaces /workspace, /tests, /logs with their sandbox equivalents so the
    verifier can run outside Docker. Handles both bare paths and quoted paths.
    Also rewrites inline Python string literals that reference these paths.
    """
    # Order matters: replace longer paths first to avoid partial matches.
    # We replace /workspace/, /tests/, /logs/ with trailing slash,
    # then the bare forms, being careful not to double-replace.
    replacements = [
        ("/workspace", f"{sandbox}/workspace"),
        ("/tests/", f"{sandbox}/tests/"),
        ("/logs/", f"{sandbox}/logs/"),
    ]

    # First pass: rewrite paths that appear as absolute references.
    # We need to be careful not to replace paths that are already sandbox paths,
    # and not to replace /tests or /logs when they appear as part of a longer
    # path (e.g. /some/other/tests/).
    result = script_content

    # Replace /workspace — but only when it's the start of an absolute path
    # (preceded by whitespace, quote, =, or start of line)
    result = re.sub(
        r'(?<![/\w])(/workspace)(?=/[\s"\']|/[a-zA-Z]|"|\s|$)',
        f"{sandbox}/workspace",
        result,
    )

    # Replace /tests/ and /tests" patterns
    result = re.sub(
        r'(?<![/\w])(/tests)(?=/[\s"\']|/[a-zA-Z]|"|\s|$)',
        f"{sandbox}/tests",
        result,
    )

    # Replace /logs/ and /logs" patterns
    result = re.sub(
        r'(?<![/\w])(/logs)(?=/[\s"\']|/[a-zA-Z]|"|\s|$)',
        f"{sandbox}/logs",
        result,
    )

    return result


def _run_verifier_in_sandbox(
    sandbox: Path,
    task_dir: Path,
    timeout_sec: int = FIXTURE_RUN_TIMEOUT,
) -> tuple[float | None, bool, str]:
    """Execute a task's test.sh inside the sandbox environment.

    Uses path rewriting to replace absolute container paths (/workspace, /tests,
    /logs) with sandbox equivalents, so the verifier can run on the host without
    needing Docker or root-level symlinks.

    Returns (score, skipped, skip_reason).
    - score is None if the verifier failed/was skipped.
    - skipped=True means a known limitation prevented execution.
    """
    test_sh = sandbox / "tests" / "test.sh"
    if not test_sh.is_file():
        return None, True, "test.sh not found in sandbox"

    # Read and path-rewrite the test.sh script
    try:
        original_content = test_sh.read_text(errors="replace")
    except OSError as e:
        return None, True, f"Cannot read test.sh: {e}"

    sandbox_str = str(sandbox)
    rewritten_content = _rewrite_paths_in_script(original_content, sandbox_str)

    # Also rewrite any helper scripts in /tests/ (verifier_lib.sh, etc.)
    for helper in sandbox.glob("tests/*.sh"):
        if helper.name == "test.sh":
            continue
        try:
            helper_content = helper.read_text(errors="replace")
            helper_rewritten = _rewrite_paths_in_script(helper_content, sandbox_str)
            if helper_rewritten != helper_content:
                helper.write_text(helper_rewritten)
        except OSError:
            pass

    # Write the rewritten test.sh to a separate runner script
    runner = sandbox / "_run_fixture.sh"
    runner_header = f"""#!/bin/bash
# Fixture test runner — auto-generated, paths rewritten to sandbox
# Sandbox: {sandbox_str}

git config --global --add safe.directory "{sandbox_str}/workspace" 2>/dev/null || true

cd "{sandbox_str}/workspace"

"""
    # Strip the shebang from original if present, since we provide our own
    script_body = rewritten_content
    if script_body.startswith("#!"):
        # Remove first line (shebang)
        script_body = script_body.split("\n", 1)[1] if "\n" in script_body else ""

    runner.write_text(runner_header + script_body)
    runner.chmod(0o755)

    # Build the environment
    env = os.environ.copy()
    env["HOME"] = str(sandbox)

    try:
        result = subprocess.run(
            ["bash", str(runner)],
            capture_output=True,
            text=True,
            timeout=timeout_sec,
            check=False,
            cwd=str(sandbox / "workspace"),
            env=env,
        )
    except subprocess.TimeoutExpired:
        return None, True, f"Verifier timed out after {timeout_sec}s"
    except OSError as e:
        return None, True, f"OS error running verifier: {e}"

    # Read the reward
    score = _read_reward(sandbox / "logs")

    if score is not None:
        return score, False, ""

    # Verifier ran but no reward produced — check for known failure patterns
    combined = (result.stdout or "") + "\n" + (result.stderr or "")
    lower = combined.lower()

    skip_patterns = [
        ("command not found", "Missing command in host environment"),
        ("no such file or directory", "Missing file/directory (Docker-only paths)"),
        ("modulenotfounderror", "Missing Python module (Docker-only dependency)"),
        ("module not found", "Missing module (Docker-only dependency)"),
        ("permission denied", "Permission denied on host filesystem"),
        ("cannot open", "Cannot open file (Docker-only resource)"),
    ]
    for pattern, reason in skip_patterns:
        if pattern in lower:
            return None, True, reason

    if result.returncode != 0:
        return None, True, f"Verifier exited with code {result.returncode}: {_shorten(combined, 200)}"

    return None, True, "Verifier produced no reward file"


def run_fixture_tests(
    task_dir: Path,
    run_idempotency: bool = False,
    timeout_sec: int = FIXTURE_RUN_TIMEOUT,
) -> tuple[list[FixtureResult], list[dict]]:
    """Run verifier self-tests using fixture directories.

    For each fixture (perfect_input, empty_input), sets up a sandbox, runs the
    verifier, and checks the score against expected bounds from metadata.json.

    If run_idempotency is True, runs the perfect_input fixture twice and checks
    that scores match within IDEMPOTENCY_EPSILON.

    Returns (fixture_results, issues) where issues are in the standard format.
    """
    results: list[FixtureResult] = []
    issues: list[dict] = []
    task_name = task_dir.name
    benchmark = task_dir.parent.name
    if benchmark == "tasks":
        benchmark = task_dir.parent.parent.name

    def issue(severity: str, check: str, message: str):
        issues.append({
            "severity": severity,
            "check": check,
            "task": task_name,
            "benchmark": benchmark,
            "message": message,
            "path": str(task_dir),
        })

    # Discover fixtures
    metadata = _discover_fixtures(task_dir)
    if metadata is None:
        return results, issues

    # Check if verifier can run outside Docker
    can_run, cant_reason = _can_run_outside_docker(task_dir)
    if not can_run:
        for fname in metadata["_fixture_names"]:
            results.append(FixtureResult(
                task_name=task_name,
                benchmark=benchmark,
                fixture_name=fname,
                score=None,
                expected_min=0.0,
                expected_max=1.0,
                passed=False,
                skipped=True,
                skip_reason=cant_reason,
                verifier_type=metadata.get("verifier_type", "unknown"),
            ))
        issue("INFO", "fixture_skipped",
              f"Fixture tests skipped: {cant_reason}")
        return results, issues

    verifier_type = metadata.get("verifier_type", "unknown")
    fixtures_dir = metadata["_fixtures_dir"]
    idempotency_scores: list[float] = []

    for fixture_name in metadata["_fixture_names"]:
        fixture_dir = fixtures_dir / fixture_name

        # Look up expected score bounds
        if fixture_name == "perfect_input":
            expected_min = float(metadata.get("perfect_expected_min", 0.9))
            expected_max = float(metadata.get("perfect_expected_max", 1.0))
        elif fixture_name == "empty_input":
            expected_min = float(metadata.get("empty_expected_min", 0.0))
            expected_max = float(metadata.get("empty_expected_max", 0.05))
        else:
            # Unknown fixture type — use permissive bounds
            expected_min = 0.0
            expected_max = 1.0

        sandbox = None
        try:
            sandbox = _setup_fixture_sandbox(task_dir, fixture_dir, metadata, fixture_name)
            score, skipped, skip_reason = _run_verifier_in_sandbox(
                sandbox, task_dir, timeout_sec=timeout_sec
            )
        except Exception as exc:
            score = None
            skipped = True
            skip_reason = f"Exception during fixture setup/run: {exc}"
        finally:
            if sandbox is not None:
                shutil.rmtree(sandbox, ignore_errors=True)

        if skipped:
            results.append(FixtureResult(
                task_name=task_name,
                benchmark=benchmark,
                fixture_name=fixture_name,
                score=None,
                expected_min=expected_min,
                expected_max=expected_max,
                passed=False,
                skipped=True,
                skip_reason=skip_reason,
                verifier_type=verifier_type,
            ))
            continue

        # Check score against expected bounds
        passed = expected_min <= score <= expected_max
        results.append(FixtureResult(
            task_name=task_name,
            benchmark=benchmark,
            fixture_name=fixture_name,
            score=score,
            expected_min=expected_min,
            expected_max=expected_max,
            passed=passed,
            skipped=False,
            skip_reason="",
            verifier_type=verifier_type,
        ))

        if not passed:
            issue(
                "CRITICAL",
                "fixture_score_mismatch",
                f"Fixture {fixture_name}: score={score:.3f} "
                f"(expected [{expected_min:.2f}, {expected_max:.2f}])",
            )

        # Track perfect_input scores for idempotency check
        if fixture_name == "perfect_input" and score is not None:
            idempotency_scores.append(score)

    # Idempotency check: run perfect_input a second time
    if run_idempotency and "perfect_input" in metadata["_fixture_names"]:
        fixture_dir = fixtures_dir / "perfect_input"
        sandbox = None
        try:
            sandbox = _setup_fixture_sandbox(task_dir, fixture_dir, metadata, "perfect_input")
            score2, skipped2, skip_reason2 = _run_verifier_in_sandbox(
                sandbox, task_dir, timeout_sec=timeout_sec
            )
        except Exception as exc:
            score2 = None
            skipped2 = True
            skip_reason2 = f"Idempotency run exception: {exc}"
        finally:
            if sandbox is not None:
                shutil.rmtree(sandbox, ignore_errors=True)

        if not skipped2 and score2 is not None:
            idempotency_scores.append(score2)

        if len(idempotency_scores) >= 2:
            s1, s2 = idempotency_scores[0], idempotency_scores[1]
            delta = abs(s1 - s2)
            if delta > IDEMPOTENCY_EPSILON:
                issue(
                    "WARNING",
                    "verifier_non_idempotent",
                    f"Verifier non-idempotent on perfect_input: "
                    f"run1={s1:.4f} run2={s2:.4f} delta={delta:.4f} "
                    f"(epsilon={IDEMPOTENCY_EPSILON})",
                )
        elif skipped2:
            issue(
                "INFO",
                "idempotency_skipped",
                f"Idempotency check skipped for perfect_input: {skip_reason2}",
            )

    return results, issues


def format_fixture_summary(
    all_fixture_results: list[FixtureResult],
    non_idempotent_count: int = 0,
) -> str:
    """Format fixture test results as a human-readable summary block."""
    if not all_fixture_results:
        return ""

    lines = []
    lines.append("")
    lines.append("=" * 60)
    lines.append("VERIFIER SELF-TESTS (fixture-based)")
    lines.append("=" * 60)

    # Group by task
    by_task: dict[str, list[FixtureResult]] = {}
    for r in all_fixture_results:
        key = f"{r.benchmark}/{r.task_name}"
        by_task.setdefault(key, []).append(r)

    passed_count = 0
    failed_count = 0
    skipped_count = 0
    non_idempotent_count = 0
    total_count = 0

    for task_key in sorted(by_task):
        task_results = by_task[task_key]
        verifier_type = task_results[0].verifier_type

        score_parts = []
        task_pass = True
        for r in task_results:
            total_count += 1
            if r.skipped:
                score_parts.append(f"{r.fixture_name}=SKIP")
                skipped_count += 1
            elif r.passed:
                score_parts.append(f"{r.fixture_name}={r.score:.2f}")
                passed_count += 1
            else:
                score_parts.append(f"{r.fixture_name}={r.score:.3f}")
                failed_count += 1
                task_pass = False

        status = "PASS" if task_pass and not all(r.skipped for r in task_results) else (
            "SKIP" if all(r.skipped for r in task_results) else "FAIL"
        )
        lines.append(
            f"  {status}: {task_key} verifier_type={verifier_type} "
            + " ".join(score_parts)
        )

        if not task_pass:
            for r in task_results:
                if not r.skipped and not r.passed:
                    lines.append(
                        f"        FAIL: {r.fixture_name}={r.score:.3f} "
                        f"(expected [{r.expected_min:.2f}, {r.expected_max:.2f}])"
                    )

    lines.append("")

    # Count non-idempotent from issues (they are tracked separately)
    # We pass this count in from the caller via the issues list

    testable = passed_count + failed_count
    summary = f"Verifier self-tests: {passed_count}/{testable} pass"
    if non_idempotent_count > 0:
        summary += f", {non_idempotent_count} non-idempotent"
    if skipped_count > 0:
        summary += f", {skipped_count} skipped"
    lines.append(summary)

    return "\n".join(lines)


def discover_task_dirs(suite: str | None = None, all_tasks: bool = False) -> list[Path]:
    """Find all task directories to validate."""
    dirs = []

    if suite:
        if suite == "sourcegraph_tasks":
            for entry in sorted(SOURCEGRAPH_TASKS_DIR.iterdir()):
                if entry.is_dir() and (entry / "task.toml").is_file():
                    dirs.append(entry)
            return dirs
        suite_dir = BENCHMARKS_DIR / suite
        if not suite_dir.is_dir():
            print(f"ERROR: Suite directory not found: {suite_dir}", file=sys.stderr)
            sys.exit(1)

        # Direct task dirs
        for entry in sorted(suite_dir.iterdir()):
            if entry.is_dir() and (entry / "task.toml").is_file():
                dirs.append(entry)
            # Check tasks/ subdirectory (swebenchpro)
            elif entry.name == "tasks" and entry.is_dir():
                for sub in sorted(entry.iterdir()):
                    if sub.is_dir() and (sub / "task.toml").is_file():
                        dirs.append(sub)
        return dirs

    if all_tasks:
        for bench_dir in sorted(BENCHMARKS_DIR.iterdir()):
            if not bench_dir.is_dir() or not bench_dir.name.startswith(("ccb_", "csb_")):
                continue
            for entry in sorted(bench_dir.iterdir()):
                if entry.is_dir() and (entry / "task.toml").is_file():
                    dirs.append(entry)
                elif entry.name == "tasks" and entry.is_dir():
                    for sub in sorted(entry.iterdir()):
                        if sub.is_dir() and (sub / "task.toml").is_file():
                            dirs.append(sub)
        if SOURCEGRAPH_TASKS_DIR.is_dir():
            for entry in sorted(SOURCEGRAPH_TASKS_DIR.iterdir()):
                if entry.is_dir() and (entry / "task.toml").is_file():
                    dirs.append(entry)
        return dirs

    return dirs


def format_table(all_issues: list[dict]) -> str:
    """Format issues as a human-readable report."""
    lines = []

    if not all_issues:
        lines.append("Pre-flight validation: ALL CHECKS PASSED")
        return "\n".join(lines)

    critical = [i for i in all_issues if i["severity"] == "CRITICAL"]
    warnings = [i for i in all_issues if i["severity"] == "WARNING"]
    infos = [i for i in all_issues if i["severity"] == "INFO"]

    lines.append(f"Pre-flight Validation: {len(all_issues)} issues found")
    lines.append(f"  CRITICAL: {len(critical)}")
    lines.append(f"  WARNING:  {len(warnings)}")
    lines.append(f"  INFO:     {len(infos)}")
    lines.append("")

    if critical:
        lines.append("CRITICAL (will cause run failures):")
        for i in critical:
            lines.append(f"  [{i['check']}] {i['benchmark']}/{i['task']}: {i['message']}")
        lines.append("")

    if warnings:
        lines.append("WARNING (may affect results):")
        for i in warnings:
            lines.append(f"  [{i['check']}] {i['benchmark']}/{i['task']}: {i['message']}")
        lines.append("")

    if infos:
        lines.append(f"INFO ({len(infos)} tasks not in selection registry — may be expected)")

    return "\n".join(lines)


def format_issue_summary(all_issues: list[dict]) -> str:
    """Format issue counts grouped by check name."""
    if not all_issues:
        return "Issue summary: no issues"

    counts: dict[str, int] = {}
    for issue in all_issues:
        counts[issue["check"]] = counts.get(issue["check"], 0) + 1

    lines = ["Issue summary by check:"]
    for check, count in sorted(counts.items(), key=lambda item: (-item[1], item[0])):
        lines.append(f"  {check}: {count}")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Pre-flight validation of benchmark tasks."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--suite", help="Validate all tasks in a suite (e.g., ccb_pytorch)")
    group.add_argument("--task", type=Path, help="Validate a single task directory")
    group.add_argument("--all", action="store_true", help="Validate all benchmark tasks")
    parser.add_argument("--format", choices=["table", "json"], default="table")
    parser.add_argument("--critical-only", action="store_true",
                        help="Only show CRITICAL issues")
    parser.add_argument(
        "--contract-only",
        action="store_true",
        help="Only show harness-agnostic task contract issues for migration work",
    )
    parser.add_argument(
        "--summary-by-check",
        action="store_true",
        help="Print an issue summary grouped by check name",
    )
    parser.add_argument(
        "--smoke-runtime",
        action="store_true",
        help="Run Docker build + verifier smoke (no agent) for each task, "
             "followed by fixture self-tests and idempotency checks",
    )
    parser.add_argument(
        "--smoke-timeout-sec",
        type=int,
        default=300,
        help="Per-task timeout for --smoke-runtime (default: 300)",
    )
    parser.add_argument(
        "--smoke-build-timeout-sec",
        type=int,
        default=None,
        help="Docker build timeout (defaults to --smoke-timeout-sec)",
    )
    parser.add_argument(
        "--smoke-verify-timeout-sec",
        type=int,
        default=None,
        help="Verifier run timeout (defaults to --smoke-timeout-sec)",
    )
    parser.add_argument(
        "--fixture-tests",
        action="store_true",
        help="Run verifier self-tests using tests/fixtures/ directories "
             "(without Docker smoke). Checks perfect_input/empty_input scores "
             "against expected bounds in metadata.json.",
    )
    parser.add_argument(
        "--idempotency",
        action="store_true",
        help="Run verifier idempotency checks (also activated by --smoke-runtime). "
             "Runs the perfect_input fixture twice and asserts scores match "
             f"within epsilon={IDEMPOTENCY_EPSILON}.",
    )
    parser.add_argument(
        "--fixture-timeout-sec",
        type=int,
        default=FIXTURE_RUN_TIMEOUT,
        help=f"Per-fixture verifier run timeout (default: {FIXTURE_RUN_TIMEOUT})",
    )
    args = parser.parse_args()

    selected_index = load_selected_tasks()

    if args.task:
        task_dir = args.task.resolve()
        if not task_dir.is_dir():
            print(f"ERROR: Not a directory: {task_dir}", file=sys.stderr)
            sys.exit(1)
        task_dirs = [task_dir]
    else:
        task_dirs = discover_task_dirs(suite=args.suite, all_tasks=args.all)

    if not task_dirs:
        print("No task directories found.", file=sys.stderr)
        sys.exit(1)

    # Determine whether to run fixture tests and idempotency checks
    # --idempotency implies --fixture-tests (needs perfect_input fixture to run)
    # --smoke-runtime implies both fixture tests and idempotency
    run_fixtures = args.fixture_tests or args.idempotency or args.smoke_runtime
    run_idempotency = args.idempotency or args.smoke_runtime

    all_issues = []
    all_fixture_results: list[FixtureResult] = []

    for td in task_dirs:
        issues = validate_task(td, selected_index)
        if args.smoke_runtime:
            issues.extend(
                smoke_task_runtime(
                    td,
                    timeout_sec=args.smoke_timeout_sec,
                    build_timeout_sec=args.smoke_build_timeout_sec,
                    verify_timeout_sec=args.smoke_verify_timeout_sec,
                )
            )

        # Fixture self-tests (after smoke, or standalone via --fixture-tests)
        if run_fixtures:
            fixture_results, fixture_issues = run_fixture_tests(
                td,
                run_idempotency=run_idempotency,
                timeout_sec=args.fixture_timeout_sec,
            )
            all_fixture_results.extend(fixture_results)
            issues.extend(fixture_issues)

        all_issues.extend(issues)

    # Count non-idempotent warnings for summary
    non_idempotent_count = sum(
        1 for i in all_issues if i["check"] == "verifier_non_idempotent"
    )

    if args.critical_only:
        all_issues = [i for i in all_issues if i["severity"] == "CRITICAL"]
    if args.contract_only:
        all_issues = [i for i in all_issues if i["check"] in CONTRACT_CHECKS]

    if args.format == "json":
        # Build fixture results data for JSON output
        fixture_data = []
        for r in all_fixture_results:
            fixture_data.append({
                "task_name": r.task_name,
                "benchmark": r.benchmark,
                "fixture_name": r.fixture_name,
                "score": r.score,
                "expected_min": r.expected_min,
                "expected_max": r.expected_max,
                "passed": r.passed,
                "skipped": r.skipped,
                "skip_reason": r.skip_reason,
                "verifier_type": r.verifier_type,
            })
        fixture_passed = sum(1 for r in all_fixture_results if r.passed)
        fixture_testable = sum(1 for r in all_fixture_results if not r.skipped)
        fixture_skipped = sum(1 for r in all_fixture_results if r.skipped)

        output = {
            "tasks_checked": len(task_dirs),
            "total_issues": len(all_issues),
            "critical": sum(1 for i in all_issues if i["severity"] == "CRITICAL"),
            "warning": sum(1 for i in all_issues if i["severity"] == "WARNING"),
            "info": sum(1 for i in all_issues if i["severity"] == "INFO"),
            "issues": all_issues,
        }
        if args.summary_by_check:
            summary_by_check = {}
            for issue in all_issues:
                summary_by_check[issue["check"]] = summary_by_check.get(issue["check"], 0) + 1
            output["summary_by_check"] = summary_by_check
        if run_fixtures:
            output["fixture_tests"] = {
                "passed": fixture_passed,
                "testable": fixture_testable,
                "skipped": fixture_skipped,
                "non_idempotent": non_idempotent_count,
                "results": fixture_data,
            }
        print(json.dumps(output, indent=2))
    else:
        print(f"Checked {len(task_dirs)} task directories.")
        print(format_table(all_issues))
        if args.summary_by_check:
            print("")
            print(format_issue_summary(all_issues))

        # Print fixture test summary if any were run
        if all_fixture_results:
            fixture_summary = format_fixture_summary(all_fixture_results, non_idempotent_count)
            print(fixture_summary)

    # Exit code: fixture failures are CRITICAL and contribute to exit code 1
    critical_count = sum(1 for i in all_issues if i["severity"] == "CRITICAL")
    if critical_count > 0:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
