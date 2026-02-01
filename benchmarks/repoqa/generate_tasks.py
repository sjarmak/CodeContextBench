#!/usr/bin/env python3
"""
Standalone RepoQA task generator for Harbor.

Downloads the upstream RepoQA dataset (evalplus/repoqa), selects a diverse
subset, and generates Harbor task directories using templates.

Usage:
    python generate_tasks.py                    # Generate default 10 tasks (2 per language)
    python generate_tasks.py --limit 20         # Generate 20 tasks
    python generate_tasks.py --languages python rust  # Specific languages only
    python generate_tasks.py --all              # Generate all 500 tasks
"""

import argparse
import json
import os
import shutil
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class RepoQAInstance:
    """A single RepoQA needle-in-haystack instance."""
    instance_id: str
    repository: str
    commit: str
    language: str
    function_name: str
    function_path: str
    function_description: str
    # Metadata for selection scoring
    code_ratio: float = 0.0
    repo_topic: str = ""


SCRIPT_DIR = Path(__file__).parent
TEMPLATE_DIR = SCRIPT_DIR / "templates"
DATA_DIR = SCRIPT_DIR / "data"
TASKS_DIR = SCRIPT_DIR / "tasks"


def load_upstream_dataset() -> List[RepoQAInstance]:
    """Load the RepoQA dataset via the repoqa package."""
    try:
        from repoqa.data import get_repoqa_data
    except ImportError:
        print("ERROR: repoqa package not installed. Run: pip install repoqa")
        sys.exit(1)

    data = get_repoqa_data()
    instances = []

    for language, repos in data.items():
        for repo_data in repos:
            repo_name = repo_data["repo"]
            commit = repo_data.get("commit_sha", "")
            topic = repo_data.get("topic", "")

            for i, needle in enumerate(repo_data.get("needles", [])):
                instance_id = f"repoqa-{language}-{repo_name.replace('/', '-')}-{i:02d}"
                instances.append(RepoQAInstance(
                    instance_id=instance_id,
                    repository=repo_name,
                    commit=commit,
                    language=language,
                    function_name=needle["name"],
                    function_path=needle["path"],
                    function_description=needle["description"],
                    code_ratio=needle.get("code_ratio", 0.0),
                    repo_topic=topic,
                ))

    return instances


