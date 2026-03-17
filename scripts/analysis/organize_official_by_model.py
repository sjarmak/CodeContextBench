#!/usr/bin/env python3
"""Build an analysis-like view for runs/official grouped by suite family and model.

Output layout (symlink-based, no artifact copies):
  runs/official/{family}/{model}/{suite}/{baseline|mcp|mcp_Vx}/{task}/{trial_link}
"""

from __future__ import annotations

import argparse
import json
import hashlib
import re
import shutil
from pathlib import Path

from config_utils import discover_configs
from official_runs import (
    load_manifest,
    raw_runs_dir,
    read_triage,
    top_level_run_dirs,
    tracked_run_dirs_from_manifest,
)
from promote_run import benchmark_for_task, find_task_dirs

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OFFICIAL_DIR = PROJECT_ROOT / "runs" / "official"
BENCHMARKS_DIR = PROJECT_ROOT / "benchmarks"
SELECTED_TASKS_FILE = PROJECT_ROOT / "configs" / "selected_benchmark_tasks.json"


def infer_model_bucket(run_name: str) -> str:
    name = run_name.lower()
    if "haiku" in name:
        return "haiku-4.5"
    if "sonnet" in name:
        return "sonnet-4.5"
    if "opus" in name:
        if re.search(r"(?:^|[_-])opus[-_]?4[-_.]?6(?:$|[_-])", name):
            return "opus-4.6"
        return "opus-4.5"
    if "gpt53codex" in name:
        return "gpt-5.3-codex"
    return "unknown-model"


def normalize_task_id(task_name: str) -> str:
    tid = task_name.strip().lower()
    tid = re.sub(r"__[a-z0-9]{4,8}$", "", tid)
    tid = re.sub(r"_[a-z0-9]{4,8}$", "", tid)
    for pfx in ("sgonly_", "mcp_", "bl_"):
        if tid.startswith(pfx):
            tid = tid[len(pfx):]
    return tid


def load_task_dir_map() -> dict[str, Path]:
    mapping: dict[str, Path] = {}
    if not SELECTED_TASKS_FILE.is_file():
        return mapping
    data = json.loads(SELECTED_TASKS_FILE.read_text())
    for task in data.get("tasks", []):
        if not isinstance(task, dict):
            continue
        task_id = task.get("task_id")
        task_dir = task.get("task_dir")
        if not isinstance(task_id, str) or not isinstance(task_dir, str):
            continue
        p = BENCHMARKS_DIR / task_dir
        if not p.is_dir():
            continue
        mapping[task_id.lower()] = p
        mapping[normalize_task_id(task_id)] = p
    return mapping


def extract_preamble_signature(instruction_text: str) -> str:
    lines = instruction_text.splitlines()
    keep: list[str] = []
    for raw in lines:
        line = raw.strip()
        low = line.lower()
        if not line:
            continue
        # End of preamble in most task instructions.
        if low in {"---", "___"}:
            break
        if re.match(r"^##\s+your task\b", low):
            break
        if re.match(r"^#\s+(bug fix task|onboarding audit|task)\b", low):
            break
        # Remove task/repo-specific lines to keep template-level signature.
        if "github.com/" in low:
            continue
        if low.startswith("**target repositor"):
            continue
        if low.startswith("**repository:**"):
            continue
        if low.startswith("repo:^github.com/") or low.startswith("repo:github.com/"):
            continue
        if low.startswith("file:"):
            continue
        if low.startswith("```"):
            continue
        keep.append(low)
    normalized = re.sub(r"\s+", " ", "\n".join(keep)).strip()
    if not normalized:
        return "unknown"
    return hashlib.sha1(normalized.encode()).hexdigest()[:12]


