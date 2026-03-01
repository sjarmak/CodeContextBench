#!/usr/bin/env python3
"""Validate the context retrieval agent against ContextBench.

ContextBench (https://github.com/EuniAI/ContextBench) is an external
benchmark with 1,136 human-annotated SWE-bench tasks measuring context
retrieval quality at file/symbol/span/edit-location granularity.

This script:
1. Loads ContextBench tasks (from Hugging Face or local parquet)
2. Runs our context_retrieval_agent on each task
3. Converts output to ContextBench trajectory format
4. Evaluates against human-annotated gold contexts
5. Reports file recall, precision, and F1

Environment variables:
    ANTHROPIC_API_KEY           Required.
    SOURCEGRAPH_ACCESS_TOKEN    Required for deepsearch/hybrid backends.
    CCB_REPO_CACHE              Repo clone cache (default: ~/.cache/ccb_repos)

Usage:
    # Install ContextBench first
    pip install contextbench datasets

    # Download gold data
    python3 scripts/validate_on_contextbench.py --download-data

    # Quick pilot (5 tasks)
    python3 scripts/validate_on_contextbench.py --sample 5 --verbose

    # Medium pilot (50 tasks)
    python3 scripts/validate_on_contextbench.py --sample 50

    # Full verified subset (500 tasks)
    python3 scripts/validate_on_contextbench.py --verified

    # Custom backend/model
    python3 scripts/validate_on_contextbench.py --sample 10 \\
        --model claude-haiku-4-5-20251001 --backend local
"""

import argparse
import json
import logging
import os
import random
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

log = logging.getLogger("validate_on_contextbench")

# Default paths
DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "contextbench"
RESULTS_DIR = Path(__file__).resolve().parent.parent / "results" / "contextbench"
REPO_CACHE = Path(os.environ.get("CCB_REPO_CACHE", str(Path.home() / ".cache" / "ccb_repos")))


def download_data(data_dir: Path = DATA_DIR) -> None:
    """Download ContextBench dataset from Hugging Face."""
    data_dir.mkdir(parents=True, exist_ok=True)

    try:
        from datasets import load_dataset
    except ImportError:
        log.error("Install datasets: pip install datasets")
        sys.exit(1)

    # Full dataset
    full_path = data_dir / "full.parquet"
    if not full_path.exists():
        log.info("Downloading ContextBench full dataset...")
        ds = load_dataset("Contextbench/ContextBench", "default")
        ds["train"].to_parquet(str(full_path))
        log.info("Saved: %s", full_path)
    else:
        log.info("Already exists: %s", full_path)

    # Verified subset
    verified_path = data_dir / "verified.parquet"
    if not verified_path.exists():
        log.info("Downloading ContextBench verified subset...")
        ds = load_dataset("Contextbench/ContextBench", "contextbench_verified")
        ds["train"].to_parquet(str(verified_path))
        log.info("Saved: %s", verified_path)
    else:
        log.info("Already exists: %s", verified_path)


def load_tasks(
    data_dir: Path = DATA_DIR,
    verified: bool = False,
    sample: int = 0,
    seed: int = 42,
) -> List[Dict[str, Any]]:
    """Load ContextBench tasks from parquet.

    Returns list of dicts with: instance_id, repo, commit, problem_statement,
    patch, gold_files, etc.
    """
    try:
        import pyarrow.parquet as pq
    except ImportError:
        log.error("Install pyarrow: pip install pyarrow")
        sys.exit(1)

    fname = "verified.parquet" if verified else "full.parquet"
    path = data_dir / fname
    if not path.exists():
        log.error("Dataset not found: %s. Run --download-data first.", path)
        sys.exit(1)

    table = pq.read_table(str(path))
    df = table.to_pydict()

    # Convert columnar dict to list of row dicts
    n_rows = len(next(iter(df.values())))
    tasks = []
    keys = list(df.keys())
    for i in range(n_rows):
        row = {k: df[k][i] for k in keys}
        tasks.append(row)

    log.info("Loaded %d tasks from %s", len(tasks), fname)

    if sample > 0 and sample < len(tasks):
        rng = random.Random(seed)
        tasks = rng.sample(tasks, sample)
        log.info("Sampled %d tasks (seed=%d)", len(tasks), seed)

    return tasks


