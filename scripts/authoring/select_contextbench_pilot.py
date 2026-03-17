#!/usr/bin/env python3
"""Select ContextBench tasks for cross-validation pilot and produce mirror manifest.

Loads ContextBench's human-annotated dataset, selects N stratified tasks, and
outputs both a pilot selection file and mirror manifest entries for
create_sg_mirrors.py.

Usage:
    # Download data first (if needed)
    python3 scripts/select_contextbench_pilot.py --download-data

    # Select 50 tasks (default)
    python3 scripts/select_contextbench_pilot.py --n 50 --seed 42

    # Verified subset only
    python3 scripts/select_contextbench_pilot.py --n 50 --verified
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))

from validate_on_contextbench import (
    download_data,
    load_tasks,
    _gold_context_size,
    _infer_language,
    _extract_gold_files,
    DATA_DIR,
)

log = logging.getLogger(__name__)

SELECTION_OUT = REPO_ROOT / "configs" / "contextbench_pilot_50.json"
MIRROR_MANIFEST = REPO_ROOT / "configs" / "mirror_creation_manifest.json"


def _mirror_name(repo: str, commit: str) -> str:
    """Generate sg-evals mirror name from repo slug + commit prefix.

    e.g. 'django/django' + 'abc123...' -> 'django--abc123de'
    """
    # Take the repo name (not org) and first 8 chars of commit
    parts = repo.rstrip("/").split("/")
    repo_short = parts[-1] if parts else repo
    return f"{repo_short}--{commit[:8]}"


def _task_id(instance_id: str) -> str:
    """Normalize ContextBench instance_id to a Harbor-safe task ID.

    Docker requires lowercase image names, so we lowercase everything.
    e.g. 'SWE-Bench-Verified__python__...__51e329de' -> 'cb-swe-bench-verified__python__...__51e329de'
    """
    return f"cb-{instance_id.lower()}"


def select_and_export(
    n: int = 50,
    seed: int = 42,
    verified: bool = False,
    download: bool = False,
) -> Path:
    """Select tasks and write selection + mirror manifest."""

    if download:
        download_data()

    tasks = load_tasks(
        data_dir=DATA_DIR,
        verified=verified,
        sample=n,
        stratified=True,
        seed=seed,
    )

    if not tasks:
        log.error("No tasks loaded. Run --download-data first.")
        sys.exit(1)

    # Build selection entries and deduplicate mirrors
    selection_tasks = []
    mirrors_by_key: dict[str, dict] = {}

    for task in tasks:
        instance_id = task.get("instance_id", "")
        repo = task.get("repo", "")
        repo_url = task.get("repo_url", "")
        if not repo_url and repo:
            repo_url = f"https://github.com/{repo}"
        commit = task.get("base_commit", task.get("commit", ""))
        language = _infer_language(instance_id, task)
        gold_files = _extract_gold_files(task)
        complexity = _gold_context_size(task)
        patch = task.get("patch", "")

        if not repo or not commit:
            log.warning("Skipping %s: missing repo or commit", instance_id)
            continue

        mirror = _mirror_name(repo, commit)
        mirror_key = f"{repo}:{commit}"

        entry = {
            "instance_id": instance_id,
            "task_id": _task_id(instance_id),
            "repo": repo,
            "repo_url": repo_url,
            "base_commit": commit,
            "language": language,
            "mirror_name": mirror,
            "gold_context_files": len(gold_files),
            "complexity": complexity,
            "source": task.get("source", ""),
            # Store these for scaffolding but don't clutter the selection
            "_problem_statement": task.get("problem_statement", ""),
            "_patch": patch,
            "_test_patch": task.get("test_patch", ""),
            "_gold_context": task.get("gold_context", "[]"),
        }
        selection_tasks.append(entry)

        if mirror_key not in mirrors_by_key:
            upstream = repo_url.replace("https://", "").replace("http://", "")
            if upstream.endswith(".git"):
                upstream = upstream[:-4]
            if not upstream.startswith("github.com/"):
                upstream = f"github.com/{repo}"
            mirrors_by_key[mirror_key] = {
                "upstream": upstream,
                "commit": commit,
                "mirror": f"sg-evals/{mirror}",
                "pin_source": "contextbench cross-validation pilot",
                "tasks": [],
            }
        mirrors_by_key[mirror_key]["tasks"].append(
            f"curator_calibration/{_task_id(instance_id)}"
        )

    # Write selection file
    selection = {
        "metadata": {
            "total": len(selection_tasks),
            "seed": seed,
            "verified_subset": verified,
            "generated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "unique_mirrors": len(mirrors_by_key),
        },
        "tasks": selection_tasks,
        "mirrors": list(mirrors_by_key.values()),
    }

    SELECTION_OUT.parent.mkdir(parents=True, exist_ok=True)
    SELECTION_OUT.write_text(json.dumps(selection, indent=2) + "\n")
    log.info("Wrote %d tasks to %s", len(selection_tasks), SELECTION_OUT)

    # Append to mirror creation manifest (if it exists, merge; otherwise create)
    new_mirrors = list(mirrors_by_key.values())
    if MIRROR_MANIFEST.exists():
        manifest = json.loads(MIRROR_MANIFEST.read_text())
        existing_names = {m["mirror"] for m in manifest.get("mirrors", [])}
        added = 0
        for m in new_mirrors:
            if m["mirror"] not in existing_names:
                manifest["mirrors"].append(m)
                added += 1
        manifest["_status"] = (
            f"UPDATED {datetime.now().strftime('%Y-%m-%d')} — "
            f"{len(manifest['mirrors'])} mirrors "
            f"({added} new contextbench)"
        )
        MIRROR_MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n")
        log.info("Appended %d new mirrors to %s", added, MIRROR_MANIFEST)
    else:
        manifest = {
            "_description": "Mirrors needed for reproducible Sourcegraph indexing",
            "_generated": datetime.now().strftime("%Y-%m-%d"),
            "_status": f"NEW — {len(new_mirrors)} contextbench mirrors",
            "mirrors": new_mirrors,
        }
        MIRROR_MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n")
        log.info("Created %s with %d mirrors", MIRROR_MANIFEST, len(new_mirrors))

    # Print summary
    langs = {}
    for t in selection_tasks:
        lang = t["language"]
        langs[lang] = langs.get(lang, 0) + 1
    complexities = {}
    for t in selection_tasks:
        c = t["complexity"]
        complexities[c] = complexities.get(c, 0) + 1

    print(f"\n=== ContextBench Pilot Selection ===")
    print(f"Tasks:   {len(selection_tasks)}")
    print(f"Mirrors: {len(mirrors_by_key)}")
    print(f"Languages: {dict(sorted(langs.items(), key=lambda x: -x[1]))}")
    print(f"Complexity: {complexities}")
    print(f"Selection: {SELECTION_OUT}")
    print(f"Manifest:  {MIRROR_MANIFEST}")

    return SELECTION_OUT


def main():
    parser = argparse.ArgumentParser(
        description="Select ContextBench tasks for cross-validation pilot"
    )
    parser.add_argument("--n", type=int, default=50, help="Number of tasks to select")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument(
        "--verified", action="store_true", help="Use verified 500-task subset"
    )
    parser.add_argument(
        "--download-data", action="store_true", help="Download data first"
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    select_and_export(
        n=args.n,
        seed=args.seed,
        verified=args.verified,
        download=args.download_data,
    )


if __name__ == "__main__":
    main()
