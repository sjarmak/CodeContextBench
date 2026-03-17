#!/usr/bin/env python3
"""Audit canonical task evaluator families and output contracts.

Reads configs/selected_benchmark_tasks.json, inspects each selected task's
task.toml, verifier entrypoints, Dockerfile variants, and task instructions,
then emits a machine-readable audit artifact for follow-on remediation work.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

try:
    import tomllib  # type: ignore[attr-defined]
except ModuleNotFoundError:  # pragma: no cover - Python <3.11 fallback
    import tomli as tomllib  # type: ignore[no-redef]


PROJECT_ROOT = Path(__file__).resolve().parent.parent
BENCHMARKS_DIR = PROJECT_ROOT / "benchmarks"
SELECTED_TASKS_PATH = PROJECT_ROOT / "configs" / "selected_benchmark_tasks.json"
DEFAULT_OUTPUT_PATH = PROJECT_ROOT / "configs" / "canonical_evaluation_audit.json"

KNOWN_OUTPUT_FILES = (
    "answer.json",
    "solution.json",
    "review.json",
    "fault_localization_result.json",
    "triage.md",
    "solution.md",
    "analysis.md",
    "documentation.md",
)

REPORT_OUTPUT_FILES = (
    "triage.md",
    "solution.md",
    "analysis.md",
    "documentation.md",
)

TASK_OUTPUT_PATTERNS = (
    re.compile(r'TASK_OUTPUT="\$\{TASK_OUTPUT:-([^"}]+)\}"'),
    re.compile(r"TASK_OUTPUT='\$\{TASK_OUTPUT:-([^'}]+)\}'"),
    re.compile(r"ENV\s+TASK_OUTPUT=([^\s]+)"),
)

ENV_VAR_PATTERNS = {
    "TASK_WORKDIR": (
        re.compile(r'TASK_WORKDIR="\$\{TASK_WORKDIR:-([^"}]+)\}"'),
        re.compile(r"TASK_WORKDIR='\$\{TASK_WORKDIR:-([^'}]+)\}'"),
        re.compile(r"ENV\s+TASK_WORKDIR=([^\s]+)"),
    ),
    "TASK_REPO_ROOT": (
        re.compile(r'TASK_REPO_ROOT="\$\{TASK_REPO_ROOT:-([^"}]+)\}"'),
        re.compile(r"TASK_REPO_ROOT='\$\{TASK_REPO_ROOT:-([^'}]+)\}'"),
        re.compile(r"ENV\s+TASK_REPO_ROOT=([^\s]+)"),
    ),
}

KNOWN_REPORT_PATH_PATTERNS = tuple(
    re.compile(rf"/logs/agent/[^\s\"']*{re.escape(name)}")
    for name in REPORT_OUTPUT_FILES
)

VALIDATION_RESULT_SCHEMA_VERSION = "validation_result.v1alpha1"
VALIDATION_RESULT_MINIMUM_FIELDS = (
    "schema_version",
    "status",
    "scorable",
    "scorer_family",
    "reward",
    "pass_threshold",
    "passed",
    "output_contract",
    "sub_scores",
    "failure",
)
VALIDATION_RESULT_OPTIONAL_FIELDS = (
    "details",
    "artifacts",
    "timing",
    "legacy",
)
OUTPUT_CONTRACT_MINIMUM_FIELDS = (
    "mode",
    "primary_path",
    "required_artifact",
)
VALIDATION_RESULT_STATUS_VALUES = {
    "scored": "Verifier had enough task output to compute a reward.",
    "invalid_output": "Required task output was missing or malformed, so the run was not scorable.",
    "verifier_error": "Verifier dependencies or runtime failed before scoring could complete.",
}
VALIDATION_RESULT_FAMILY_MAP: dict[str, dict[str, Any]] = {
    "binary": {
        "reward_source": "Binary pass/fail outcome.",
        "recommended_sub_scores": ["binary_pass"],
        "notes": "Use sub_scores={} only if the family exposes no finer-grained assertions.",
    },
    "checklist": {
        "reward_source": "Weighted checklist aggregate.",
        "recommended_sub_scores": ["checks.<assertion_id>"],
        "notes": "Preserve stable assertion ids rather than emitting only a scalar reward.",
    },
    "continuous": {
        "reward_source": "Family-defined continuous score.",
        "recommended_sub_scores": ["continuous_score"],
        "notes": "Use the family metric name when one already exists.",
    },
    "diff_similarity": {
        "reward_source": "Diff similarity composite.",
        "recommended_sub_scores": ["file_recall", "line_recall", "line_precision"],
        "notes": "Keep the weighted composite in reward and component recalls in sub_scores.",
    },
    "f1": {
        "reward_source": "F1 score.",
        "recommended_sub_scores": ["precision", "recall", "f1"],
        "notes": "Include precision/recall even when reward duplicates f1.",
    },
    "f1_hybrid": {
        "reward_source": "Blended detection F1 and fix quality score.",
        "recommended_sub_scores": ["detection_f1", "fix_score"],
        "notes": "Artifact bridge tasks should still identify answer_json_bridge in output_contract.mode.",
    },
    "find_and_prove": {
        "reward_source": "Composite regression-proof score.",
        "recommended_sub_scores": ["checks.<assertion_id>"],
        "notes": "Use stable assertion ids for fail-on-buggy, pass-after-patch, and explanation checks.",
    },
    "ir_checklist": {
        "reward_source": "Checklist-style retrieval score.",
        "recommended_sub_scores": ["checks.<assertion_id>"],
        "notes": "Preserve retrieval-specific assertion ids in sub_scores.",
    },
    "oracle_checks": {
        "reward_source": "Suite-weighted composite over oracle checks.",
        "recommended_sub_scores": [
            "file_set_match",
            "symbol_resolution",
            "dependency_chain",
            "keyword_presence",
            "provenance",
            "json_schema_match",
            "test_ratio",
        ],
        "notes": "One sub-score entry per configured oracle check; keep raw checker payload in details.",
    },
    "repo_state_heuristic": {
        "reward_source": "Repo-state heuristic aggregate.",
        "recommended_sub_scores": ["checks.<assertion_id>"],
        "notes": "Use stable assertion ids instead of only shell log output.",
    },
    "score": {
        "reward_source": "Generic scalar score.",
        "recommended_sub_scores": [],
        "notes": "Transitional family only; preferred family names should be more specific.",
    },
    "semantic_retrieval_qa": {
        "reward_source": "Primary QA correctness score.",
        "recommended_sub_scores": ["correct_function", "correct_path", "justification_score"],
        "notes": "Keep free-form reasoning under details rather than flattening it into top-level fields.",
    },
    "semantic_similarity": {
        "reward_source": "Semantic similarity score.",
        "recommended_sub_scores": ["similarity"],
        "notes": "Record the exact similarity measure in details when multiple measures exist.",
    },
    "test_ratio": {
        "reward_source": "Passed/total test ratio.",
        "recommended_sub_scores": ["tests_passed_ratio"],
        "notes": "Store passed/failed counts in details when available.",
    },
}


def read_text(path: Path) -> str:
    if not path.is_file():
        return ""
    return path.read_text(errors="ignore")


def load_selected_tasks() -> list[dict[str, Any]]:
    data = json.loads(SELECTED_TASKS_PATH.read_text())
    return data.get("tasks", [])


def find_task_dir(task: dict[str, Any]) -> Path | None:
    task_dir = task.get("task_dir")
    if task_dir:
        candidate = BENCHMARKS_DIR / task_dir
        if candidate.is_dir():
            return candidate

    benchmark = task.get("benchmark", "")
    task_id = task.get("task_id", "")
    for variant in (task_id, task_id.lower(), task_id.upper()):
        candidate = BENCHMARKS_DIR / benchmark / variant
        if candidate.is_dir():
            return candidate
    return None


def load_toml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    with path.open("rb") as fh:
        return tomllib.load(fh)


def resolve_verifier_entrypoint(command: str, tests_dir: Path) -> Path | None:
    parts = command.split()
    for part in parts:
        if not part.startswith("/tests/"):
            continue
        candidate = tests_dir / part[len("/tests/"):]
        if candidate.is_file():
            return candidate
    if (tests_dir / "test.sh").is_file():
        return tests_dir / "test.sh"
    if (tests_dir / "eval.sh").is_file():
        return tests_dir / "eval.sh"
    return None


def extract_task_output_defaults(*texts: str) -> list[str]:
    values: list[str] = []
    for text in texts:
        if not text:
            continue
        for pattern in TASK_OUTPUT_PATTERNS:
            for match in pattern.findall(text):
                if match and match not in values:
                    values.append(match)
    return values


def extract_env_defaults(*texts: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for var_name, patterns in ENV_VAR_PATTERNS.items():
        for text in texts:
            if not text:
                continue
            for pattern in patterns:
                matches = pattern.findall(text)
                if matches:
                    values[var_name] = matches[0]
                    break
            if var_name in values:
                break
    return values


def detect_known_outputs(*texts: str) -> list[str]:
    values: list[str] = []
    for text in texts:
        lower = text.lower()
        for name in KNOWN_OUTPUT_FILES:
            if name.lower() in lower and name not in values:
                values.append(name)
    return values


def detect_report_paths(*texts: str) -> list[str]:
    values: list[str] = []
    for text in texts:
        if not text:
            continue
        for pattern in KNOWN_REPORT_PATH_PATTERNS:
            for match in pattern.findall(text):
                if match not in values:
                    values.append(match)
    return values


def classify_evaluator_family(
    reward_type: str,
    verification_description: str,
    verifier_text: str,
    has_oracle_files: bool,
) -> tuple[str, list[str]]:
    signals: list[str] = []
    reward_type = reward_type or "unknown"
    desc = verification_description.lower()
    lower = verifier_text.lower()

    if has_oracle_files:
        signals.append("oracle_files_present")
        return "oracle_checks", signals

    if "semanticretrievalqaverifier" in lower:
        signals.append("semantic_retrieval_verifier")
        return "semantic_retrieval_qa", signals

    if reward_type == "diff_similarity":
        signals.append("reward_type=diff_similarity")
        return "diff_similarity", signals

    if reward_type == "test_ratio":
        signals.append("reward_type=test_ratio")
        if "fail-on-buggy" in lower or "pass-after-patch" in lower:
            signals.append("navigation_verified_keywords")
            return "navigation_verified", signals
        return "test_ratio", signals

    if reward_type == "binary":
        signals.append("reward_type=binary")
        return "binary", signals

    if reward_type == "semantic_similarity":
        signals.append("reward_type=semantic_similarity")
        return "semantic_similarity", signals

    if reward_type == "checklist":
        signals.append("reward_type=checklist")
        if "f1 score" in desc or "fix_patch" in lower or "review.json" in lower:
            signals.append("f1_hybrid_signals")
            return "f1_hybrid", signals
        if "ground_truth.json" in lower or "required_findings" in lower:
            signals.append("ground_truth_checklist_signals")
            return "checklist", signals
        if "git diff head" in lower or "grep -q" in lower or "verify_repo" in lower:
            signals.append("repo_state_heuristic_signals")
            return "repo_state_heuristic", signals
        return "checklist", signals

    if reward_type == "score":
        signals.append("reward_type=score")
        return "score", signals

    return reward_type, signals


def classify_output_contract(
    primary_output_path: str | None,
    known_outputs: list[str],
    answer_json_mode: str,
    report_paths: list[str],
    repo_state_required: bool,
) -> str:
    if answer_json_mode == "bridge":
        return "answer_json_bridge"
    if primary_output_path and primary_output_path.endswith("answer.json"):
        return "answer_json_native"
    if primary_output_path and primary_output_path.endswith("solution.json"):
        return "solution_json"
    if report_paths:
        return "report_markdown"
    if repo_state_required:
        return "repo_state"
    if known_outputs:
        return known_outputs[0]
    return "unspecified"


def classify_validation_result_migration(structured_output_mode: str) -> str:
    if structured_output_mode == "validation_result":
        return "already_validation_result"
    if structured_output_mode == "reward_json":
        return "wrap_reward_json"
    return "emit_validation_result_sidecar"


def build_validation_result_contract(records: list[dict[str, Any]]) -> dict[str, Any]:
    family_counts = Counter()
    family_output_contracts: dict[str, Counter[str]] = defaultdict(Counter)
    family_structured_modes: dict[str, Counter[str]] = defaultdict(Counter)
    family_examples: dict[str, list[str]] = defaultdict(list)
    migration_counts = Counter()

    for record in records:
        if record.get("error"):
            continue

        family = record["evaluator"]["family"]
        structured_output_mode = record["verification"]["structured_output_mode"]
        output_contract = record["output_contract"]["classification"]
        migration_class = classify_validation_result_migration(structured_output_mode)

        family_counts[family] += 1
        family_output_contracts[family][output_contract] += 1
        family_structured_modes[family][structured_output_mode] += 1
        migration_counts[migration_class] += 1

        if len(family_examples[family]) < 3:
            family_examples[family].append(record["task_id"])

    families = sorted(set(VALIDATION_RESULT_FAMILY_MAP) | set(family_counts))
    family_mappings: dict[str, dict[str, Any]] = {}
    for family in families:
        spec = VALIDATION_RESULT_FAMILY_MAP.get(
            family,
            {
                "reward_source": "Family-specific scalar reward.",
                "recommended_sub_scores": [],
                "notes": "Populate sub_scores={} until the family receives a more specific contract.",
            },
        )
        family_mappings[family] = {
            **spec,
            "current_task_count": family_counts.get(family, 0),
            "structured_output_modes": dict(sorted(family_structured_modes[family].items())),
            "output_contracts": dict(sorted(family_output_contracts[family].items())),
            "sample_tasks": family_examples[family],
        }

    return {
        "schema_version": VALIDATION_RESULT_SCHEMA_VERSION,
        "minimum_required_fields": list(VALIDATION_RESULT_MINIMUM_FIELDS),
        "recommended_optional_fields": list(VALIDATION_RESULT_OPTIONAL_FIELDS),
        "output_contract_required_fields": list(OUTPUT_CONTRACT_MINIMUM_FIELDS),
        "status_values": VALIDATION_RESULT_STATUS_VALUES,
        "migration_classes": {
            "already_validation_result": "Task already writes validation_result.json and should backfill any missing canonical fields.",
            "wrap_reward_json": "Task writes reward.json today and should wrap that scalar into validation_result.json.",
            "emit_validation_result_sidecar": "Task writes reward.txt only and should add validation_result.json alongside it.",
        },
        "migration_counts": dict(sorted(migration_counts.items())),
        "family_mappings": family_mappings,
    }


def build_task_record(task: dict[str, Any]) -> dict[str, Any]:
    task_dir = find_task_dir(task)
    if task_dir is None:
        return {
            "task_id": task.get("task_id"),
            "benchmark": task.get("benchmark"),
            "task_dir": task.get("task_dir"),
            "excluded": bool(task.get("excluded")),
            "error": "task_dir_not_found",
        }

    tests_dir = task_dir / "tests"
    env_dir = task_dir / "environment"
    task_toml = load_toml(task_dir / "task.toml")

    verification = task_toml.get("verification", {})
    task_meta = task_toml.get("task", {})

    reward_type = verification.get("reward_type", "")
    verification_description = verification.get("description", "")
    verification_command = verification.get("command", "")
    verification_modes = task_meta.get("verification_modes", [])

    instruction_text = read_text(task_dir / "instruction.md")
    instruction_mcp_text = read_text(task_dir / "instruction_mcp.md")
    verifier_path = resolve_verifier_entrypoint(verification_command, tests_dir)
    test_path = tests_dir / "test.sh"
    eval_path = tests_dir / "eval.sh"
    verifier_entrypoint = (
        str(verifier_path.relative_to(PROJECT_ROOT)) if verifier_path is not None else None
    )
    test_text = read_text(test_path)
    eval_text = read_text(eval_path)
    artifact_dockerfile_text = read_text(env_dir / "Dockerfile.artifact_only")
    baseline_artifact_dockerfile_text = read_text(env_dir / "Dockerfile.artifact_baseline")

    verifier_text = "\n".join(
        text
        for text in (
            test_text,
            eval_text,
            verification_description,
            verification_command,
        )
        if text
    )

    has_oracle_checks = (tests_dir / "oracle_checks.py").is_file()
    has_task_spec = (tests_dir / "task_spec.json").is_file()
    has_promoted_verifier = (tests_dir / "promoted_verifier.py").is_file()
    has_answer_json_bridge = (tests_dir / "answer_json_verifier_lib.sh").is_file()
    has_ground_truth = (tests_dir / "ground_truth.json").is_file()

    task_output_defaults = extract_task_output_defaults(
        artifact_dockerfile_text,
        baseline_artifact_dockerfile_text,
        eval_text,
        test_text,
    )
    env_defaults = extract_env_defaults(
        artifact_dockerfile_text,
        baseline_artifact_dockerfile_text,
        eval_text,
        test_text,
    )
    known_outputs = detect_known_outputs(
        instruction_text,
        instruction_mcp_text,
        test_text,
        eval_text,
    )
    report_paths = detect_report_paths(instruction_text, instruction_mcp_text, test_text, eval_text)

    primary_output_path = task_output_defaults[0] if task_output_defaults else None
    if primary_output_path is None:
        if "answer.json" in known_outputs:
            primary_output_path = "/workspace/answer.json"
        elif "solution.json" in known_outputs:
            primary_output_path = "/app/solution.json"
    if primary_output_path:
        for var_name, default_value in env_defaults.items():
            primary_output_path = primary_output_path.replace(f"${var_name}", default_value)
            primary_output_path = primary_output_path.replace(f"${{{var_name}}}", default_value)

    repo_state_required = any(
        token in verifier_text
        for token in ("VERIFY_REPO", "/repo_full", "git diff", "patch -p1", "git apply")
    )

    answer_json_mode = "none"
    answer_json_signals = []
    if has_answer_json_bridge:
        answer_json_mode = "bridge"
        answer_json_signals.append("answer_json_verifier_lib.sh")
    elif any(
        "answer.json" in text.lower()
        for text in (
            instruction_text,
            instruction_mcp_text,
            test_text,
            eval_text,
            artifact_dockerfile_text,
            baseline_artifact_dockerfile_text,
        )
    ) and (primary_output_path or "").endswith("answer.json"):
        answer_json_mode = "native"
        answer_json_signals.append("primary_output_path=answer.json")

    structured_output_mode = "none"
    if "validation_result.json" in verifier_text:
        structured_output_mode = "validation_result"
    elif "reward.json" in verifier_text:
        structured_output_mode = "reward_json"

    evaluator_family, evaluator_signals = classify_evaluator_family(
        reward_type=reward_type,
        verification_description=verification_description,
        verifier_text=verifier_text,
        has_oracle_files=has_oracle_checks or has_task_spec or has_promoted_verifier,
    )

    output_contract = classify_output_contract(
        primary_output_path=primary_output_path,
        known_outputs=known_outputs,
        answer_json_mode=answer_json_mode,
        report_paths=report_paths,
        repo_state_required=repo_state_required,
    )
    migration_class = classify_validation_result_migration(structured_output_mode)

    return {
        "task_id": task.get("task_id"),
        "benchmark": task.get("benchmark"),
        "task_dir": str(task_dir.relative_to(BENCHMARKS_DIR)),
        "excluded": bool(task.get("excluded")),
        "verification": {
            "reward_type": reward_type or None,
            "description": verification_description or None,
            "command": verification_command or None,
            "verification_modes": verification_modes,
            "entrypoint": verifier_entrypoint,
            "deterministic_verifier_present": bool(test_path.is_file() or eval_path.is_file()),
            "structured_output_mode": structured_output_mode,
        },
        "evaluator": {
            "family": evaluator_family,
            "signals": evaluator_signals,
        },
        "artifact_support": {
            "dockerfile_artifact_only": (env_dir / "Dockerfile.artifact_only").is_file(),
            "dockerfile_artifact_baseline": (env_dir / "Dockerfile.artifact_baseline").is_file(),
            "dockerfile_sg_only": (env_dir / "Dockerfile.sg_only").is_file(),
            "dockerfile_default": (env_dir / "Dockerfile").is_file(),
            "answer_json_mode": answer_json_mode,
            "answer_json_signals": answer_json_signals,
        },
        "ground_truth": {
            "ground_truth_json": has_ground_truth,
            "task_spec_json": has_task_spec,
            "oracle_checks_py": has_oracle_checks,
            "promoted_verifier_py": has_promoted_verifier,
            "answer_json_bridge_lib": has_answer_json_bridge,
        },
        "output_contract": {
            "classification": output_contract,
            "env_defaults": env_defaults,
            "primary_output_path": primary_output_path,
            "known_outputs": known_outputs,
            "report_paths": report_paths,
            "repo_state_required": repo_state_required,
        },
        "validation_result_plan": {
            "schema_version": VALIDATION_RESULT_SCHEMA_VERSION,
            "migration_class": migration_class,
            "output_contract_mode": output_contract,
            "scorer_family": evaluator_family,
        },
    }


def summarize(records: list[dict[str, Any]]) -> dict[str, Any]:
    missing_task_dirs = [
        {"benchmark": r.get("benchmark"), "task_id": r.get("task_id")}
        for r in records
        if r.get("error") == "task_dir_not_found"
    ]
    summary: dict[str, Any] = {
        "total_tasks": len(records),
        "active_tasks": sum(1 for r in records if not r.get("excluded")),
        "excluded_tasks": sum(1 for r in records if r.get("excluded")),
        "missing_task_dirs": sorted(
            missing_task_dirs, key=lambda x: (str(x.get("benchmark")), str(x.get("task_id")))
        ),
    }

    family_counter = Counter()
    reward_type_counter = Counter()
    output_contract_counter = Counter()
    answer_json_mode_counter = Counter()
    structured_output_counter = Counter()
    artifact_output_counter = Counter()
    suite_summary: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "total": 0,
            "excluded": 0,
            "artifact_only": 0,
            "artifact_baseline": 0,
            "answer_json_native": 0,
            "answer_json_bridge": 0,
            "validation_result": 0,
            "reward_json": 0,
        }
    )

    missing_artifact_only: list[dict[str, str]] = []
    missing_validation_result: list[dict[str, str]] = []
    artifact_without_answer_json: list[dict[str, str]] = []

    for record in records:
        if record.get("error"):
            continue

        benchmark = record["benchmark"]
        suite = suite_summary[benchmark]
        suite["total"] += 1
        suite["excluded"] += int(record.get("excluded", False))

        verifier = record["verification"]
        artifact = record["artifact_support"]
        outputs = record["output_contract"]
        evaluator = record["evaluator"]

        family_counter[evaluator["family"]] += 1
        reward_type_counter[verifier["reward_type"] or "unknown"] += 1
        output_contract_counter[outputs["classification"]] += 1
        answer_json_mode_counter[artifact["answer_json_mode"]] += 1
        structured_output_counter[verifier["structured_output_mode"]] += 1

        if artifact["dockerfile_artifact_only"]:
            suite["artifact_only"] += 1
            primary_output = outputs["primary_output_path"] or outputs["classification"]
            artifact_output_counter[primary_output] += 1
            if artifact["answer_json_mode"] == "none":
                artifact_without_answer_json.append(
                    {"benchmark": benchmark, "task_id": record["task_id"]}
                )
        else:
            missing_artifact_only.append({"benchmark": benchmark, "task_id": record["task_id"]})

        if artifact["dockerfile_artifact_baseline"]:
            suite["artifact_baseline"] += 1
        if artifact["answer_json_mode"] == "native":
            suite["answer_json_native"] += 1
        if artifact["answer_json_mode"] == "bridge":
            suite["answer_json_bridge"] += 1
        if verifier["structured_output_mode"] == "validation_result":
            suite["validation_result"] += 1
        elif verifier["structured_output_mode"] == "reward_json":
            suite["reward_json"] += 1
            missing_validation_result.append({"benchmark": benchmark, "task_id": record["task_id"]})
        else:
            missing_validation_result.append({"benchmark": benchmark, "task_id": record["task_id"]})

    summary["counts"] = {
        "evaluator_families": dict(sorted(family_counter.items())),
        "reward_types": dict(sorted(reward_type_counter.items())),
        "output_contracts": dict(sorted(output_contract_counter.items())),
        "answer_json_modes": dict(sorted(answer_json_mode_counter.items())),
        "structured_output_modes": dict(sorted(structured_output_counter.items())),
        "artifact_primary_outputs": dict(sorted(artifact_output_counter.items())),
    }
    summary["by_suite"] = dict(sorted(suite_summary.items()))
    summary["gaps"] = {
        "missing_artifact_only": sorted(missing_artifact_only, key=lambda x: (x["benchmark"], x["task_id"])),
        "missing_validation_result": sorted(
            missing_validation_result, key=lambda x: (x["benchmark"], x["task_id"])
        ),
        "artifact_without_answer_json": sorted(
            artifact_without_answer_json, key=lambda x: (x["benchmark"], x["task_id"])
        ),
    }
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
        help=f"Path to write audit JSON (default: {DEFAULT_OUTPUT_PATH})",
    )
    args = parser.parse_args()

    tasks = load_selected_tasks()
    records = [build_task_record(task) for task in tasks]
    records.sort(key=lambda r: (str(r.get("benchmark", "")), str(r.get("task_id", ""))))

    output = {
        "source": {
            "selected_tasks": str(SELECTED_TASKS_PATH.relative_to(PROJECT_ROOT)),
            "total_selected_entries": len(tasks),
        },
        "summary": summarize(records),
        "validation_result_contract": build_validation_result_contract(records),
        "tasks": records,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")

    print(
        json.dumps(
            {
                "output": str(args.output.relative_to(PROJECT_ROOT)),
                "total_tasks": output["summary"]["total_tasks"],
                "missing_artifact_only": len(output["summary"]["gaps"]["missing_artifact_only"]),
                "missing_validation_result": len(output["summary"]["gaps"]["missing_validation_result"]),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