def clone_for_contextbench(
    repo_url: str, commit: str, cache_dir: Path = REPO_CACHE
) -> Optional[Path]:
    """Clone a repo at a specific commit for ContextBench evaluation.

    ContextBench tasks reference repos by URL + commit hash.
    """
    # Extract org/repo from URL
    # e.g., "https://github.com/django/django" -> "django__django"
    repo_slug = repo_url.rstrip("/").split("github.com/")[-1].replace("/", "__")
    repo_dir = cache_dir / "contextbench" / f"{repo_slug}__{commit[:8]}"

    if repo_dir.exists() and (repo_dir / ".git").exists():
        return repo_dir

    repo_dir.mkdir(parents=True, exist_ok=True)
    log.info("Cloning %s @ %s", repo_url, commit[:8])
    try:
        # Clone and checkout specific commit
        subprocess.run(
            ["git", "clone", "--no-checkout", repo_url, str(repo_dir)],
            check=True, capture_output=True, text=True, timeout=300,
        )
        subprocess.run(
            ["git", "checkout", commit],
            check=True, capture_output=True, text=True,
            timeout=60, cwd=str(repo_dir),
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        log.error("Clone failed: %s @ %s: %s", repo_url, commit, e)
        return None
    return repo_dir


def run_retrieval_agent_on_cb_task(
    task: Dict[str, Any],
    repo_path: Path,
    client: Any,
    model: str,
    backend: str,
    sg: Any = None,
    verbose: bool = False,
) -> Dict[str, Any]:
    """Run our retrieval agent on a ContextBench task.

    Returns the agent's oracle output.
    """
    from scripts.context_retrieval_agent import (
        run_agent, SourcegraphClient,
    )

    # Build a CCB-style context dict from ContextBench task
    instance_id = task.get("instance_id", "")
    problem = task.get("problem_statement", "")

    # Extract repo name from instance_id (e.g., "django__django-12345" -> "django/django")
    parts = instance_id.rsplit("-", 1)
    repo_name = parts[0].replace("__", "/") if parts else instance_id

    ctx = {
        "task_dir": "",
        "task_name": instance_id,
        "suite_name": "contextbench",
        "seed_prompt": problem,
        "instruction": problem,
        "check_types": ["file_set_match"],
    }

    repo_paths = {repo_name: repo_path, instance_id: repo_path}

    oracle, metadata = run_agent(
        ctx, repo_paths, client,
        model=model, backend=backend,
        sg=sg, verbose=verbose,
    )

    return {
        "oracle": oracle,
        "metadata": metadata,
        "instance_id": instance_id,
    }


def convert_to_trajectory(
    instance_id: str,
    oracle: Dict[str, Any],
    model_patch: str = "",
) -> Dict[str, Any]:
    """Convert our oracle output to ContextBench trajectory format.

    ContextBench expects:
    {
        "instance_id": "owner__repo-1234",
        "traj_data": {
            "pred_steps": [{"files": [...], "spans": {}, "symbols": {}}],
            "pred_files": ["path/to/file1.py", ...],
            "pred_spans": {}
        },
        "model_patch": "..."
    }
    """
    files = [f.get("path", "") for f in oracle.get("files", []) if f.get("path")]

    # Build spans from symbols if we have line info
    pred_spans = {}
    for sym in oracle.get("symbols", []):
        path = sym.get("path", "")
        if path and path not in pred_spans:
            pred_spans[path] = []
        # We don't have exact line numbers from our oracle format,
        # so we leave spans empty and rely on file-level metrics

    return {
        "instance_id": instance_id,
        "traj_data": {
            "pred_steps": [{
                "files": files,
                "spans": pred_spans,
                "symbols": {},
            }],
            "pred_files": files,
            "pred_spans": pred_spans,
        },
        "model_patch": model_patch,
    }


def evaluate_trajectories(
    gold_path: Path,
    traj_path: Path,
    out_path: Path,
) -> Dict[str, Any]:
    """Run ContextBench evaluation.

    Returns aggregate metrics dict.
    """
    cmd = [
        sys.executable, "-m", "contextbench.evaluate",
        "--gold", str(gold_path),
        "--pred", str(traj_path),
        "--out", str(out_path),
    ]
    log.info("Running: %s", " ".join(cmd))
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=600,
        )
        if result.returncode != 0:
            log.error("ContextBench eval failed:\n%s", result.stderr[:2000])
            return {}
        # Parse results from output file
        if out_path.exists():
            results = []
            for line in out_path.read_text().splitlines():
                if line.strip():
                    try:
                        results.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
            return {"results": results, "stderr": result.stderr[:2000]}
    except subprocess.TimeoutExpired:
        log.error("ContextBench eval timed out")
    except FileNotFoundError:
        log.error("contextbench not installed. pip install contextbench")
    return {}