def build_preamble_variant_map(task_dir_map: dict[str, Path]) -> tuple[dict[str, str], dict[str, dict[str, str]]]:
    sig_by_task: dict[str, str] = {}
    sig_counts: dict[str, int] = {}
    sig_example_task: dict[str, str] = {}
    for task_id, task_dir in task_dir_map.items():
        instr = task_dir / "instruction_mcp.md"
        if not instr.is_file():
            continue
        sig = extract_preamble_signature(instr.read_text(errors="ignore"))
        sig_by_task[task_id] = sig
        sig_counts[sig] = sig_counts.get(sig, 0) + 1
        sig_example_task.setdefault(sig, task_dir.as_posix())

    # Deterministic V-numbering: most common signatures get lowest Vn.
    ordered = sorted(sig_counts.keys(), key=lambda s: (-sig_counts[s], s))
    sig_to_variant = {sig: f"mcp_V{i+1}" for i, sig in enumerate(ordered)}
    variant_meta = {
        sig_to_variant[sig]: {
            "signature": sig,
            "task_count": str(sig_counts[sig]),
            "example_task_dir": sig_example_task[sig],
        }
        for sig in ordered
    }
    return sig_to_variant, variant_meta


def family_from_suite(suite: str) -> str:
    if suite.startswith("csb_sdlc_"):
        return "csb_sdlc"
    if suite.startswith("csb_org_"):
        return "csb_org"
    if suite.startswith("csb_"):
        parts = suite.split("_")
        return "_".join(parts[:2]) if len(parts) >= 2 else suite
    return suite


def channel_from_config(config_name: str, run_name: str) -> str | None:
    cfg = config_name.lower()
    if "retrieval_events" in cfg:
        return None
    if "baseline" in cfg and "sourcegraph" not in cfg:
        return "baseline"
    if "mcp" in cfg or "sourcegraph" in cfg:
        return "mcp"
    return None


def load_run_suite_map(manifest: dict) -> dict[str, dict[str, str]]:
    run_to_suite_cfg: dict[str, dict[str, str]] = {}
    run_history = manifest.get("run_history", {})
    if not isinstance(run_history, dict):
        return run_to_suite_cfg

    for suite_cfg, tasks in run_history.items():
        if not isinstance(tasks, dict) or "/" not in suite_cfg:
            continue
        suite, config = suite_cfg.split("/", 1)
        for stats in tasks.values():
            runs = stats.get("runs", []) if isinstance(stats, dict) else []
            if not isinstance(runs, list):
                continue
            for run in runs:
                if not isinstance(run, dict):
                    continue
                run_dir = run.get("run_dir")
                if not isinstance(run_dir, str) or not run_dir:
                    continue
                run_to_suite_cfg.setdefault(run_dir, {})
                run_to_suite_cfg[run_dir].setdefault(config, suite)
    return run_to_suite_cfg


def resolved_suite(run_name: str, config_name: str, task_dir: Path, suite_map: dict[str, dict[str, str]]) -> str | None:
    per_cfg = suite_map.get(run_name, {})
    if config_name in per_cfg:
        return per_cfg[config_name]
    if len(set(per_cfg.values())) == 1 and per_cfg:
        return next(iter(per_cfg.values()))
    return benchmark_for_task(run_name, task_dir)