def save_dataset_jsonl(instances: List[RepoQAInstance], output_path: Path) -> None:
    """Save instances to JSONL for reproducibility."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        for inst in instances:
            f.write(json.dumps(asdict(inst)) + "\n")
    print(f"Saved {len(instances)} instances to {output_path}")


def select_tasks(
    instances: List[RepoQAInstance],
    per_language: int = 2,
    languages: Optional[List[str]] = None,
    limit: Optional[int] = None,
    select_all: bool = False,
) -> List[RepoQAInstance]:
    """Select a diverse subset of tasks.

    Strategy: pick `per_language` tasks per language, preferring:
    - Different repos (1 per repo when possible)
    - Higher code_ratio (function is larger relative to context)
    """
    if select_all:
        if languages:
            return [i for i in instances if i.language in languages]
        return instances

    available_languages = sorted(set(i.language for i in instances))
    if languages:
        available_languages = [l for l in available_languages if l in languages]

    selected = []
    for lang in available_languages:
        lang_instances = [i for i in instances if i.language == lang]

        # Group by repo, pick best from each
        by_repo: Dict[str, List[RepoQAInstance]] = {}
        for inst in lang_instances:
            by_repo.setdefault(inst.repository, []).append(inst)

        # Sort repos by number of instances (more = more popular), pick from diverse repos
        repo_order = sorted(by_repo.keys(), key=lambda r: len(by_repo[r]), reverse=True)

        count = 0
        target = per_language
        # First pass: one per repo
        for repo in repo_order:
            if count >= target:
                break
            # Pick the needle with highest code_ratio (most substantial function)
            candidates = sorted(by_repo[repo], key=lambda x: x.code_ratio, reverse=True)
            selected.append(candidates[0])
            count += 1

    if limit and len(selected) > limit:
        selected = selected[:limit]

    return selected


def render_template(template_path: Path, context: dict) -> str:
    """Simple {key} placeholder replacement."""
    content = template_path.read_text()
    for key, value in context.items():
        content = content.replace(f"{{{key}}}", str(value))
    return content


def generate_task(instance: RepoQAInstance, output_dir: Path) -> None:
    """Generate a single Harbor task directory from a RepoQA instance."""
    task_dir = output_dir / instance.instance_id
    if task_dir.exists():
        shutil.rmtree(task_dir)
    task_dir.mkdir(parents=True)

    context = {
        "repository": instance.repository,
        "commit": instance.commit,
        "language": instance.language,
        "function_description": instance.function_description,
        "task_variant": "sr-qa",
    }

    # 1. instruction.md
    instruction = render_template(TEMPLATE_DIR / "instruction_sr-qa.md", context)
    (task_dir / "instruction.md").write_text(instruction)

    # 2. task.toml -- render from template and update fields
    toml_template = (TEMPLATE_DIR / "task.toml").read_text()
    toml_content = toml_template.replace(
        'repository = "unknown"', f'repository = "{instance.repository}"'
    ).replace(
        'commit = "unknown"', f'commit = "{instance.commit}"'
    ).replace(
        'language = "unknown"', f'language = "{instance.language}"'
    ).replace(
        'tags = ["repoqa", "code-search"]',
        f'tags = ["repoqa", "{instance.language}", "sr-qa", "code-search"]'
    )
    (task_dir / "task.toml").write_text(toml_content)

    # 3. environment/Dockerfile
    env_dir = task_dir / "environment"
    env_dir.mkdir()
    dockerfile = render_template(TEMPLATE_DIR / "environment" / "Dockerfile", context)
    (env_dir / "Dockerfile").write_text(dockerfile)

    # 4. tests/
    tests_dir = task_dir / "tests"
    tests_dir.mkdir()

    # ground_truth.json
    ground_truth = {
        "function_id": f"{instance.function_path}::{instance.function_name}",
        "canonical_path": instance.function_path,
        "canonical_name": instance.function_name,
        "language": instance.language,
        "nl_description": instance.function_description,
        "task_variant": "sr-qa",
    }
    with open(tests_dir / "ground_truth.json", "w") as f:
        json.dump(ground_truth, f, indent=2)

    # test.sh
    test_sh = render_template(TEMPLATE_DIR / "tests" / "test.sh", context)
    test_sh_path = tests_dir / "test.sh"
    test_sh_path.write_text(test_sh)
    test_sh_path.chmod(0o755)

    # verifiers.py (needed by test.sh)
    verifiers_src = SCRIPT_DIR / "verifiers.py"
    if verifiers_src.exists():
        shutil.copy2(verifiers_src, tests_dir / "verifiers.py")

    # 5. solution/ (empty, agent writes here)
    (task_dir / "solution").mkdir()


def main():
    parser = argparse.ArgumentParser(description="Generate RepoQA Harbor tasks")
    parser.add_argument("--per-language", type=int, default=2,
                        help="Tasks per language (default: 2)")
    parser.add_argument("--languages", nargs="+", default=None,
                        help="Filter to specific languages")
    parser.add_argument("--limit", type=int, default=None,
                        help="Maximum total tasks")
    parser.add_argument("--all", action="store_true",
                        help="Generate all 500 tasks")
    parser.add_argument("--output-dir", type=Path, default=TASKS_DIR,
                        help="Output directory (default: tasks/)")
    args = parser.parse_args()

    # Load upstream dataset
    print("Loading RepoQA dataset...")
    instances = load_upstream_dataset()
    print(f"Loaded {len(instances)} instances across "
          f"{len(set(i.language for i in instances))} languages, "
          f"{len(set(i.repository for i in instances))} repos")

    # Save full dataset for reproducibility
    save_dataset_jsonl(instances, DATA_DIR / "repoqa_instances.jsonl")

    # Select tasks
    selected = select_tasks(
        instances,
        per_language=args.per_language,
        languages=args.languages,
        limit=args.limit,
        select_all=args.all,
    )
    print(f"\nSelected {len(selected)} tasks:")
    by_lang = {}
    for s in selected:
        by_lang.setdefault(s.language, []).append(s)
    for lang in sorted(by_lang):
        print(f"  {lang}: {len(by_lang[lang])} tasks")
        for t in by_lang[lang]:
            print(f"    {t.instance_id} ({t.repository} -> {t.function_path}::{t.function_name})")

    # Save selected list
    selected_data = {
        "benchmark": "repoqa",
        "total_available": len(instances),
        "total_selected": len(selected),
        "tasks": [
            {
                "task_id": s.instance_id,
                "repository": s.repository,
                "commit": s.commit,
                "language": s.language,
                "function_name": s.function_name,
                "function_path": s.function_path,
            }
            for s in selected
        ],
    }
    with open(SCRIPT_DIR / "selected_tasks.json", "w") as f:
        json.dump(selected_data, f, indent=2)
        f.write("\n")

    # Generate tasks
    print(f"\nGenerating {len(selected)} task directories...")
    args.output_dir.mkdir(parents=True, exist_ok=True)

    success = 0
    for i, inst in enumerate(selected, 1):
        try:
            generate_task(inst, args.output_dir)
            print(f"  [{i}/{len(selected)}] {inst.instance_id}")
            success += 1
        except Exception as e:
            print(f"  [{i}/{len(selected)}] FAILED {inst.instance_id}: {e}")

    print(f"\nGeneration complete: {success}/{len(selected)} succeeded")
    print(f"Output: {args.output_dir}")


if __name__ == "__main__":
    main()