def compute_simple_file_metrics(
    tasks: List[Dict],
    trajectories: List[Dict],
) -> Dict[str, float]:
    """Compute file-level metrics without needing ContextBench installed.

    Compares predicted files against gold files from the dataset.
    """
    recalls = []
    precisions = []

    for task, traj in zip(tasks, trajectories):
        # Get gold files from task
        gold_files_raw = task.get("files", [])
        if isinstance(gold_files_raw, str):
            try:
                gold_files_raw = json.loads(gold_files_raw)
            except json.JSONDecodeError:
                gold_files_raw = []

        gold_files = set()
        if isinstance(gold_files_raw, list):
            for f in gold_files_raw:
                if isinstance(f, str):
                    gold_files.add(f)
                elif isinstance(f, dict):
                    gold_files.add(f.get("path", ""))

        # Also get gold files from patch if available
        patch = task.get("patch", "")
        if patch:
            for line in patch.split("\n"):
                if line.startswith("--- a/") or line.startswith("+++ b/"):
                    path = line[6:].strip()
                    if path and path != "/dev/null":
                        gold_files.add(path)

        pred_files = set(traj.get("traj_data", {}).get("pred_files", []))

        if not gold_files:
            continue

        # Normalize paths (strip leading /)
        gold_norm = {f.lstrip("/") for f in gold_files if f}
        pred_norm = {f.lstrip("/") for f in pred_files if f}

        inter = gold_norm & pred_norm
        recall = len(inter) / len(gold_norm) if gold_norm else 0
        precision = len(inter) / len(pred_norm) if pred_norm else 0
        recalls.append(recall)
        precisions.append(precision)

    if not recalls:
        return {"file_recall": 0, "file_precision": 0, "file_f1": 0, "n_evaluated": 0}

    avg_recall = sum(recalls) / len(recalls)
    avg_precision = sum(precisions) / len(precisions)
    f1 = (2 * avg_recall * avg_precision / (avg_recall + avg_precision)
           if (avg_recall + avg_precision) > 0 else 0)

    return {
        "file_recall": round(avg_recall, 4),
        "file_precision": round(avg_precision, 4),
        "file_f1": round(f1, 4),
        "n_evaluated": len(recalls),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate context retrieval agent against ContextBench"
    )
    parser.add_argument(
        "--download-data", action="store_true",
        help="Download ContextBench dataset from Hugging Face",
    )
    parser.add_argument(
        "--sample", type=int, default=0,
        help="Number of tasks to sample (0 = all)",
    )
    parser.add_argument(
        "--verified", action="store_true",
        help="Use verified subset (500 tasks) instead of full (1136)",
    )
    parser.add_argument(
        "--model", type=str, default="claude-sonnet-4-6",
        help="Model to use",
    )
    parser.add_argument(
        "--backend", type=str, default="hybrid",
        choices=("local", "deepsearch", "hybrid"),
        help="Tool backend",
    )
    parser.add_argument(
        "--max-cost", type=float, default=0,
        help="Cost limit in USD",
    )
    parser.add_argument(
        "--out", type=str, default="",
        help="Output directory (default: results/contextbench/)",
    )
    parser.add_argument(
        "--seed", type=int, default=42,
        help="Random seed for sampling",
    )
    parser.add_argument(
        "--verbose", action="store_true",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    if args.download_data:
        download_data()
        return 0

    # Set up output dir
    out_dir = Path(args.out) if args.out else RESULTS_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    # Load tasks
    tasks = load_tasks(
        verified=args.verified,
        sample=args.sample,
        seed=args.seed,
    )
    if not tasks:
        return 1

    # Check for anthropic
    try:
        import anthropic
    except ImportError:
        log.error("pip install anthropic")
        return 1

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        log.error("ANTHROPIC_API_KEY not set")
        return 1

    client = anthropic.Anthropic(api_key=api_key)

    # Set up SG client if needed
    sg = None
    if args.backend in ("deepsearch", "hybrid"):
        from scripts.context_retrieval_agent import SourcegraphClient
        sg = SourcegraphClient()

    total_cost = 0.0
    trajectories = []
    evaluated_tasks = []

    for i, task in enumerate(tasks):
        if args.max_cost > 0 and total_cost >= args.max_cost:
            log.warning("Cost limit reached ($%.2f)", total_cost)
            break

        instance_id = task.get("instance_id", f"task_{i}")
        repo_url = task.get("repo", task.get("repo_url", ""))
        commit = task.get("base_commit", task.get("commit", "HEAD"))

        log.info("[%d/%d] %s", i + 1, len(tasks), instance_id)

        if not repo_url:
            # Try to reconstruct from instance_id
            parts = instance_id.rsplit("-", 1)
            org_repo = parts[0].replace("__", "/") if parts else ""
            repo_url = f"https://github.com/{org_repo}" if org_repo else ""

        if not repo_url:
            log.warning("  No repo URL, skipping")
            continue

        # Clone repo
        repo_path = clone_for_contextbench(repo_url, commit)
        if not repo_path:
            log.warning("  Clone failed, skipping")
            continue

        # Run agent
        try:
            result = run_retrieval_agent_on_cb_task(
                task, repo_path, client,
                model=args.model, backend=args.backend,
                sg=sg, verbose=args.verbose,
            )
        except Exception as e:
            log.error("  Agent failed: %s", e)
            continue

        total_cost += result["metadata"].get("cost_usd", 0)

        # Convert to trajectory
        traj = convert_to_trajectory(
            instance_id, result["oracle"],
            model_patch=task.get("patch", ""),
        )
        trajectories.append(traj)
        evaluated_tasks.append(task)

        n_files = len(result["oracle"].get("files", []))
        log.info(
            "  -> %d files, $%.4f",
            n_files, result["metadata"]["cost_usd"],
        )

    if not trajectories:
        log.error("No tasks completed")
        return 1

    # Write trajectories
    traj_path = out_dir / "trajectories.traj.json"
    with open(traj_path, "w") as f:
        for traj in trajectories:
            f.write(json.dumps(traj) + "\n")
    log.info("Wrote %d trajectories: %s", len(trajectories), traj_path)

    # Compute simple file metrics (works without contextbench installed)
    simple_metrics = compute_simple_file_metrics(evaluated_tasks, trajectories)
    log.info("Simple file metrics: %s", json.dumps(simple_metrics, indent=2))

    # Try running ContextBench evaluator
    gold_fname = "verified.parquet" if args.verified else "full.parquet"
    gold_path = DATA_DIR / gold_fname
    cb_results_path = out_dir / "contextbench_results.jsonl"

    cb_metrics = {}
    if gold_path.exists():
        cb_metrics = evaluate_trajectories(gold_path, traj_path, cb_results_path)

    # Write summary report
    report = {
        "model": args.model,
        "backend": args.backend,
        "n_tasks_attempted": len(tasks),
        "n_tasks_completed": len(trajectories),
        "total_cost_usd": round(total_cost, 4),
        "avg_cost_per_task": round(total_cost / len(trajectories), 4) if trajectories else 0,
        "simple_file_metrics": simple_metrics,
        "contextbench_metrics": cb_metrics,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    report_path = out_dir / "validation_report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n")

    # Print summary
    print(f"\n{'=' * 60}")
    print(f"ContextBench Validation Report")
    print(f"{'=' * 60}")
    print(f"Model: {args.model}")
    print(f"Backend: {args.backend}")
    print(f"Tasks: {len(trajectories)}/{len(tasks)} completed")
    print(f"Cost: ${total_cost:.4f} (avg ${total_cost/len(trajectories):.4f}/task)")
    print(f"\nFile-level metrics (simple):")
    print(f"  Recall:    {simple_metrics['file_recall']:.4f}")
    print(f"  Precision: {simple_metrics['file_precision']:.4f}")
    print(f"  F1:        {simple_metrics['file_f1']:.4f}")
    if cb_metrics:
        print(f"\nContextBench metrics: see {cb_results_path}")
    print(f"\nFull report: {report_path}")
    print(f"Trajectories: {traj_path}")
    print(f"{'=' * 60}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