def safe_unlink(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.is_dir():
        shutil.rmtree(path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--official-dir", default=str(OFFICIAL_DIR), help="Path to runs/official")
    parser.add_argument("--execute", action="store_true", help="Apply symlink changes (default: dry-run)")
    parser.add_argument("--clean-families", action="store_true", help="Remove existing family view dirs before rebuild")
    parser.add_argument("--report", default=str(PROJECT_ROOT / "runs" / "validation" / "official_model_view_report.json"))
    args = parser.parse_args()

    official_dir = Path(args.official_dir)
    source_root = raw_runs_dir(official_dir)
    manifest = load_manifest(official_dir / "MANIFEST.json")
    tracked = tracked_run_dirs_from_manifest(manifest)
    triage_include: set[str] = set()
    for run_dir in top_level_run_dirs(official_dir):
        triage, triage_err = read_triage(run_dir)
        if triage_err is None and triage and triage.get("decision") == "include":
            triage_include.add(run_dir.name)
    source_runs = sorted(tracked | triage_include)
    suite_map = load_run_suite_map(manifest)
    task_dir_map = load_task_dir_map()
    sig_to_variant, variant_meta = build_preamble_variant_map(task_dir_map)

    links_to_create: list[tuple[Path, Path]] = []
    family_dirs: set[Path] = set()
    skipped_missing_results = 0
    skipped_unknown_channel = 0
    skipped_unknown_suite = 0
    scanned_trials = 0

    for run_name in source_runs:
        run_dir = source_root / run_name
        if not run_dir.is_dir():
            continue
        model = infer_model_bucket(run_name)

        for config_name in discover_configs(run_dir):
            channel = channel_from_config(config_name, run_name)
            if channel is None:
                skipped_unknown_channel += 1
                continue

            config_dir = run_dir / config_name
            for task_dir in find_task_dirs(config_dir):
                result_json = task_dir / "result.json"
                if not result_json.is_file():
                    skipped_missing_results += 1
                    continue
                scanned_trials += 1
                try:
                    data = json.loads(result_json.read_text())
                    task_name = data.get("task_name") or task_dir.name.rsplit("__", 1)[0]
                except Exception:
                    task_name = task_dir.name.rsplit("__", 1)[0]

                suite = resolved_suite(run_name, config_name, task_dir, suite_map)
                if not suite:
                    skipped_unknown_suite += 1
                    continue

                bucket = channel
                if channel == "mcp":
                    task_key = normalize_task_id(task_name)
                    mapped_dir = task_dir_map.get(task_key)
                    if mapped_dir is not None:
                        sig = extract_preamble_signature((mapped_dir / "instruction_mcp.md").read_text(errors="ignore")) \
                            if (mapped_dir / "instruction_mcp.md").is_file() else "unknown"
                        bucket = sig_to_variant.get(sig, "mcp_unknown")
                    else:
                        bucket = "mcp_unknown"

                family = family_from_suite(suite)
                family_dir = official_dir / family
                family_dirs.add(family_dir)
                target_dir = family_dir / model / suite / bucket / task_name
                link_name = f"{run_name}__{task_dir.name}"
                link_path = target_dir / link_name
                links_to_create.append((task_dir, link_path))

    if args.clean_families:
        for family_dir in sorted(family_dirs):
            if family_dir.exists():
                if args.execute:
                    shutil.rmtree(family_dir)

    created = 0
    unchanged = 0
    conflicts = 0
    conflict_paths: list[str] = []

    for source, target in links_to_create:
        if target.exists() or target.is_symlink():
            if target.is_symlink() and target.resolve() == source.resolve():
                unchanged += 1
                continue
            conflicts += 1
            conflict_paths.append(str(target))
            if args.execute:
                safe_unlink(target)
            else:
                continue
        if args.execute:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.symlink_to(source)
            created += 1

    report = {
        "official_dir": str(official_dir),
        "source_raw_dir": str(source_root),
        "tracked_runs": len(tracked),
        "triage_include_runs": len(triage_include),
        "source_runs": len(source_runs),
        "scanned_trials": scanned_trials,
        "planned_links": len(links_to_create),
        "created_links": created,
        "planned_new_links": created + (0 if args.execute else (len(links_to_create) - unchanged - conflicts)),
        "unchanged_links": unchanged,
        "conflicts_replaced": conflicts if args.execute else 0,
        "conflicts_detected": conflicts,
        "skipped_missing_results": skipped_missing_results,
        "skipped_unknown_channel": skipped_unknown_channel,
        "skipped_unknown_suite": skipped_unknown_suite,
        "sample_conflicts": conflict_paths[:50],
        "family_dirs": sorted(str(p) for p in family_dirs),
        "mcp_variant_catalog": variant_meta,
        "mode": "execute" if args.execute else "dry_run",
    }

    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + "\n")

    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
